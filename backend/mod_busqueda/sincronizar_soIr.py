""" cargamos catalogo a Solr desde Postgres al iniciar el contenedor de búsqueda. 
Esto es para tener datos en Solr desde el arranque """

# Ejecutar con docker exec -it python_search python /app/mod_busqueda/sincronizar_solr.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pysolr

print("Iniciando Bootstrapping: Sincronizando catálogo desde Postgres hacia Solr...")

# 1. Configurar conexión a Solr
SOLR_URL = 'http://solr_engine:8983/solr/catalogo'
solr = pysolr.Solr(SOLR_URL, always_commit=True)

try:
    # 2. Configurar conexión a PostgreSQL
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db_main'),
        database='db_catalogo',
        user=os.environ.get('POSTGRES_USER', 'admin'),
        password=os.environ.get('POSTGRES_PASSWORD', 'adminpassword')
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 3. Leer los juegos
    cur.execute("SELECT * FROM catalogo")
    juegos = cur.fetchall()
    
    # 4. Formatear para Solr
    documentos = []
    for juego in juegos:
        documentos.append({
            "id": juego['id_juego'],
            "titulo": juego['titulo'],
            "plataforma": juego['plataforma'],
            "precio_base": float(juego['precio_base']),
            "stock": 2 # Stock base para pruebas
        })
        
    # 5. Inyectar en Solr
    solr.add(documentos)
    print(f"¡Éxito! Se sincronizaron {len(documentos)} juegos en Apache Solr.")

except Exception as e:
    print(f"Error fatal de sincronización: {e}")
finally:
    if 'conn' in locals() and conn is not None:
        conn.close()