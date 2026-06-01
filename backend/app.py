import json
from flask import Flask, request, jsonify
from shared.cache import redis_client
from mod_ventas.service import procesar_checkout

app = Flask(__name__)

# Mocked user for MVP
MOCK_USER_ID = "user-123"
MOCK_EMAIL = "user@example.com"

@app.route('/')
def home():
    return jsonify({"status": "Backend running!"})

@app.route('/cart', methods=['GET'])
def get_cart():
    try:
        clave_redis = f"cart:{MOCK_USER_ID}"
        carrito_raw = redis_client.get(clave_redis)
        if carrito_raw:
            return jsonify(json.loads(carrito_raw)), 200
        else:
            return jsonify({"items": [], "total_estimado": 0, "region_compra": "LATAM"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cart', methods=['POST'])
def update_cart():
    try:
        data = request.json
        clave_redis = f"cart:{MOCK_USER_ID}"
        redis_client.set(clave_redis, json.dumps(data))
        redis_client.expire(clave_redis, 86400) # 24 hours
        return jsonify({"mensaje": "Carrito actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ventas/comprar', methods=['POST'])
def comprar():
    try:
        id_orden = procesar_checkout(MOCK_USER_ID, MOCK_EMAIL)
        if id_orden:
            return jsonify({"mensaje": "Compra iniciada", "id_orden_compra": id_orden}), 200
        else:
            return jsonify({"error": "No se pudo iniciar la compra. El carrito podría estar vacío."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)