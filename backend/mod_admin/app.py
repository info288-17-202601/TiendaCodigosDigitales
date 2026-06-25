from flask import Flask, request, jsonify
import sys
import os
import psycopg2
import json
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import get_inventory_db_name, get_connection, release_connection
from shared.messaging import publicar_evento

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DB_USER = os.environ.get("DB_USER_INVENTARIO", "user_inventario")
DB_PASS = os.environ.get("DB_PASS_INVENTARIO", "PassInv654")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

@app.route('/admin/agregar_stock', methods=['POST'])
def agregar_stock():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)