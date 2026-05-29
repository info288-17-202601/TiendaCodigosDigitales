import os
import json
import pika

# ENV
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "adminpassword")

# Establece y retorna una conexion con RabbitMQ
def get_rabbitmq_connection():
    """Establece y retorna una conexion con RabbitMQ"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    return pika.BlockingConnection(parameters)

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
        
        # Publicar mensaje en la cola
        canal.basic_publish(
            exchange='',
            routing_key=cola,
            body=json.dumps(payload),
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
        canal.basic_consume(queue=cola, on_message_callback=callback, auto_ack=False)

        print(f"Consumidor iniciado. Escuchando la cola '{cola}'...")
        canal.start_consuming()
    except Exception as e:
        print(f"Error en consumidor RabbitMQ: {e}")


