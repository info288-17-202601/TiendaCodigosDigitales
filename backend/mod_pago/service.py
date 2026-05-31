# Procesa las compras
import time
from random import randint
from shared.messaging import iniciar_consumidor

# Funcion para poder ver los mensajes
def iniciar_escucha():
    iniciar_consumidor('orden.creada',procesar_pago)


# Procesamiento de la compra de manera artificial
def procesar_pago(monto:float, usuario:str, correo:str,id_orden_compra:str,token:str):
    print(f"Realizando compra de {monto}\nUserID : {usuario}\nCorreo : {correo}")

    print(f"El token taba bien :3")

    # Realmente no vamos a usar mucho esto
    estado = "aprovado"
    time.sleep(5) # Puede cambiar segun logica frontend
    chance = randint(1,100)
    if chance <= 15:
        match (int)(chance/5) :
            case 0:
                estado = "rechazado"
            case 1:
                estado = "cancelado"
            case _:
                estado = "expirado"
    
    # "Logica Real"

    match estado:  
        case "aprovado":
            payload = {
                "id_orden_compra": id_orden_compra,
                "estado_pago": "APROBADO",
                "id_transaccion_pasarela": "txn_987654321"
            }
        case "expirado":
            payload = {
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO",
                "motivo": "Timed Out - El pago demoro en ser procesado"
            }
        case "cancelado":
            payload = {
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO", 
                "motivo": "Pago Cancelado / No procesado"
            }
        case "rechazado":
            payload = {
                "id_orden_compra": id_orden_compra,
                "estado_pago": "NO APROBADO",
                "motivo": "Tarjeta rechazada"
            }
        case _ :
            payload = {None}


    return payload