import uuid
import json
from shared.cache import redis_client
from shared.messaging import publicar_evento
from shared.database import get_connection, release_connection

def procesar_checkout(usuario_id, email):
    """
    Simula la recepcion de una solicitud de compra.
    Lee el carrito de Redis respetando el contrato definido, emite el evento y limpia la cache.
    """
    try:
        # Leer el carrito de Redis con la clave del contrato
        clave_redis = f"cart:{usuario_id}"
        carrito_raw = redis_client.get(clave_redis)
        
        # Si no tiene nada
        if not carrito_raw:
            print(f"[Ventas] Checkout rechazado. El carrito del usuario {usuario_id} esta vacio.")
            return False
            
        # Deserializar el objeto completo segun el contrato
        datos_carrito = json.loads(carrito_raw)
        items_carrito = datos_carrito.get("items", [])
        region_compra = datos_carrito.get("region_compra", "LATAM")   # LATAM como Fallback
        total_estimado = datos_carrito.get("total_estimado", 0)
        
        if not items_carrito:
            print(f"[Ventas] Checkout rechazado. El carrito no tiene items.")
            return False

        # Generar un identificador unico para esta transaccion
        id_orden_compra = f"ORD-{str(uuid.uuid4())[:8].upper()}"
        print(f"[Ventas] Iniciando checkout para la orden {id_orden_compra}...")

        # Registrar la orden como PENDIENTE
        db_name = "db_ventas"
        conn = None
        try:
            conn = get_connection(db_name)
            cur = conn.cursor()
            
            # Guardamos el total estimado en total_pagado temporalmente
            query_insert = """
                INSERT INTO orden_compra (id_orden_compra, id_usuario, total_pagado, estado_pago) 
                VALUES (%s, %s, %s, 'PENDIENTE');
            """
            cur.execute(query_insert, (id_orden_compra, usuario_id, total_estimado))
            conn.commit()
            cur.close()
            print(f"[Ventas] BD: Orden {id_orden_compra} registrada como PENDIENTE.")
            
        except Exception as e_db:
            if conn:
                conn.rollback()
            print(f"[!] Error de BD al registrar orden: {e_db}")
            return False 
        finally:
            if conn:
                release_connection(db_name, conn)

        # Empaquetar el Payload con el contrato de datos exacto que Inventario espera
        evento_orden = {
            "id_orden_compra": id_orden_compra,
            "usuario_id": usuario_id,
            "email": email,
            "region": region_compra,
            "items": items_carrito,
            "total_estimado": total_estimado
        }

        # Publicar el evento
        publicar_evento('orden.creada', evento_orden)
        print(f"[Ventas] Evento publicado en 'orden.creada'.")

        # Conservar el carrito temporalmente ante posibles fallos (Expira en 24h)
        redis_client.expire(clave_redis, 86400)
        print(f"[Ventas] TTL de 24h configurado para el carrito de {usuario_id}.")
        
        return id_orden_compra

    except Exception as e:
        print(f"[!] Error en el Modulo de Ventas al procesar checkout: {e}")
        return False
