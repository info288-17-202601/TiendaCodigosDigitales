from flask import Flask, request, jsonify
from mod_pago.service import iniciar_escucha
from shared.database import get_connection, release_connection

# Definicion principal del Modulo de pagos
app = Flask(__name__)

def main():
    app.run(host='0.0.0.0', port=5003)


# Definicion de Metodos para la API

# Solicitar las tarjetas del usuario
#
# GET /cartera?id_usuario=algo
@app.route('/cartera',methods=['GET']) 
def conseguir_cartera():
    id_usuario = request.args.get('id_usuario') 

    # Comienzo conexion
    conn = None
    try:
        conn = get_connection("db_perfil")
        cursor = conn.cursor()
        
        query = """
            SELECT tipo_tarjeta,ultimos_4,id_perfil
            FROM perfil_pago
            WHERE id_usuario = %s
        """

        cursor.execute(query,(id_usuario,))
        tarjetas = cursor.fetchall()

        if not tarjetas:
            return jsonify({"error":"El usuario no tiene ninguna tarjeta"}),404
        
        return jsonify({"mensaje":"Tarjetas encontradas",
                        "cant_tarjetas":len(tarjetas),
                        "tarjetas":tarjetas}), 200


    except Exception as e:
        return jsonify({"error":"Algo fallo al intentar conseguir las billeteras","detalle":str(e)}),500
    
    finally:
        cursor.close()
        if conn:
            release_connection("db_perfil",conn)

# Añadir una nueva tarjeta de un usuario a la BD
#
# PUT /cartera
# Content-Type: application/json
# {
#     "usuario_id": 1,
#     "tipo_tarjeta": "VISA",
#     "ultimos_4": "1234"
# }
@app.route('/cartera',methods=['PUT'])
def añadir_cartera():
    data = request.get_json()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    id_usuario = data.get('usuario_id')
    tipo_tarjeta = data.get('tipo_tarjeta')
    ultimos_4 = data.get('ultimos_4')
    token_pago = "TOKEN_OK"

    if not (tipo_tarjeta and id_usuario and ultimos_4):
        return jsonify({"error":"Los datos ingresados son erroneos o estan vacios"}),400

    conn = None

    try:
        conn = get_connection("db_perfil")
        cursor = conn.cursor()
        query = """
                INSERT INTO perfil_pago (id_usuario,tipo_tarjeta,token_pago,ultimos_4)
                VALUES (%s,%s,%s,%s);
                """
    
        try:
            cursor.execute(query,(id_usuario,tipo_tarjeta,token_pago,ultimos_4))
            conn.commit()

            return jsonify({"mensaje":"Se a añadido de manera correcta la tarjeta"}),201
        
        except Exception as e_db:
            if conn:
                conn.rollback()
        
            return jsonify({"error":"Hubo un fallo en la base de datos","detalle":str(e_db)}),500
        
        
    
    except Exception as e:
        return jsonify({"error":"Algo fallo al intentar conseguir las billeteras","detalle":str(e)}),500
    
    finally:
            if conn:
                cursor.close()
                release_connection("db_perfil",conn)
# Eliminar una tarjeta de la BD
#
# DELETE /cartera
# Content-Type: application/json
# {
#     "id_perfil": 1,
# }
@app.route('/cartera',methods=['DELETE'])
def eliminar_cartera():
    data = request.get_json()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    id_perfil = data.get('id_perfil') 
    conn = None
    try:
        conn = get_connection("db_perfil")
        cursor = conn.cursor()
        
        query = """
            SELECT id_perfil
            FROM perfil_pago
            WHERE id_perfil = %s
        """

        cursor.execute(query,(id_perfil,))
        tarjetas = cursor.fetchone()
        if not tarjetas:
            return jsonify({"error":"la tarjeta ingresada no existe"}),404

        try:
            query = """
            DELETE FROM perfil_pago
            WHERE id_perfil = %s
            """
            cursor.execute(query,(id_perfil,))
            conn.commit()

            return jsonify({"mensaje":"La tarjeta fue eliminada del sistema de manera correcta"}),200

        except Exception as e_db:
            if conn:
                conn.rollback()
            return jsonify({"error":"Algo fallo al intentar conseguir las billeteras","detalle":str(e_db)}),500

    except Exception as e:
        return jsonify({"error":"Algo fallo al intentar conseguir las billeteras","detalle":str(e)}),500
    
    finally:
        cursor.close()
        if conn:
            release_connection("db_perfil",conn)

if __name__ == "__main__":
    main()