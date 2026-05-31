""" service.py: Es la API web (Flask). Se encarga de responder a las búsquedas de los usuarios """

import os
# Importamos Flask (para crear la API web) y jsonify (para responder en formato JSON)
from flask import Flask, request, jsonify
from flask_cors import CORS
# Importamos pysolr (la librería para comunicarnos con Solr)
import pysolr

import psycopg2 
from psycopg2.extras import RealDictCursor

import threading  # Librería nativa para procesos en segundo plano
from consumer import iniciar_escucha_busqueda

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

# 3. Creamos la "Ruta" o "Endpoint" de búsqueda inteligente
@app.route('/buscarPorTitulo', methods=['GET'])
def buscar_juegos():
    # Ahora atrapamos un parámetro normal, por ejemplo: /buscarPorTitulo?t=splatoon
    # Si no envían nada, el valor será un texto vacío ''
    nombre_juego = request.args.get('t', '') 

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

        return jsonify({
            "mensaje": "Búsqueda exitosa",
            "cantidad_encontrada": len(lista_juegos),
            "resultados": lista_juegos
        }), 200

    except Exception as e:
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500
    
# Ruta para buscar juegos exclusivamente por su plataforma
@app.route('/buscarPorPlataforma', methods=['GET'])
def buscar_por_plataforma():
    # Atrapamos el parámetro 'p' de la URL. Ejemplo: /buscarPorPlataforma?p=Nintendo
    plataforma_buscada = request.args.get('p', '') 

    # --- TRADUCCIÓN PARA SOLR ---
    if plataforma_buscada == '':
        # Si no especifican plataforma, trae todo el catálogo
        query_solr = '*:*'
    else:
        # Forzamos a Solr a buscar coincidencias parciales solo en el campo 'plataforma'
        # Esto se traducirá como: plataforma:*Nintendo*
        query_solr = f'plataforma:*{plataforma_buscada}*'
    # -----------------------------

    try:
        # Ejecutamos la búsqueda en Solr
        resultados = solr.search(query_solr)

        lista_juegos = []
        for juego in resultados:
            lista_juegos.append(juego) 

        return jsonify({
            "mensaje": f"Búsqueda por plataforma exitosa",
            "criterio": plataforma_buscada if plataforma_buscada else "Todas",
            "cantidad_encontrada": len(lista_juegos),
            "resultados": lista_juegos
        }), 200

    except Exception as e:
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500
    

# Nueva ruta que recibe el ID del juego en la URL (ej: /juego/splatoon-3-ext)
@app.route('/juego/<id_juego>', methods=['GET'])
def obtener_detalle_juego(id_juego):
    conn = None
    try:
        conn = get_db_connection()
        # RealDictCursor hace que la respuesta sea {"titulo": "x", "precio": y} en vez de una tupla rara ("x", y)
        cur = conn.cursor(cursor_factory=RealDictCursor) 
        
        # Hacemos la consulta SQL a la tabla catalogo
        cur.execute("SELECT * FROM catalogo WHERE id_juego = %s", (id_juego,))
        juego = cur.fetchone() # fetchone() trae solo 1 resultado
        
        cur.close()
        
        if juego is None:
            return jsonify({"error": "Juego no encontrado"}), 404
            
        return jsonify(juego), 200

    except Exception as e:
        return jsonify({"error": "Fallo en la base de datos", "detalle": str(e)}), 500
    finally:
        if conn is not None:
            conn.close() 

if __name__ == '__main__':

    # Arrancamos el consumidor de RabbitMQ en un hilo de fondo (background thread)
    # daemon=True asegura que si Flask se apaga, el consumidor también se apague.
    hilo_consumidor = threading.Thread(target=iniciar_escucha_busqueda, daemon=True)
    hilo_consumidor.start()
    print("[*] Hilo del consumidor RabbitMQ iniciado en segundo plano.", flush=True)

    # Arrancamos Flask
    # Según la documentación, este módulo va en el puerto 5002
    # host='0.0.0.0' permite que Docker exponga el puerto hacia afuera
    app.run(host='0.0.0.0', port=5002)