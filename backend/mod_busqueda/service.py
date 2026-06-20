""" service.py: Es la API web (Flask). Se encarga de responder a las búsquedas de los usuarios """

import os
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
# Importamos pysolr (la librería para comunicarnos con Solr)
import pysolr
# Importamos redis para la caché
import redis

import psycopg2 
from psycopg2.extras import RealDictCursor


# 1. Inicializamos la aplicación Flask
app = Flask(__name__)

# Habilitamos CORS para todas las rutas
CORS(app, resources={r"/*": {"origins": "*"}})

# 2. Configuramos la conexión a Solr
# "solr_engine" es el nombre que le dimos al contenedor en el docker-compose.yml
# "8983" es el puerto, y "catalogo" es el core que creamos.
SOLR_URL = 'http://solr_engine:8983/solr/catalogo'

# Función auxiliar para conectarnos a la BD
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database='db_catalogo',
        user=os.environ.get('POSTGRES_USER', 'admin'),
        password=os.environ.get('POSTGRES_PASSWORD', 'adminpassword')
    )

# Creamos el "cliente" que hablará con Solr
solr = pysolr.Solr(SOLR_URL, always_commit=True)

# Configuramos la conexión a Redis para la caché
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    db=0,
    decode_responses=True
)

# Test de conexión a Redis al iniciar
try:
    redis_client.ping()
    print(f"[✓] Redis conectado exitosamente en {REDIS_HOST}:6379")
except Exception as e:
    print(f"[✗] ERROR: No se pudo conectar a Redis en {REDIS_HOST}:6379 - {e}")

# 3. Creamos la "Ruta" o "Endpoint" de búsqueda inteligente
@app.route('/buscarPorTitulo', methods=['GET'])
def buscar_juegos():
    # Ahora atrapamos un parámetro normal, por ejemplo: /buscarPorTitulo?t=splatoon
    # Si no envían nada, el valor será un texto vacío ''
    nombre_juego = request.args.get('t', '').strip() 

    if nombre_juego != '':
        cache_key = f"busqueda:titulo:{nombre_juego.lower()}"
        
        try:
            # Buscar en Redis (Cache Hit)
            resultado_cache = redis_client.get(cache_key)
            if resultado_cache:
                print(f"[Caché] Respondiendo '{nombre_juego}' desde RAM.")
                return jsonify(json.loads(resultado_cache)), 200
                
        except Exception as e:
            print(f"[!] Advertencia: No se pudo conectar a Redis: {e}")
            # Si Redis falla, no botamos el sistema, seguimos con Solr.
    print(f"[Caché] No estaba en caché. Consultando a Solr por '{nombre_juego}'...")

    if nombre_juego == '' or nombre_juego == '*:*':
        # Si el usuario no escribió nada o envía *:*, le traemos todo el catálogo
        query_solr = '*:*'
    else:
        # Si el usuario escribió "splatoon", el backend arma la sintaxis de Solr sola:
        # Se convierte en: titulo:*splatoon*
        query_solr = f'titulo:*{nombre_juego}*'
    # -------------------------------------

    try:
        # Le enviamos la búsqueda traducida a Solr
        resultados = solr.search(query_solr)

        lista_juegos = []
        for juego in resultados:
            lista_juegos.append(juego) 

        respuesta = {
            "mensaje": f"Búsqueda por título exitosa",
            "criterio": nombre_juego if nombre_juego else "Todas",
            "cantidad_encontrada": len(lista_juegos),
            "resultados": lista_juegos}
        # Guardamos el resultado en Redis con una expiración de 10 minutos (600 segundos)
        try: # Utilizamos .setex que es como .set pero con expiración.
            redis_client.setex(cache_key, 600, json.dumps(respuesta))
            print(f"[Caché] Guardando resultado de '{nombre_juego}' en caché por 10 minutos.")
        except Exception as e:
            print(f"[!] Advertencia: No se pudo guardar en Redis: {e}")

        return jsonify(respuesta), 200

    except Exception as e:
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500
    
# Ruta para buscar juegos exclusivamente por su plataforma
@app.route('/buscarPorPlataforma', methods=['GET'])
def buscar_por_plataforma():
    # Atrapamos el parámetro 'p' de la URL. Ejemplo: /buscarPorPlataforma?p=Nintendo
    plataforma_buscada = request.args.get('p', '').strip()

    if plataforma_buscada != '':
        cache_key = f"busqueda:plataforma:{plataforma_buscada.lower()}"
        
        try:
            # Buscar en Redis (Cache Hit)
            resultado_cache = redis_client.get(cache_key)
            if resultado_cache:
                print(f"[Caché] Respondiendo '{plataforma_buscada}' desde RAM.")
                return jsonify(json.loads(resultado_cache)), 200
                
        except Exception as e:
            print(f"[!] Advertencia: No se pudo conectar a Redis: {e}")
            # Si Redis falla, no botamos el sistema, seguimos con Solr.
    print(f"[Caché] No estaba en caché. Consultando a Solr por '{plataforma_buscada}'...")

    if plataforma_buscada == '':
        # Si no especifican plataforma, trae todo el catálogo
        query_solr = '*:*'
    else:
        # Forzamos a Solr a buscar coincidencias parciales solo en el campo 'plataforma'
        # Esto se traducirá como: plataforma:*Nintendo*
        query_solr = f'plataforma:*{plataforma_buscada}*'
    

    try:
        # Ejecutamos la búsqueda en Solr
        resultados = solr.search(query_solr)

        lista_juegos = []
        for juego in resultados:
            lista_juegos.append(juego) 

        respuesta = {
            "mensaje": f"Búsqueda por plataforma exitosa",
            "criterio": plataforma_buscada if plataforma_buscada else "Todas",
            "cantidad_encontrada": len(lista_juegos),
            "resultados": lista_juegos}

        # Guardamos el resultado en Redis con una expiración de 10 minutos (600 segundos)
        try:
            redis_client.setex(cache_key, 600, json.dumps(respuesta))
            print(f"[Caché] Guardando resultado de '{plataforma_buscada}' en caché por 10 minutos.")
        except Exception as e:
            print(f"[!] Advertencia: No se pudo guardar en Redis: {e}")

        # Respondemos al cliente con los resultados de Solr    
        return jsonify(respuesta), 200

    except Exception as e:
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500
    

# Ruta que recibe el ID del juego en la URL (ej: /juego/splatoon-3-ext)
@app.route('/juego/<id_juego>', methods=['GET'])
def obtener_detalle_juego(id_juego):
    # Generamos la clave de caché
    cache_key = f"detalle:juego:{id_juego}"
    
    try:
        # Buscar en Redis
        resultado_cache = redis_client.get(cache_key)
        if resultado_cache:
            print(f"[Caché] Respondiendo detalles de '{id_juego}' desde RAM.")
            return jsonify(json.loads(resultado_cache)), 200
            
    except Exception as e:
        print(f"[!] Advertencia: No se pudo conectar a Redis: {e}")
        # Si Redis falla, no botamos el sistema, seguimos con Solr.
    
    print(f"[Caché] No estaba en caché. Consultando Solr por '{id_juego}'...")
    
    try:
        # Buscamos el juego por su ID en Solr
        query_solr = f'id:{id_juego}'
        resultados = solr.search(query_solr)
        
        if len(resultados) == 0:
            return jsonify({"error": "Juego no encontrado"}), 404
        
        # Tomamos el primer resultado (debe haber solo uno por ID)
        juego = list(resultados)[0]
        
        # Guardamos el resultado en Redis con una expiración de 10 minutos (600 segundos)
        try:
            redis_client.setex(cache_key, 600, json.dumps(juego))
            print(f"[Caché] Guardando detalles de '{id_juego}' en caché por 10 minutos.")
        except Exception as e:
            print(f"[!] Advertencia: No se pudo guardar en Redis: {e}")
            
        return jsonify(juego), 200

    except Exception as e:
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)