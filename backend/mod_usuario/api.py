from flask import Flask, request, jsonify
from shared.database import get_connection, release_connection
from shared.messaging import publicar_evento
from psycopg2 import Error as error_db
# Definicion principal del Modulo de usuarios

# Clave de incriptacion : FUTURO FUTURO FUTURO
app = Flask(__name__)

def main():
    app.run(host='0.0.0.0', port=5006)


# Solicitar datos de un usuario
#
# GET /usuario?id_usuario=algo
@app.route('/usuario',methods=['GET'])
def AAAAAAAAAAA():
    id_usuario = request.args.get('id_usuario')

    # Conexiando
    conn = None
    try:
        conn = get_connection("db_usuarios")
        cursor = conn.cursor()
        query = """
            SELECT *
            FROM usuario
            WHERE id_usuario = %s
        """
        cursor.execute(query,(id_usuario,))
        usuario = cursor.fetchall()

        if not usuario:
            return jsonify({"error","El usuario no existe en la base de datos"}),404

        return jsonify({"mensaje":"Usuario encontrado",
                        "usuario":usuario}),200
    except Exception as e:
        return jsonify({"error":"Hubo un fallo al intentar ingresar los datos","detalle":str(e)}),500
    
    finally:
        cursor.close()
        if conn:
            release_connection("db_usuarios",conn)

# Añadir un usuario a la BD
#
# PUT /registrar
# Content-type: application/json
# {
#   "usuario_id": "Mamoshka-1231",
#   "usuario" : "asdasda",
#   "email" : "Weezer@gmail.com",
#   "contrasena" : "para entender",
#   "region" : "LATAM"
# }

# Existe la posibilidad de que usuarios puedan usar el mismo correo para multiples cuentas
@app.route('/registrar',methods=['PUT'])
def añadir_usuario():
    data = request.get_json()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    id_usuario = data.get('usuario_id') # Pega para ti vito :3
    usuario = data.get('usuario')
    email = data.get('email')
    contrasena = data.get('contrasena')
    region = data.get('region')

    if not (id_usuario and usuario and email and contrasena and region):
        return jsonify({"error":"Los datos ingresados son erroneos o estan vacios"}),400

    conn = None
    try:
        conn = get_connection("db_usuarios")
        cursor = conn.cursor()
        query = """
            INSERT INTO usuario
            (id_usuario, usuario, email, contrasena, region)
            VALUES (%s,%s,%s,%s,%s)
        """
        cursor.execute(query,(id_usuario,usuario,email,contrasena,region,))
        conn.commit()

        return jsonify({"mensaje":"Se a añadido de manera correcta el usuario"}),201

    except Exception as e:
        if isinstance(error_db,e):
            if conn:
                conn.rollback()
            return jsonify({"error":"Hubo un fallo en la base de datos","detalle":str(e)}),500
        return jsonify({"error":"Hubo un fallo al intentar ingresar los datos","detalle":str(e)}),500
    finally:
        cursor.close()
        if conn:
            release_connection("db_usuarios",conn)

        payload = {"usuario":usuario, 
                   "email":email,
                   "region":region}
        
        publicar_evento("usuario.registrado",payload)


# Verificar un log in
#
# GET /login
# Content-type: application/json
# {
#   "email" : "Weezer@gmail.com",
#   "contrasena" : "para entender"
# }
@app.route('/login',methods=['GET'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    email = data.get('email')
    contrasena = data.get('contrasena')

    conn = None
    try:
        conn = get_connection("db_usuarios")
        cursor = conn.cursor()
        query = """
            SELECT *
            FROM usuario
            WHERE email = %s AND contrasena = %s
        """
        cursor.execute(query,(email,contrasena,))
        usuario = cursor.fetchall()

        if not usuario:
            return jsonify({"error":"El usuario no existe en la base de datos"}),404

        return jsonify({"mensaje":"Sesion iniciada",
                        "usuario":usuario}),200
    except Exception as e:
        return jsonify({"error":"Hubo un fallo al intentar buscar los datos","detalle":str(e)}),500
    
    finally:
        cursor.close()
        if conn:
            release_connection("db_usuarios",conn)

# Solicitar datos de un usuario
#
# GET /usuario_olvidado?email=algo
@app.route('/usuario_olvidado',methods=['GET'])
def meolvide():
    email = request.args.get('email')

    conn = None
    try:
        conn = get_connection("db_usuarios")
        cursor = conn.cursor()
        query = """
            SELECT usuario, email
            FROM usuario
            WHERE email = %s
        """
        cursor.execute(query,(email,))
        correo = cursor.fetchall()

        if not correo:
            return jsonify({"error":"El usuario no existe en la base de datos"}),404
        
        
        payload = {"usuario":correo[0][0],
                    "email":email}
        publicar_evento("usuario.olvidado",payload)

        return jsonify({"mensaje":"Enviado mensaje para recuperar contrasena"}),200

    except Exception as e:
        return jsonify({"error":"Hubo un fallo al intentar buscar los datos","detalle":str(e)}),500
    finally:
        cursor.close()
        if conn:
            release_connection("db_usuarios",conn)

if __name__ == "__main__":
    main()