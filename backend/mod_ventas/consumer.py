import json
import time
from shared.messaging import iniciar_multiples_consumidores
from shared.database import get_connection, release_connection
from shared.cache import get_carrito, set_carrito

# ----- Callbacks -----

def callback_pago_ventas(ch, method, properties, body):
    payload = json.loads(body)
    id_orden_compra = payload.get('id_orden_compra')
    metodo_pago = payload.get('metodo_pago')
    estado_pago = payload.get('estado_pago')
    usuario_id = payload.get('usuario_id')

    # Si la compra fue exitosa registrar la orden como PAGADO
    if (estado_pago == "APROBADO"):
        db_name = "db_ventas"
        conn = None
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()

            # Usamos UPDATE
            query = """
                UPDATE orden_compra 
                SET estado_pago = 'PAGADO' 
                WHERE id_orden_compra = %s;
            """
            cur.execute(query, (id_orden_compra,))
            conn.commit()
            cur.close()
            
            print(f"[Ventas] BD Actualizada: Orden {id_orden_compra} como PAGADO.")

            # Liberar carrito
            if usuario_id:
                carrito = get_carrito(usuario_id)
                if carrito:
                    carrito['items'] = []
                    carrito['total_estimado'] = 0
                    set_carrito(usuario_id, carrito)
                    print(f"[Ventas] Carrito liberado para el usuario {usuario_id}")

        except Exception as e_db:
                if conn:
                    conn.rollback()
                print(f"[!] Error de base de datos en Ventas: {e_db}")
                raise e_db 

        finally:
            if conn:
                    release_connection(db_name, conn)

    # Si la compra fue fallida registrar la ordn como FALLIDO
    elif (estado_pago == "NO APROBADO"):
        db_name = "db_ventas"
        conn = None
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()

            # Usamos UPDATE
            query = """
                UPDATE orden_compra 
                SET estado_pago = 'FALLIDO' 
                WHERE id_orden_compra = %s;
            """
            cur.execute(query, (id_orden_compra,))
            conn.commit()
            cur.close()
            
            print(f"[Ventas] BD Actualizada: Orden {id_orden_compra} como FALLIDO.")

        except Exception as e_db:
                if conn:
                    conn.rollback()
                print(f"[!] Error de base de datos en Ventas: {e_db}")
                raise e_db 

        finally:
            if conn:
                    release_connection(db_name, conn)

    else:
         print(f"[Ventas] Comportamiento inesperado: Orden {id_orden_compra} recibio estado no reconocido {estado_pago}.")
         
    ch.basic_ack(delivery_tag=method.delivery_tag)


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
        metodo_pago = datos_fallo.get('metodo_pago')
        motivo = datos_fallo.get('motivo')

        print(f"[Ventas] Reaccion del Modulo de Ventas al fallo de la orden {id_orden_compra}")
        print(f"         - Usuario afectado: {usuario_id}")
        print(f"         - Metodo de pago: {metodo_pago}")
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
    mis_colas = [
        # Cola clasica directa para inventario fallido
        {
            "cola": "inventario.fallido", 
            "callback": procesar_inventario_fallido
        },
        
        # Cola compartida para pago procesado
        {
            "cola": "cola_ventas_pagos",
            "exchange": "tienda_exchange",
            "routing_key": "pago.procesado",
            "callback": callback_pago_ventas
        }
    ]
    
    iniciar_multiples_consumidores(mis_colas)


