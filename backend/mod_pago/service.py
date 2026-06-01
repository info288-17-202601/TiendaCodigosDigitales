import time
import json
from random import randint
from shared.messaging import iniciar_consumidor, publicar_evento_exchange

def iniciar_escucha():
    iniciar_consumidor('inventario.reservado', _callback_pago)

def _callback_pago(ch, method, properties, body):
    try:
        datos = json.loads(body)
        procesar_pago(
            monto=datos.get('total_estimado', 0),
            usuario=datos.get('usuario_id'),
            correo=datos.get('email'),
            id_orden_compra=datos.get('id_orden_compra'),
            region=datos.get('region'),
            metodo_pago=datos.get('metodo_pago'),
            token=datos.get('token', 'TOKEN_DEFAULT')
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[Pagos] Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def procesar_pago(monto: float, usuario: str, correo: str, id_orden_compra: str, region: str, metodo_pago: str, token: str):
    print(f"Realizando compra de {monto}\nUserID : {usuario}\nCorreo : {correo}")
    print(f"El metodo de {metodo_pago} fue aceptado. Token: {token}")
    print(f"El token taba bien :3")

    estado = "aprovado"
    time.sleep(5)
    chance = randint(1, 100)
    if chance <= 15:
        match (int)(chance / 5):
            case 0:
                estado = "rechazado"
            case 1:
                estado = "cancelado"
            case _:
                estado = "expirado"

    match estado:
        case "aprovado":
            payload = {
                "id_usuario": usuario,
                "usuario_email": correo,       # <-- agregado, notificaciones lo necesita
                "id_orden_compra": id_orden_compra,
                "estado_pago": "APROBADO",
                "motivo": "",
                "region": region,
                "id_transaccion_pasarela": "txn_987654321"
            }
        case "expirado":
            payload = {
                "id_usuario": usuario,
                "usuario_email": correo,       # <-- agregado
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO",
                "motivo": "Timed Out - El pago demoro en ser procesado",
                "region": region,
                "id_transaccion_pasarela": ""
            }
        case "cancelado":
            payload = {
                "id_usuario": usuario,
                "usuario_email": correo,       # <-- agregado
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO",
                "motivo": "Pago Cancelado / No procesado",
                "region": region,
                "id_transaccion_pasarela": ""
            }
        case "rechazado":
            payload = {
                "id_usuario": usuario,
                "usuario_email": correo,       # <-- agregado
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO",
                "motivo": "Tarjeta rechazada",
                "region": region,
                "id_transaccion_pasarela": ""
            }
        case _:
            return  # caso inválido, no publicar nada

    publicar_evento_exchange('pago.procesado', payload)
    print(f"[Pagos] Evento 'pago.procesado' publicado para orden {id_orden_compra} — Estado: {payload['estado_pago']}")

    return payload
