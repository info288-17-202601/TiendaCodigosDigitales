import json
import time
from shared.messaging import iniciar_consumidor
from shared.database import get_connection, release_connection

def procesar_inventario_fallido(ch, method, properties, body):
    """
    Callback sincronico que escucha cuando el Modulo de Inventario 
    rechaza una orden por falta de stock y registra el historial final.
    """
    try:
        # Deserializar el mensaje
        datos_fallo = json.loads(body)
        id_orden_compra = datos_fallo.get('id_orden_compra')
        usuario_id = datos_fallo.get('usuario_id')
        motivo = datos_fallo.get('motivo')

        print(f"[Ventas] Reaccion del Modulo de Ventas al fallo de la orden {id_orden_compra}")
        print(f"         - Usuario afectado: {usuario_id}")
        print(f"         - Motivo del rechazo: {motivo}")

        # Insercion en la Base de Datos de Ventas (Historial de Fallo)
        db_name = "db_ventas"
        conn = None
        
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()
            
            # Usamos UPDATE, buscando la orden PENDIENTE
            query = """
                UPDATE orden_compra 
                SET estado_pago = 'FALLIDO' 
                WHERE id_orden_compra = %s;
            """
            cur.execute(query, (id_orden_compra,))
            conn.commit()
            cur.close()
            
            print(f"[Ventas] BD Actualizada: Orden {id_orden_compra} marcada como FALLIDO por stock.")
            
        except Exception as e_db:
            if conn:
                conn.rollback()
            print(f"[!] Error de base de datos en Ventas: {e_db}")
            raise e_db 
            
        finally:
            if conn:
                release_connection(db_name, conn)

        # Confirmacion Critica: Enviar ACK a RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[Ventas] ACK enviado. Incidente cerrado y borrado de la cola.")

    except Exception as e:
        print(f"[!] Error el consumidor de fallos de ventas: {e}")

if __name__ == '__main__':
    print("Iniciando Consumidor de Ventas (Escuchando fallos de inventario)...")
    time.sleep(2) 
    iniciar_consumidor('inventario.fallido', procesar_inventario_fallido)