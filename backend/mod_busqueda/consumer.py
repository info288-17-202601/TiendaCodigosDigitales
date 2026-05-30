import json
import sys
import os

# Raíz del backend al path para poder importar shared
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.messaging import iniciar_consumidor

def callback_busqueda(ch, method, properties, body):
    # Esta función se dispara cuando llega un evento
    mensaje = json.loads(body.decode())
    print(f" [x] Búsqueda recibió evento: {mensaje}", flush=True)
    # IMPORTANTE: La función de tu equipo requiere confirmación manual (auto_ack=False)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_escucha_busqueda():
    # Usamos la función compartida para escuchar una cola de prueba
    iniciar_consumidor('eventos_busqueda', callback_busqueda)

if __name__ == '__main__':
    iniciar_escucha_busqueda()