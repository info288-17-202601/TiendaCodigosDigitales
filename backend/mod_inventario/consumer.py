import json
import time
from shared.messaging import iniciar_multiples_consumidores, publicar_evento
from mod_inventario.service import reservar_codigo_seguro, liberar_codigo_seguro

# ----- Callbacks -----

def procesar_orden_creada(ch, method, properties, body):
    """
    Callback que procesa multiples items con esquema "Todo o Nada".
    """
    try:
        datos_orden = json.loads(body)
        id_orden_compra = datos_orden.get('id_orden_compra') 
        usuario_id = datos_orden.get('usuario_id')
        usuario_email = datos_orden.get("email")
        region = datos_orden.get('region', 'LATAM')
        items = datos_orden.get('items', [])
        metodo_pago = datos_orden.get('metodo_pago')
        total_estimado = datos_orden.get('total_estimado')

        
        if not items:
            print(f"[Inventario] Orden {id_orden_compra} rechazada: Carrito vacio.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        print(f"[*] Procesando orden {id_orden_compra} con {len(items)} items | Region: {region} | Metodo de pago: {metodo_pago}")

        reservas_exitosas = []
        juegos_sin_stock = []

        # Iterar sobre todos los elementos del carrito
        for item in items:
            juego_id = item.get('juego_id')
            juego_titulo = item.get('titulo')
            resultado_reserva = reservar_codigo_seguro(juego_id, region, id_orden_compra)

            if resultado_reserva:
                # Almacenar la reserva exitosa añadiendo el juego_id para el payload final
                resultado_reserva['juego_id'] = juego_id
                reservas_exitosas.append(resultado_reserva)
            else:
                juegos_sin_stock.append({"juego_id": juego_id, "titulo": juego_titulo})   
                
            
        # ¿Hubo al menos un fallo de stock?
        if len(juegos_sin_stock) > 0:
            
            # Revertir las reservas que si tuvieron exito
            print(f"[Inventario] Falto stock para los juegos: {juegos_sin_stock}. Iniciando rollback...")
            for reserva in reservas_exitosas:
                liberar_codigo_seguro(reserva['id_clave'], region)
            print(f"[Inventario] Rollback completo para la orden {id_orden_compra}.")        
            
            # Emitir evento de fallo total con la lista de juegos agotados
            evento_fallo = {
                "id_orden_compra": id_orden_compra,
                "usuario_id": usuario_id,
                "usuario_email": usuario_email,
                "metodo_pago": metodo_pago,
                "motivo": "OUT_OF_STOCK",
                "juegos_sin_stock": juegos_sin_stock # Enviamos la lista completa al Modulo de Ventas
            }
            publicar_evento('inventario.fallido', evento_fallo)
            print(f"[Inventario] Evento 'inventario.fallido' publicado con {len(juegos_sin_stock)} juegos sin stock.")

        # Si la lista de fallos esta vacia
        else:
            evento_exito = {
                "id_orden_compra": id_orden_compra,
                "usuario_id": usuario_id,
                "region": region,
                "usuario_email": usuario_email,
                "items": reservas_exitosas, 
                "estado_reserva": "EXITO",
                "metodo_pago": metodo_pago,
                "monto_a_cobrar": total_estimado,
            }
            publicar_evento('inventario.reservado', evento_exito)
            print(f"[Inventario] exito total. Evento 'inventario.reservado' publicado.")

        # Confirmacion Critica
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[!] Error inesperado en consumidor de inventario: {e}")


def callback_pago_inventario(ch, method, properties, body):
    payload = json.loads(body)
    id_orden_compra = payload.get('id_orden_compra')
    metodo_pago = payload.get('metodo_pago')
    estado_pago = payload.get('estado_pago')
    region = payload.get('region')

    # Si la compra fue exitosa registrar la clave como VENDIDO
    if (estado_pago == "APROBADO"):
        db_name = get_inventory_db_name(region)
        conn = None
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()

            # Usamos UPDATE
            query = """
                UPDATE clave_digital
                SET estado = 'VENDIDO' 
                WHERE id_orden_compra = %s;
            """
            cur.execute(query, (id_orden_compra,))
            conn.commit()
            cur.close()
            
            print(f"[Inventario] BD Actualizada: claves con orden {id_orden_compra} como VENDIDO.")

        except Exception as e_db:
                if conn:
                    conn.rollback()
                print(f"[!] Error de base de datos en inventario: {e_db}")
                raise e_db 

        finally:
            if conn:
                release_connection(db_name, conn)

    # Si la compra fue fallida registrar la clave como DISPONIBLE
    elif (estado_pago == "NO APROBADO"):
        db_name = get_inventory_db_name(region)
        conn = None
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()

            # Usamos UPDATE
            query = """
                UPDATE clave_digital
                SET estado = 'DISPONIBLE', id_orden_compra = NULL 
                WHERE id_orden_compra = %s;
            """
            cur.execute(query, (id_orden_compra,))
            conn.commit()
            cur.close()
            
            print(f"[Inventario] BD Actualizada: claves con orden {id_orden_compra} como DISPONIBLE.")

        except Exception as e_db:
                if conn:
                    conn.rollback()
                print(f"[!] Error de base de datos en inventario: {e_db}")
                raise e_db 

        finally:
            if conn:
                    release_connection(db_name, conn)

    else:
         print(f"[Inventario] Comportamiento inesperado: claves con id de orden {id_orden_compra} recibieron estado no reconocido {estado_pago}.")
         
    ch.basic_ack(delivery_tag=method.delivery_tag)



if __name__ == '__main__':
    mis_colas = [
        # Cola clasica directa para orden creada
        {
            "cola": "orden.creada", 
            "callback": procesar_orden_creada
        },
        
        # Cola compartida para pago procesado
        {
            "cola": "cola_inventario_pagos",
            "exchange": "tienda_exchange",
            "routing_key": "pago.procesado",
            "callback": callback_pago_inventario
        }
    ]
    
    iniciar_multiples_consumidores(mis_colas)