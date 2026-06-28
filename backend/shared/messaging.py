import os
import json
import pika
import time
from .security import _envolver_mensaje, envolver_callback

# ENV
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "adminpassword")

# Establece y retorna una conexion con RabbitMQ
def get_rabbitmq_connection(reintentos=12, espera=5):
    """Establece y retorna una conexion con RabbitMQ"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    for intento in range(reintentos):
        try:
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            print(f"[Messaging] RabbitMQ no está listo. Reintentando en {espera}s... (Intento {intento + 1}/{reintentos})")
            time.sleep(espera)
            
    # Si falla después de 5 intentos, lanzamos el error real
    raise Exception("No se pudo conectar a RabbitMQ después de varios intentos. ¿Está prendido el contenedor?")
    

# ----- Normal ------

# Convierte un diccionario a JSON
# y lo publica en la cola especificada
def publicar_evento(cola, payload):
    """
    Convierte un diccionario a JSON
    y lo publica en la cola especificada
    """
    try:
        # Crear conexion con RabbitMQ
        conexion = get_rabbitmq_connection()

        # Abrir un canal de comunicacion
        canal = conexion.channel()
    
        # durable=True asegura que la cola
        # sobreviva reinicios del broker
        canal.queue_declare(queue=cola, durable=True)
        
        # Envolver y firmar
        mensaje = _envolver_mensaje(cola,payload)

        # Publicar mensaje en la cola
        canal.basic_publish(
            exchange='',
            routing_key=cola,
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,  # delivery_mode=2 hace que el mensaje sea persistente en disco
            )
        )

        # Cerrar conexion
        conexion.close()

    except Exception as e:
        print(f"[Messaging] Error publicando evento en RabbitMQ: {e}")


# Mantiene una conexion abierta escuchando mensajes de una cola
# Ejecuta el callback especificado cada vez que llega un mensaje
def iniciar_consumidor(cola, callback):
    """Mantiene una conexion abierta escuchando mensajes de una cola"""
    """Ejecuta el callback especificado cada vez que llega un mensaje"""
    try:
        # Crear conexion con RabbitMQ
        conexion = get_rabbitmq_connection()

        # Abrir canal de comunicacion
        canal = conexion.channel()
        
        # durable=True asegura que la cola
        # sobreviva reinicios del broker
        canal.queue_declare(queue=cola, durable=True)

        # prefetch_count=1 obliga a RabbitMQ
        # a no enviar otro mensaje a este consumidor
        # hasta que el anterior haya sido procesado
        # y confirmado con ACK
        canal.basic_qos(prefetch_count=1)
        
        # auto_ack=False requiere confirmacion manual
        # del mensaje procesado
        canal.basic_consume(queue=cola, on_message_callback=envolver_callback(callback), auto_ack=False)

        print(f"Consumidor iniciado. Escuchando la cola '{cola}'...")
        canal.start_consuming()
    except Exception as e:
        print(f"Error en consumidor RabbitMQ: {e}")


# ----- Exchange -----

def publicar_evento_exchange(routing_key, payload):
    try:
        conexion = get_rabbitmq_connection()
        canal = conexion.channel()
        canal.exchange_declare(exchange='tienda_exchange', exchange_type='direct', durable=True)
        
        mensaje = _envolver_mensaje(routing_key,payload)
        
        canal.basic_publish(
            exchange='tienda_exchange',
            routing_key=routing_key,
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conexion.close()
    except Exception as e:
        print(f"Error: {e}")

def iniciar_consumidor_exchange(nombre_cola, routing_key, callback):
    try:
        conexion = get_rabbitmq_connection()
        canal = conexion.channel()
        canal.exchange_declare(exchange='tienda_exchange', exchange_type='direct', durable=True)
        canal.queue_declare(queue=nombre_cola, durable=True)
        canal.queue_bind(exchange='tienda_exchange', queue=nombre_cola, routing_key=routing_key)
        canal.basic_qos(prefetch_count=1)
        canal.basic_consume(queue=nombre_cola, on_message_callback=envolver_callback(callback), auto_ack=False)
        canal.start_consuming()
    except Exception as e:
        print(f"Error: {e}")


# ----- Para multiples consumidores -----

def iniciar_multiples_consumidores(configuraciones):
    """
    Inicia un solo worker que escucha multiples colas.
    Soporta colas directas tradicionales y colas enlazadas a Exchanges.
    """
    try:
        conexion = get_rabbitmq_connection()
        canal = conexion.channel()
        canal.basic_qos(prefetch_count=1)

        # Iterar sobre la lista para registrar cada oyente
        for config in configuraciones:
            nombre_cola = config["cola"]
            cb = config["callback"]

            # Siempre declaramos la cola 
            canal.queue_declare(queue=nombre_cola, durable=True)

            # Si tiene configuracion de exchange hacemos el bind
            if "exchange" in config and "routing_key" in config:
                # Aseguramos que el exchange exista
                canal.exchange_declare(exchange=config["exchange"], exchange_type='direct', durable=True)
                # Enlazamos la cola al exchange
                canal.queue_bind(exchange=config["exchange"], queue=nombre_cola, routing_key=config["routing_key"])
                print(f"[*] Registrado oyente en cola '{nombre_cola}' (via Exchange '{config['exchange']}')")
            
            # Caso cola clasica no hace mas cambios
            else:
                print(f"[*] Registrado oyente en cola directa '{nombre_cola}'")

            # Le decimos al canal que empiece a escuchar este buzon
            canal.basic_consume(queue=nombre_cola, on_message_callback=envolver_callback(cb), auto_ack=False)
            
        print("[*] Worker iniciado y bloqueado. Escuchando multiples colas...")
        
        # Bloquear el script al final
        canal.start_consuming()
        
    except Exception as e:
        print(f"Error iniciando multiples consumidores: {e}")