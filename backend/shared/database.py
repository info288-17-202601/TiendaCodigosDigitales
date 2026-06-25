import os
import threading
import time
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

# ENV
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("POSTGRES_USER", "admin")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "adminpassword")
DB_PORT = os.environ.get("DB_PORT", "5432")
MAX_DB_POOL_CONNS = os.environ.get("MAX_DB_POOL_CONNS", "20")

# Diccionario global almacenado en memoria del proceso
_connection_pools = {}

# Lock para evitar que varios hilos creen la misma piscina al mismo tiempo
_pool_lock = threading.Lock()


# Router de shards:
# recibe una region y retorna el nombre de la base de datos correspondiente
def get_inventory_db_name(region):
    """
    Router de shards:
    recibe una region y retorna el nombre de su base de datos
    """
    shards = {
        "LATAM": "db_inv_latam",
        "NA": "db_inv_na",
        "EU": "db_inv_eu"
    }
    return shards.get(region.upper(), "db_inv_latam")


# Obtiene y retorna una conexion desde la piscina de <db_name>
def get_connection(db_name, db_user=None, db_pass=None):
    """Obtiene y retorna una conexion desde la piscina de <db_name>"""
    # Fallback
    user = db_user if db_user else os.environ.get("POSTGRES_USER", "admin")
    password = db_pass if db_pass else os.environ.get("POSTGRES_PASSWORD", "adminpassword")

    with _pool_lock:
        if db_name not in _connection_pools:
            try:
                # Hace la piscina
                _connection_pools[db_name] = ThreadedConnectionPool(
                    1, MAX_DB_POOL_CONNS,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=db_name,
                    user=user,
                    password=password,
                    cursor_factory=RealDictCursor
                )
                print(f"[Database] Piscina creada para '{db_name}' con usuario '{user}'")
            except Exception as e:
                print(f"[!] Error creando el pool para '{db_name}': {e}")
                raise e
                
    # Extrae una conexion inactiva desde la piscina
    return _connection_pools[db_name].getconn()

# Devuelve una conexion a la piscina
def release_connection(db_name, conn):
    """Devuelve una conexion a la piscina"""
    if db_name in _connection_pools:
        _connection_pools[db_name].putconn(conn)



