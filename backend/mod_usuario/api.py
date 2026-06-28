from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.database import get_connection, release_connection
from shared.messaging import publicar_evento
from shared.cache import set_sesion,get_sesion,delete_sesion
from psycopg2 import Error as error_db # Para sacar un Error de Psycopg2
import os # Para sacar Variables de entonro
import json
from secrets import token_urlsafe
from argon2 import PasswordHasher # Para Codificar
# Definicion principal del Modulo de usuarios

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DB_USER = os.environ.get("DB_USER_USUARIOS", "user_usuarios")
DB_PASS = os.environ.get("DB_PASS_USUARIOS", "PassUser456")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

def main():
    app.run(host='0.0.0.0', port=5006)

# Solicitar datos de un usuario
#
# GET /usuario?token=algo
@app.route('/usuario',methods=['GET'])
def getUsuario():
    token = request.args.get('token')
    if token:
        try:
            resultado = get_sesion(token)
            if resultado:
                return jsonify({"mensaje":"usuario encontrado",
                                "detalle":json.loads(resultado)}),200
            
            else:
                return jsonify({"error":"usuario no encontrado"}),401
            
        except Exception as e:
            return jsonify({"error":"Ocurrio un error al intentar conseguir los datos","detalle":e}),402

    return jsonify({"error":"No se ingreso nada"}),400
# Añadir un usuario a la BD
#
# POST /registrar
# Content-type: application/json
# {
#   "usuario" : "asdasda",
#   "email" : "Weezer@gmail.com",
#   "contrasena" : "para entender",
#   "region" : "LATAM"
# }
# Conste que no deberia guardarse nada, solo luego del login
@app.route('/registrar',methods=['POST'])
def añadir_usuario():
    data = request.get_json()
    ph = PasswordHasher()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    usuario = data.get('usuario')
    email = data.get('email')
    contrasena = ph.hash(data.get('contrasena'))
    region = data.get('region')

    if not (usuario and email and contrasena and region):
        return jsonify({"error":"Los datos ingresados son erroneos o estan vacios"}),400

    conn = None
    try:
        conn = get_connection("db_usuarios", DB_USER, DB_PASS)
        cursor = conn.cursor()
        query = """
            SELECT email
            FROM usuario
            WHERE email = %s
        """
        cursor.execute(query,(email,))

        encontrado = cursor.fetchall()
        
        if encontrado:
            return jsonify({"error":"Ya existe un usuario con este correo"}),400

        query = """
            INSERT INTO usuario
            ( usuario, email, contrasena, region, rol)
            VALUES (%s,%s,%s,%s,%s)
        """
        cursor.execute(query,(usuario,email,contrasena,region,"usuario",))
        conn.commit()
        payload = {"usuario":usuario, 
                   "email":email,
                   "region":region}
        
        publicar_evento("usuario.registrado",payload)
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
    ph = PasswordHasher()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    email = data.get('email')
    contrasena = data.get('contrasena')

    conn = None
    try:
        conn = get_connection("db_usuarios", DB_USER, DB_PASS)
        cursor = conn.cursor()
        query = """
            SELECT contrasena,usuario,email,region,rol,id_usuario
            FROM usuario
            WHERE email = %s
        """
        cursor.execute(query,(email,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"error":"El usuario no existe en la base de datos"}),404

        contrasena_hashed = usuario[0]

        if ph.verify(contrasena_hashed,contrasena):
            token = token_urlsafe(32)
            cache_sesion = {
                "id_usuario" : usuario[5],
                "usuario" : usuario[1],
                "correo" : usuario[2],
                "region": usuario[3],
                "rol": usuario[4]
            }
            set_sesion(token,cache_sesion)
            return jsonify({"mensaje":"Sesion iniciada",
                            "token":token,
                            "usuario":cache_sesion}),200

        else:
            return jsonify({"error":"Email o contrasena incorrecta"}),401
    except Exception as e:
        return jsonify({"error":"Hubo un fallo al intentar buscar los datos","detalle":str(e)}),500
    
    finally:
        cursor.close()
        if conn:
            release_connection("db_usuarios",conn)

# Solicitud cambio de contraseña para un usuario
#
# GET /usuario_olvidado?email=algo
@app.route('/usuario_olvidado',methods=['GET'])
def meolvide():
    email = request.args.get('email')

    conn = None
    try:
        conn = get_connection("db_usuarios", DB_USER, DB_PASS)
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

# Solicitud para salir de la sesion
#
# GET /logout?token=algo
@app.route('/logout',methods=['GET'])
def logout():
    token = request.args.get('token')
    if not token :
        return jsonify({"error":"No se entregaron los datos"}),400
    
    try:
        delete_sesion(token)
        return jsonify({"mensaje":"La sesion fue cerrada con exito"}),200

    except Exception as e:
        return jsonify({"error":"hubo un error al intentar cerrar la sesion","detalle":e}),400

if __name__ == "__main__":
    main()