# Espera compras

import json
from mod_pago.service import procesar_pago
from shared.messaging import publicar_evento_exchange

# Procesamiento de compra de los productos
def verificar_compra(ch, method, properties, body):
    try:
        datos_orden = json.loads(body)
        id_orden_compra = datos_orden.get('id_orden_compra') 
        total_estimado = datos_orden.get('monto_a_cobrar')
        usuario_id = datos_orden.get('usuario_id')
        usuario_email = datos_orden.get('usuario_email')
        metodo_pago = datos_orden.get('metodo_pago')
        region = datos_orden.get('region')
        
        #Saca el token

        payload = procesar_pago(total_estimado,usuario_id,usuario_email,id_orden_compra,region,metodo_pago,None)
        
        publicar_evento_exchange('pago.procesado',payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[!] Error inesperado en consumidor de Pago: {e}")

if __name__ == "__main__":
    from shared.messaging import iniciar_consumidor
    iniciar_consumidor('inventario.reservado', verificar_compra)