from flask import Flask, request, jsonify
from shared.database import get_inventory_db_name, get_connection, release_connection

app = Flask(__name__)

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
        conn = get_connection(db_name)
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)