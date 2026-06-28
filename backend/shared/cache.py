import os
import json
import redis

# ENV
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
USER_SESSION_EXPIRATION_TIME = os.environ.get("USER_SESSION_EXPIRATION_TIME", "3600")
MAX_CACHE_POOL_CONNS = os.environ.get("MAX_CACHE_POOL_CONNS", "50")

try:
    # Intenta definir una piscina de conexiones a Redis con un maximo de conexiones
    # para evitar consumir demasiada memoria RAM durante picos de trafico
    redis_pool = redis.ConnectionPool(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        decode_responses=True,
        max_connections=int(MAX_CACHE_POOL_CONNS),
        password=REDIS_PASSWORD
    )
    redis_client = redis.Redis(connection_pool=redis_pool)
    print("[Cache] Piscina de conexiones a Redis inicializada.")
except Exception as e:
    print(f"[!] Error conectando a Redis: {e}")


# ----- USER SESSION -----

# Guarda una sesion de usuario
def set_sesion(token, datos_usuario, expiracion_segundos=USER_SESSION_EXPIRATION_TIME):
    """Guarda una sesion de usuario"""
    clave = f"session:{token}"
    redis_client.setex(clave, expiracion_segundos, json.dumps(datos_usuario))

# Obtiene y deserializa una sesion de usuario
def get_sesion(token):
    """Obtiene y deserializa una sesion de usuario"""
    datos = redis_client.get(f"session:{token}")
    if datos:
        return json.loads(datos)
    return None

def delete_sesion(token):
    redis_client.delete(f"session:{token}")


# ----- Carrito -----

# Guarda el estado del carrito del usuario
def set_carrito(usuario_id, datos_carrito):
    """Guarda el estado del carrito de compras - Sin expiracion"""
    clave = f"carrito:{usuario_id}"
    redis_client.set(clave, json.dumps(datos_carrito))

# Obtiene y deserializa el carrito del usuario
def get_carrito(usuario_id):
    """Obtiene y deserializa el carrito de compras"""
    datos = redis_client.get(f"carrito:{usuario_id}")
    if datos:
        return json.loads(datos)
    return {"items": [], "total_estimado": 0, "region_compra": "LATAM"}


# ----- Catalogo y Busqueda -----

def set_cache_busqueda(clave, datos_respuesta, expiracion_segundos=600):
    """
    Guarda los resultados de una busqueda o los detalles de un juego en la cache.
    Por defecto, los datos expiran en 10 minutos (600 segundos).
    """
    try:
        redis_client.setex(clave, expiracion_segundos, json.dumps(datos_respuesta))
    except Exception as e:
        print(f"[!] Error guardando en cache la clave {clave}: {e}")

def get_cache_busqueda(clave):
    """
    Obtiene y deserializa los resultados de busqueda desde la cache.
    Retorna None si la clave no existe o si expiro.
    """
    try:
        datos = redis_client.get(clave)
        if datos:
            return json.loads(datos)
    except Exception as e:
        print(f"[!] Error leyendo de cache la clave {clave}: {e}")
    return None

