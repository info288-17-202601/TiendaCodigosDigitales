import json
import time

from shared.messaging import iniciar_multiples_consumidores
from mod_notificaciones.service import (
    enviar_notificacion_compra, 
    enviar_notificacion, 
    armar_mensaje_generico
)

def procesar_evento_pago(ch, method, properties, body):
    try:
        datos = json.loads(body)
        id_orden_compra = datos.get('id_orden_compra')
        usuario_id = datos.get('id_usuario') or datos.get('usuario_id')
        email = datos.get('usuario_email') or f"{usuario_id}@usuario.local" # Fallback si no viene email
        estado_pago = datos.get('estado_pago')
        motivo = datos.get('motivo')

        # Solo actuamos en el caso de pago NO APROBADO para notificar la falla
        if estado_pago == "NO APROBADO":
            print(f"[Notificaciones] Pago rechazado para orden {id_orden_compra}. Enviando aviso a {email}...")
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

def procesar_orden_completada(ch, method, properties, body):
    try:
        datos = json.loads(body)
        id_orden_compra = datos.get('id_orden_compra')
        email = datos.get('usuario_email')
        items_raw = datos.get('items')

        codigos = []
        juegos_ids = []

        if isinstance(items_raw, list):
            for item in items_raw:
                if isinstance(item, dict):
                    c = item.get('codigo_serial')
                    j = item.get('juego_id')
                    if c:
                        codigos.append(c)
                    if j:
                        juegos_ids.append(j)
        elif isinstance(items_raw, dict):
            c = items_raw.get('codigo_serial')
            j = items_raw.get('juego_id')
            if c:
                codigos.append(c)
            if j:
                juegos_ids.append(j)

        if codigos:
            juegos_unicos = list(set(juegos_ids))
            juegos_str = ", ".join(juegos_unicos) if juegos_unicos else "Varios"
            
            print(f"[Notificaciones] Orden completada recibida para {id_orden_compra}. Enviando {len(codigos)} códigos a {email}...")
            enviar_notificacion_compra(email, id_orden_compra, juegos_str, codigos)
        else:
            print(f"[Notificaciones] ALERTA: Orden completada recibida pero no se encontraron códigos en el evento para orden {id_orden_compra}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error procesando orden completada en notificaciones: {e}")

def procesar_usuario_registrado(ch, method, properties, body):
    try:
        datos = json.loads(body)
        usuario = datos.get('usuario', 'Usuario')
        email = datos.get('email')

        if email:
            asunto = "¡Bienvenido a KittenZtore!"
            mensaje = f"Hola {usuario},\n\nTu cuenta ha sido creada con éxito. ¡Gracias por registrarte en nuestra plataforma!"
            cuerpo = armar_mensaje_generico(asunto, mensaje)
            print(f"[Notificaciones] Registro de usuario recibido para {usuario}. Enviando bienvenida a {email}...")
            enviar_notificacion(email, asunto, cuerpo)
        else:
            print("[Notificaciones] ALERTA: Registro recibido pero sin email del usuario.")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error procesando registro de usuario en notificaciones: {e}")

def procesar_recuperar_contrasena(ch, method, properties, body):
    try:
        datos = json.loads(body)
        usuario = datos.get('usuario', 'Usuario')
        email = datos.get('email')

        if email:
            asunto = "Recuperación de Contraseña"
            mensaje = f"Hola {usuario},\n\nHemos recibido una solicitud para restablecer tu contraseña. Si fuiste tú, sigue las instrucciones para recuperarla."
            cuerpo = armar_mensaje_generico(asunto, mensaje)
            print(f"[Notificaciones] Solicitud de recuperación de contraseña recibida para {usuario}. Enviando enlace a {email}...")
            enviar_notificacion(email, asunto, cuerpo)
        else:
            print("[Notificaciones] ALERTA: Recuperación recibida pero sin email del usuario.")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error procesando recuperación de contraseña en notificaciones: {e}")

if __name__ == '__main__':
    print("Iniciando Consumidor del Modulo de Notificaciones...")
    time.sleep(2)

    mis_colas = [
        {
            "cola": "cola_notificaciones_pagos",
            "exchange": "tienda_exchange",
            "routing_key": "pago.procesado",
            "callback": procesar_evento_pago
        },
        {
            "cola": "notificaciones_inventario.fallido",
            "exchange": "tienda_exchange",
            "routing_key": "inventario.fallido",
            "callback": procesar_inventario_fallido
        },
        {
            "cola": "inventario.orden_completada",
            "callback": procesar_orden_completada
        },
        {
            "cola": "usuario.registrado",
            "callback": procesar_usuario_registrado
        },
        {
            "cola": "usuario.olvidado",
            "callback": procesar_recuperar_contrasena
        }
    ]
    
    iniciar_multiples_consumidores(mis_colas)