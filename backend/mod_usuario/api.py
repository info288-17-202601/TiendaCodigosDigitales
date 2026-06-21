from flask import Flask, request, jsonify
from shared.database import get_connection, release_connection
from shared.messaging import publicar_evento
from psycopg2 import Error as error_db # Para sacar un Error de Psycopg2
import redis # Para la cache
import os # Para sacar Variables de entonro
import json
from argon2 import PasswordHasher # Para Codificar
# Definicion principal del Modulo de usuarios

# Clave de incriptacion : FUTURO FUTURO FUTURO
app = Flask(__name__)

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
redis_client = redis.Redis(
        host=REDIS_HOST,
        port=6379,
        db=0,
        decode_responses=True
    )

def connect_redis():
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=6379,
        db=0,
        decode_responses=True
    )

    try:
        redis_client.ping()
    except Exception as e:
        print(f"Error al intentar realizar la conexion\n Detalles: {e}")

def main():
    app.run(host='0.0.0.0', port=5006)

@app.route('/cache_reconect',methods=['GET'])
def reconectar():
    connect_redis()

# Solicitar datos de un usuario
#
# GET /usuario?id_usuario=algo
@app.route('/usuario',methods=['GET'])
def getUsuario():
    id_usuario = request.args.get('id_usuario')
    if id_usuario:
        cache_key = f"usuario:{id_usuario}"
        try:
            resultado = redis_client.get(cache_key)
            if resultado:
                return jsonify({"mensaje":"usuario encontrado",
                                "detalle":json.loads(resultado)}),200
            
        except Exception as e:
            print(f"No se encontro la conexion con la cache\n Detalles: {e}")

    
        # Conexiando
        conn = None
        try:
            conn = get_connection("db_usuarios")
            cursor = conn.cursor()
            query = """
                SELECT email,usuario,usuario_id,region
                FROM usuario
                WHERE id_usuario = %s
            """
            cursor.execute(query,(id_usuario,))
            usuario = cursor.fetchall()

            if not usuario:
                return jsonify({"error","El usuario no existe en la base de datos"}),404

            redis_client.setex(cache_key,60*60*24,json.dumps(usuario))
            return jsonify({"mensaje":"Usuario encontrado",
                            "usuario":usuario}),200
        except Exception as e:
            return jsonify({"error":"Hubo un fallo al intentar ingresar los datos","detalle":str(e)}),500
        
        finally:
            cursor.close()
            if conn:
                release_connection("db_usuarios",conn)
    return jsonify({"error":"No se ingreso nada"}),400
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
# Conste que no deberia guardarse nada, solo luego del login
@app.route('/registrar',methods=['PUT'])
def añadir_usuario():
    data = request.get_json()
    ph = PasswordHasher()
    if not data:
        return jsonify({"error":"No se entregaron parametros"}),400
    id_usuario = data.get('usuario_id') # Pega para ti vito :3
    usuario = data.get('usuario')
    email = data.get('email')
    contrasena = ph.hash(data.get('contrasena'))
    region = data.get('region')

    if not (id_usuario and usuario and email and contrasena and region):
        return jsonify({"error":"Los datos ingresados son erroneos o estan vacios"}),400

    conn = None
    try:
        conn = get_connection("db_usuarios")
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
            (id_usuario, usuario, email, contrasena, region)
            VALUES (%s,%s,%s,%s,%s)
        """
        cursor.execute(query,(id_usuario,usuario,email,contrasena,region,))
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
        conn = get_connection("db_usuarios")
        cursor = conn.cursor()
        query = """
            SELECT contrasena,usuario,id_usuario,email,region
            FROM usuario
            WHERE email = %s
        """
        cursor.execute(query,(email,))
        usuario = cursor.fetchall()

        if not usuario:
            return jsonify({"error":"El usuario no existe en la base de datos"}),404

        contrasena_hashed = usuario[0][0]

        if ph.verify(contrasena_hashed,contrasena):
            redis_client.setex(f"usuario:{usuario:[0][3]}",60*60*24,json.dumps([usuario[0][1],usuario[0][2],
                                                                                usuario[0][3]],usuario[0][4]))
            return jsonify({"mensaje":"Sesion iniciada",
                            "usuario":usuario}),200

        else:
            return jsonify({"error":"Email o contrasena incorrecta"}),401
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