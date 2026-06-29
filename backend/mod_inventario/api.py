import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.database import get_inventory_db_name, get_connection, release_connection
from shared.messaging import publicar_evento
from shared.cache import get_sesion

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DB_USER = os.environ.get("DB_USER_INVENTARIO", "user_inventario")
DB_PASS = os.environ.get("DB_PASS_INVENTARIO", "PassInv654")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

# ----- Endpoints ------

@app.route("/api/inventario/stock/<id_juego>", methods=["GET"])
def obtener_stock_exacto(id_juego):
    """
    Devuelve la cantidad exacta de claves en estado 'DISPONIBLE' 
    para un juego en una region especifica.
    """
    # Obtener la region de los parametros de la URL (?region=LATAM)
    region = request.args.get('region')
    
    if not region:
        return jsonify({
            "error": "Debe especificar la region como parametro de consulta (ej. ?region=LATAM)"
        }), 400

    # Determinar la base de datos correcta segun la region
    db_name = get_inventory_db_name(region)
    conn = None
    
    try:
        conn = get_connection(db_name, DB_USER, DB_PASS)
        cur = conn.cursor()
        
        # Contar solo las claves disponibles
        query_stock = """
            SELECT COUNT(id_clave) as stock_disponible
            FROM clave_digital 
            WHERE id_juego = %s AND estado = 'DISPONIBLE';
        """
        cur.execute(query_stock, (id_juego,))
        resultado = cur.fetchone()
        cur.close()
        
        # Extraer el numero 
        stock = resultado['stock_disponible'] if isinstance(resultado, dict) else resultado[0]
        
        # Devolver la respuesta al Frontend
        return jsonify({
            "id_juego": id_juego,
            "region": region,
            "stock_disponible": stock
        }), 200

    except Exception as e:
        print(f"[!] Error consultando stock en {db_name}: {e}")
        return jsonify({"error": "Error interno al consultar el inventario"}), 500
        
    finally:
        # Devolver conexion 
        if conn:
            release_connection(db_name, conn)

@app.route('/api/inventario/agregar_stock', methods=['POST'])
def agregar_stock():
    # Verficar que traiga token valido
    token_sesion = request.headers.get("Authorization")

    if not token_sesion:
        return jsonify({"error": "Falta el header Authorization"}), 400

    if token_sesion.startswith("Bearer "):
        token_sesion = token_sesion[7:]

    sesion_usuario = get_sesion(token_sesion)

     # Si no existe el registro
    if sesion_usuario == None:
        return jsonify({"error": "No existe sesion valida con el token dado"}), 401
    
    if sesion_usuario.get('rol') != "admin":
        return jsonify({"error": "El rol de usuario no es admin"}), 401

    datos = request.json
    id_juego = datos.get('juego_id')
    region = datos.get('region')
    nuevos_codigos = datos.get('codigos', [])

    if not id_juego or not region or not nuevos_codigos:
        return jsonify({"error": "Faltan datos en la petición"}), 400

    db_name = get_inventory_db_name(region)
    conn = None
    try:
        conn = get_connection(db_name, DB_USER, DB_PASS)
        cur = conn.cursor()

        # Insertar códigos en la tabla clave_digital 
        for codigo in nuevos_codigos:
            cur.execute(
                "INSERT INTO clave_digital (id_juego, codigo_serial, estado) VALUES (%s, %s, 'DISPONIBLE')",
                (id_juego, codigo)
            )
        
        conn.commit()
        cur.close()

        # Publicar evento a RabbitMQ para que el Buscador se entere 
        payload = {
            "juego_id": id_juego,
            "region": region,
            "motivo": "DISPONIBLE" 
        }
        publicar_evento('inventario.cambio_stock', payload)

        return jsonify({"mensaje": f"Se añadieron {len(nuevos_codigos)} códigos en {region}."}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            release_connection(db_name, conn)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)