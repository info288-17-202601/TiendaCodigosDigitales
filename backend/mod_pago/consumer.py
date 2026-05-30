# Espera compras

import json
from mod_pago.service import procesar_pago
from shared.messaging import publicar_evento

#Luego de verificar con el token
def procesar_compra(ch, method, properties, body):
    try:
        datos_orden = json.loads(body)
        id_orden_compra = datos_orden.get('id_orden_compra') 
        total_estimado = datos_orden.get('total_estimado')
        usuario_id = datos_orden.get('usuario_id')
        usuario_email = datos_orden.get('usuario_email')
        
        #usa el token

        payload, estado = procesar_pago(total_estimado,usuario_id,usuario_email,id_orden_compra)
        
        publicar_evento(f'pago.{estado}',payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[!] Error inesperado en consumidor de Pago: {e}")

# Sale al presionar comprar
def verificar_compra(ch, method, properties, body):
    try:
        datos_orden = json.loads(body)
        id_orden_compra = datos_orden.get('id_orden_compra') 
        total_estimado = datos_orden.get('total_estimado')
        usuario_id = datos_orden.get('usuario_id')
        usuario_email = datos_orden.get('usuario_email')
        
        #Saca el token

        payload, estado = procesar_pago(total_estimado,usuario_id,usuario_email,id_orden_compra)
        
        publicar_evento(f'pago.{estado}',payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error inesperado en consumidor de Pago: {e}")