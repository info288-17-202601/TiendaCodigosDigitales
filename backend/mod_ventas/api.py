import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.database import get_connection, release_connection
from shared.cache import get_carrito, set_carrito
from mod_ventas.service import procesar_checkout

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DB_USER = os.environ.get("DB_USER_VENTAS", "user_ventas")
DB_PASS = os.environ.get("DB_PASS_VENTAS", "PassVentas321")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

# ----- Endpoints ------

# Obtener elemento del carrito
@app.route("/api/ventas/carrito", methods=["GET"])
def obtener_carrito():
    """
    Obtiene el carrito del usuario.
    """
    # Por ahora usamos un usuario_id por defecto
    # En un caso real, vendría del header o JWT
    usuario_id = "user-123"
    
    carrito = get_carrito(usuario_id)
    return jsonify(carrito), 200

# Añadir elemento al carrito
@app.route("/api/ventas/carrito", methods=["POST"])
def agregar_al_carrito():
    """
    Agrega un juego al carrito temporal del usuario utilizando el manejador de cache.
    """
    data = request.get_json()
    
    # Validacion manual de que traiga todos los datos
    campos_requeridos = ["usuario_id", "juego_id", "cantidad", "precio_unitario", "titulo"]
    if not data or not all(campo in data for campo in campos_requeridos):
        return jsonify({"error": "Faltan campos obligatorios en el JSON"}), 400

    usuario_id = data['usuario_id']
    
    # Prepar el nuevo item
    nuevo_item = {
        "juego_id": data['juego_id'],
        "cantidad": int(data['cantidad']),
        "precio": float(data['precio_unitario']),
        "titulo": data['titulo']
    }
    
    # Obtener el carrito actual
    carrito_actual = get_carrito(usuario_id)
    
    # Añadir el nuevo itema la lista de items
    carrito_actual["items"].append(nuevo_item)
    
    # Actualizar el total estimado en el diccionario
    subtotal_item = nuevo_item["precio"] * nuevo_item["cantidad"]
    carrito_actual["total_estimado"] += subtotal_item
    
    # Guardar en Redis
    set_carrito(usuario_id, carrito_actual)
    
    # Dar respuesta
    return jsonify({
        "mensaje": "Producto añadido al carrito exitosamente", 
        "usuario_id": usuario_id,
        "total_estimado": carrito_actual["total_estimado"]
    }), 200

# Realizar la orden de compra
@app.route("/api/ventas/checkout", methods=["POST"])
def iniciar_checkout():
    """
    Inicia el proceso de compra llamando a service.py.
    """
    data = request.get_json()
    
    # Validacion manual de que traiga el usuario
    campos_requeridos = ["usuario_id", "email","metodo_pago"]
    if not data or not all(campo in data for campo in campos_requeridos):
        return jsonify({"error": "Faltan campos obligatorios en el JSON"}), 400

    # Utilizar servicio del modulo de ventas
    id_orden = procesar_checkout(data['usuario_id'], data['email'], data['metodo_pago'])
    
    # Si ocurre un error en el servicio especificamente
    if not id_orden:
        return jsonify({
            "error": "No se pudo procesar el checkout"
        }), 400

    # Dar respuesta    
    return jsonify({
        "id_orden_compra": id_orden,
        "mensaje": "Orden recibida y enviada a procesamiento asincrono."
    }), 202

# Quitar un elemento especifico del carrito
@app.route("/api/ventas/carrito/<usuario_id>/item/<juego_id>", methods=["DELETE"])
def quitar_del_carrito(usuario_id, juego_id):
    """
    Elimina solo la primera instancia de un juego especifico 
    del carrito temporal del usuario y recalcula el total.
    """
    # Obtener el carrito actual
    carrito_actual = get_carrito(usuario_id)
    
    items_restantes = []
    item_eliminado = False  # Nuestra bandera de control
    
    for item in carrito_actual.get("items", []):
        # Si coincide el ID Y aun no hemos eliminado ninguno en este ciclo
        if str(item.get("juego_id")) == str(juego_id) and not item_eliminado:
            # Restamos el costo de este item especifico
            costo_a_restar = item.get("precio", 0) * item.get("cantidad", 1)
            carrito_actual["total_estimado"] -= costo_a_restar
            
            # Encendemos la bandera para que no se borren copias adicionales
            item_eliminado = True
        else:
            # Todos los demas items se conservan
            items_restantes.append(item)
            
    if not item_eliminado:
        return jsonify({"error": "El producto no se encontraba en el carrito"}), 404
        
    carrito_actual["total_estimado"] = max(0.0, carrito_actual["total_estimado"])
    carrito_actual["items"] = items_restantes
    
    # Guardar en Redis
    set_carrito(usuario_id, carrito_actual)
    
    # Dar respuesta
    return jsonify({
        "mensaje": "Un producto eliminado del carrito exitosamente", 
        "usuario_id": usuario_id,
        "total_estimado": carrito_actual["total_estimado"]
    }), 200

# Vaciar todo el carrito de un usuario
@app.route("/api/ventas/carrito/<usuario_id>", methods=["DELETE"])
def vaciar_carrito(usuario_id):
    """
    Limpia por completo el carrito de compras de un usuario.
    """
    carrito_actual = get_carrito(usuario_id)
    
    # Reiniciar valores
    carrito_actual["items"] = []
    carrito_actual["total_estimado"] = 0.0
    
    # Guardar en Redis
    set_carrito(usuario_id, carrito_actual)
    
    # Dar respuesta
    return jsonify({
        "mensaje": "El carrito ha sido vaciado exitosamente",
        "usuario_id": usuario_id,
        "total_estimado": 0.0
    }), 200

# Obtener estado de una orden
@app.route("/api/ventas/ordenes/status/<id_orden_compra>", methods=["GET"])
def consultar_estado_orden(id_orden_compra):
    """
    Endpoint para Polling del estado de la orden por parte del frontend.
    """
    db_name = "db_ventas"

    # Obtener conexion
    conn = get_connection(db_name, DB_USER, DB_PASS)
    try:
        cur = conn.cursor()
        query = "SELECT estado_pago FROM orden_compra WHERE id_orden_compra = %s"
        cur.execute(query, (id_orden_compra,))
        resultado = cur.fetchone()
        cur.close()
        
        # Si no existe la orden
        if not resultado:
            return jsonify({"error": "Orden no encontrada"}), 404
            
        # Dar respuesta    
        return jsonify({
            "id_orden_compra": id_orden_compra, 
            "estado_pago": resultado["estado_pago"]
        }), 200
        
    # Liberar conexion
    finally:
        release_connection(db_name, conn)

# Obtener historial de ordenes
@app.route("/api/ventas/ordenes/usuario/<usuario_id>", methods=["GET"])
def historial_compras_usuario(usuario_id):
    """
    Devuelve el historial inmutable de compras para un usuario.
    """
    db_name = "db_ventas"

    # Obtener conexion
    conn = get_connection(db_name, DB_USER, DB_PASS)
    try:
        cur = conn.cursor()
        query = """
            SELECT id_orden_compra, fecha_transaccion, metodo_pago, total_pagado, estado_pago 
            FROM orden_compra 
            WHERE id_usuario = %s 
            ORDER BY fecha_transaccion DESC
        """
        cur.execute(query, (usuario_id,))
        
        ordenes = cur.fetchall()
        cur.close()
        
        # Dar respuesta
        return jsonify({
            "usuario_id": usuario_id, 
            "historial": ordenes
        }), 200
        
    # Liberar conexion
    finally:
        release_connection(db_name, conn)

# Obtener el carrito actual
@app.route("/api/ventas/carrito/usuario/<usuario_id>", methods=["GET"])
def carrito_usuario(usuario_id):
    """
    Devuelve el estado actual del carrito del usuario <usuario_id>
    """
    return jsonify(get_carrito(usuario_id), 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

