import json
import time

from shared.messaging import iniciar_consumidor
from mod_notificaciones.service import enviar_notificacion_compra


def procesar_orden_completada(ch, method, properties, body):
    try:
        datos = json.loads(body)
        id_orden_compra = datos.get('id_orden_compra')
        email = datos.get('email') or datos.get('usuario_email')
        juego_id = datos.get('juego_id')
        codigos_entregados = datos.get('codigos_entregados', [])

        if not email or not codigos_entregados:
            print(f"[Notificaciones] Orden {id_orden_compra} recibida sin datos suficientes para notificar.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        resultado = enviar_notificacion_compra(email, id_orden_compra, juego_id, codigos_entregados)
        print(f"[Notificaciones] Resultado del envio: {resultado['estado']} para {resultado['destinatario']}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[!] Error inesperado en notificaciones: {e}")


if __name__ == '__main__':
    print("Iniciando Consumidor del Modulo de Notificaciones...")
    time.sleep(2)
    iniciar_consumidor('orden.completada', procesar_orden_completada)