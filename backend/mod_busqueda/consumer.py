""" consumer.py: Es el trabajador de fondo. Se encarga de escuchar los mensajes de RabbitMQ """

import json
import sys
import os
import pysolr

# Raíz del backend al path para poder importar shared
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.messaging import iniciar_consumidor

# 1. Configuramos la conexión a Solr (Igual que en service.py)
SOLR_URL = 'http://solr_engine:8983/solr/catalogo'
solr = pysolr.Solr(SOLR_URL, always_commit=True)

def callback_busqueda(ch, method, properties, body):
    try:
        # Decodificamos el mensaje
        mensaje = json.loads(body.decode())
        print(f" [x] Búsqueda recibió evento: {mensaje}", flush=True)

        evento_tipo = mensaje.get('evento')
        id_juego = mensaje.get('id_juego')
        stock_restante = mensaje.get('stock_restante')

        """ actualizar la base de datos de Solr cuando llegue un mensaje de venta. """
        # 2. Lógica para actualizar Solr
        if evento_tipo == 'venta_completada' and id_juego:
            print(f" [*] Actualizando stock de '{id_juego}' en Solr...", flush=True)
            
            # Buscamos si el juego ya existe en Solr
            resultados = solr.search(f'id:{id_juego}')
            
            if len(resultados) > 0:
                # Si existe, tomamos el documento actual
                juego_solr = resultados.docs[0]
                # Actualizamos el stock (o lo marcamos agotado)
                juego_solr['stock'] = stock_restante
                
                # Volvemos a guardar el documento en Solr (lo sobreescribe)
                solr.add([juego_solr])
                print(f" [v] Solr actualizado: {id_juego} ahora tiene stock {stock_restante}", flush=True)
            else:
                 print(f" [!] Advertencia: Juego {id_juego} no encontrado en Solr. No se pudo actualizar.", flush=True)

        # IMPORTANTE: Confirmación manual (auto_ack=False)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
         print(f" [X] Error procesando mensaje en Búsqueda: {e}", flush=True)
         # En un entorno real, aquí podríamos usar basic_nack() para rechazar el mensaje

def iniciar_escucha_busqueda():
    # Usamos la función compartida para escuchar una cola de prueba
    iniciar_consumidor('eventos_busqueda', callback_busqueda)

if __name__ == '__main__':
    iniciar_escucha_busqueda()