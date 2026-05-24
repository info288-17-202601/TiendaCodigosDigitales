from flask import Flask, jsonify

app = Flask(__name__)

# Nginx ya cortó el '/api/', así que Flask recibe la petición en '/'
@app.route('/')
def home():
    return jsonify({"status": "Backend running!"})

# Un ejemplo de cómo se verán tus rutas reales de compra mañana:
@app.route('/ventas/comprar', methods=['POST'])
def comprar():
    return jsonify({"mensaje": "Ruta de compras lista"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)