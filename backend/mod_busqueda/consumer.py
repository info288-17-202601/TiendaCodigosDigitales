import json
import sys
import os
import pysolr
import psycopg2
from psycopg2.extras import RealDictCursor

# Raíz del backend al path para poder importar shared
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.messaging import iniciar_consumidor

# Configuramos la conexión a Solr
SOLR_URL = 'http://solr_engine:8983/solr/catalogo'
solr = pysolr.Solr(SOLR_URL, always_commit=True)

# Función auxiliar para conectarnos a Postgres
def obtener_conexion_db():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db_main'),
        database='db_catalogo',
        user=os.environ.get('POSTGRES_USER', 'admin'),
        password=os.environ.get('POSTGRES_PASSWORD', 'adminpassword')
    )

def callback_busqueda(ch, method, properties, body):
    conn = None
    try:
        # 1. Decodificamos el mensaje que viene de Inventario 
        # EJ: {'evento': 'stock_agotado_region', 'id_juego': 'splatoon-3', 'region': 'LATAM'}
        mensaje = json.loads(body.decode())
        print(f" [x] Búsqueda recibió evento: {mensaje}", flush=True)

        id_juego = mensaje.get('juego_id') 
        region_agotada = mensaje.get('region')

        # 2. Lógica para evento de Stock Agotado por Región
        if id_juego and region_agotada:
            print(f" [*] Procesando agotamiento de '{id_juego}' en la región {region_agotada}...", flush=True)
            
            # ACTUALIZAR POSTGRESQL 
            conn = obtener_conexion_db()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Traemos el juego actual para ver su JSON de disponibilidad
            cur.execute("SELECT disponibilidad_regional FROM catalogo WHERE id_juego = %s", (id_juego,))
            resultado_db = cur.fetchone()
            
            if resultado_db:
                # Modificamos el JSON: Ponemos en "false" la región que se agotó
                json_disponibilidad = resultado_db['disponibilidad_regional']
                json_disponibilidad[region_agotada] = False 
                
                # Guardamos el JSON actualizado en Postgres
                cur.execute(
                    "UPDATE catalogo SET disponibilidad_regional = %s WHERE id_juego = %s",
                    (json.dumps(json_disponibilidad), id_juego)
                )
                conn.commit()
                print(f" [v] Postgres actualizado: {id_juego} ahora tiene {region_agotada}: false", flush=True)
                
                # ACTUALIZAR SOLR (El buscador) 
                resultados_solr = solr.search(f'id:{id_juego}')
                if len(resultados_solr) > 0:
                    juego_solr = resultados_solr.docs[0]
                    # Solr guarda la disponibilidad_regional como un string que hay que parsear a dict si es necesario
                    # Pero en un escenario simple, con modificar Postgres el Bootstrapping futuro lo leerá bien.
                    # Para mantener sincronizado Solr en vivo:
                    juego_solr['disponibilidad_regional'] = json.dumps(json_disponibilidad)
                    solr.add([juego_solr])
                    print(f" [v] Solr actualizado para reflejar la nueva disponibilidad.", flush=True)
                else:
                    print(f" [!] Advertencia: Juego no encontrado en Solr.", flush=True)
            else:
                print(f" [!] Error: Juego {id_juego} no existe en PostgreSQL.", flush=True)
                
            if cur:
                cur.close()

        # Confirmación manual del mensaje (¡Importante para RabbitMQ!)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
         print(f" [X] Error procesando mensaje en Búsqueda: {e}", flush=True)
         if conn:
             conn.rollback() # Si algo falla, deshacemos cambios en DB
    finally:
        if conn is not None:
            conn.close()

def iniciar_escucha_busqueda():
    iniciar_consumidor('inventario.agotado', callback_busqueda)

if __name__ == '__main__':
    iniciar_escucha_busqueda()