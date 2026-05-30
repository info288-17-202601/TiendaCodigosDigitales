# Importamos Flask (para crear la API web) y jsonify (para responder en formato JSON)
from flask import Flask, request, jsonify
# Importamos pysolr (la librería para comunicarnos con Solr)
import pysolr

# 1. Inicializamos la aplicación Flask
app = Flask(__name__)

# 2. Configuramos la conexión a Solr
# "solr_engine" es el nombre que le dimos al contenedor en el docker-compose.yml
# "8983" es el puerto, y "catalogo" es el core que creamos.
SOLR_URL = 'http://solr_engine:8983/solr/catalogo'

# Creamos el "cliente" que hablará con Solr
solr = pysolr.Solr(SOLR_URL, always_commit=True)

# 3. Creamos la "Ruta" o "Endpoint" de búsqueda
# Cuando alguien entre a http://tu-servidor:5002/buscar, se ejecutará esta función
@app.route('/buscar', methods=['GET'])
def buscar_juegos():
    # request.args.get() atrapa las variables de la URL. 
    # Ejemplo: /buscar?q=mario -> Atrapa la palabra "mario"
    # Si no envían nada, el valor por defecto será '*:*' (que en Solr significa "traer todo")
    termino_busqueda = request.args.get('q', '*:*') 

    try:
        # 4. Le pedimos a Solr que busque
        # Hacemos una búsqueda simple. En un futuro aquí puedes añadir filtros
        resultados = solr.search(termino_busqueda)

        # 5. Preparamos la respuesta
        lista_juegos = []
        for juego in resultados:
            lista_juegos.append(juego) # Guardamos cada resultado en nuestra lista

        # Devolvemos la lista en formato JSON con un código 200 (OK)
        return jsonify({
            "mensaje": "Búsqueda exitosa",
            "cantidad_encontrada": len(lista_juegos),
            "resultados": lista_juegos
        }), 200

    except Exception as e:
        # Si algo falla (ej. Solr está apagado), devolvemos un error 500
        return jsonify({"error": "Fallo en el servidor de búsqueda", "detalle": str(e)}), 500

# 6. Encender el servidor
if __name__ == '__main__':
    # Según la documentación, este módulo va en el puerto 5002
    # host='0.0.0.0' permite que Docker exponga el puerto hacia afuera
    app.run(host='0.0.0.0', port=5002)