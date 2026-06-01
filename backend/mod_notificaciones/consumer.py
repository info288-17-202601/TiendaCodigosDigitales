import json
import time

from shared.messaging import iniciar_multiples_consumidores
from mod_notificaciones.service import (
    enviar_notificacion_compra, 
    enviar_notificacion, 
    armar_mensaje_generico
)
from shared.database import get_connection, release_connection

def obtener_codigos_vendidos(id_orden_compra, region):
    # Intentamos leer de la BD de inventario correspondiente a la region para recuperar los códigos confirmados
    # Asumimos que los codigos se marcaron como VENDIDO en mod_inventario/consumer.py
    # Y que tienen asociado el id_orden_compra.
    db_name = f"db_inv_{region.lower()}" if region else "db_inv_latam"
    conn = None
    codigos = []
    try:
        conn = get_connection(db_name)
        cur = conn.cursor()
        query = "SELECT codigo_serial FROM clave_digital WHERE id_orden_compra = %s;"
        cur.execute(query, (id_orden_compra,))
        filas = cur.fetchall()
        for fila in filas:
            codigos.append(fila[0])
        cur.close()
    except Exception as e:
        print(f"[Notificaciones] No se pudieron recuperar códigos de {db_name}: {e}")
    finally:
        if conn:
            release_connection(db_name, conn)
    return codigos

def procesar_evento_pago(ch, method, properties, body):
    try:
        datos = json.loads(body)
        id_orden_compra = datos.get('id_orden_compra')
        usuario_id = datos.get('id_usuario') or datos.get('usuario_id')
        email = datos.get('usuario_email') or f"{usuario_id}@usuario.local" # Fallback si no viene email
        estado_pago = datos.get('estado_pago')
        motivo = datos.get('motivo')
        region = datos.get('region', 'latam')

        if estado_pago == "APROBADO":
            print(f"[Notificaciones] Pago aprobado para orden {id_orden_compra}. Recuperando códigos...")
            # Damos un pequeñisimo margen para asegurar que el inventario hizo el commit de los códigos a 'VENDIDO'
            time.sleep(1) 
            codigos = obtener_codigos_vendidos(id_orden_compra, region)
            
            if codigos:
                enviar_notificacion_compra(email, id_orden_compra, "Varios", codigos)
            else:
                print(f"[Notificaciones] ALERTA: Pago aprobado pero no se encontraron códigos reservados para orden {id_orden_compra}")

        elif estado_pago == "NO APROBADO":
            asunto = f"Aviso sobre tu orden de compra {id_orden_compra}"
            cuerpo = armar_mensaje_generico(asunto, f"Tu pago no fue aprobado.\nMotivo: {motivo}")
            enviar_notificacion(email, asunto, cuerpo)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error inesperado en notificaciones/pagos: {e}")

def procesar_inventario_fallido(ch, method, properties, body):
    try:
        datos_fallo = json.loads(body)
        id_orden_compra = datos_fallo.get('id_orden_compra')
        email = datos_fallo.get('usuario_email')
        juegos_sin_stock = datos_fallo.get('juegos_sin_stock', [])

        if email:
            nombres_agotados = ", ".join([j.get('titulo', 'Desconocido') for j in juegos_sin_stock])
            asunto = f"Problemas de stock con tu orden {id_orden_compra}"
            mensaje = f"Lo sentimos, no pudimos completar tu orden total debido a la falta de stock de los siguientes juegos: {nombres_agotados}."
            cuerpo = armar_mensaje_generico(asunto, mensaje)
            enviar_notificacion(email, asunto, cuerpo)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error procesando fallo de inventario en notificaciones: {e}")


if __name__ == '__main__':
    print("Iniciando Consumidor del Modulo de Notificaciones...")
    time.sleep(2)

    mis_colas = [
        # Escuchar pagos (éxitos para códigos y rechazos para avisos)
        {
            "cola": "cola_notificaciones_pagos",
            "exchange": "tienda_exchange",
            "routing_key": "pago.procesado",
            "callback": procesar_evento_pago
        },
        # Escuchar inventario (cuando falta stock)
        {
            "cola": "notificaciones_inventario.fallido",
            "exchange": "tienda_exchange",
            "routing_key": "inventario.fallido",
            "callback": procesar_inventario_fallido
        }
    ]
    
    iniciar_multiples_consumidores(mis_colas)