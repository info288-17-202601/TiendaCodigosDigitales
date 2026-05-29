import json
import time
from shared.messaging import iniciar_consumidor, publicar_evento
from mod_inventario.service import reservar_codigo_seguro, liberar_codigo_seguro

def procesar_orden_creada(ch, method, properties, body):
    """
    Callback que procesa multiples items con esquema "Todo o Nada".
    """
    try:
        datos_orden = json.loads(body)
        id_orden_compra = datos_orden.get('id_orden_compra') 
        usuario_id = datos_orden.get('usuario_id')
        usuario_email = datos_orden.get("email")
        region = datos_orden.get('region', 'LATAM')
        items = datos_orden.get('items', [])
        total_estimado = datos_orden.get('total_estimado')
        
        if not items:
            print(f"[Inventario] Orden {id_orden_compra} rechazada: Carrito vacio.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        print(f"[*] Procesando orden {id_orden_compra} con {len(items)} items | Region: {region}")

        reservas_exitosas = []

        # Iterar sobre todos los elementos del carrito
        for item in items:
            juego_id = item.get('juego_id')
            resultado_reserva = reservar_codigo_seguro(juego_id, region, id_orden_compra)

            if resultado_reserva:
                # Almacenar la reserva exitosa añadiendo el juego_id para el payload final
                resultado_reserva['juego_id'] = juego_id
                reservas_exitosas.append(resultado_reserva)
            else:
                # COMPENSACION: Revertir todas las reservas anteriores de esta orden.
                print(f"[Inventario] Fallo al reservar '{juego_id}'. Iniciando rollback de compensacion...")
                for reserva in reservas_exitosas:
                    liberar_codigo_seguro(reserva['id_clave'], region)
                print(f"[Inventario] Rollback completo")        
        
                
                # Emitir evento de fallo total
                evento_fallo = {
                    "id_orden_compra": id_orden_compra,
                    "usuario_id": usuario_id,
                    "usuario_email": usuario_email,
                    "motivo": f"OUT_OF_STOCK_{juego_id}"
                }
                publicar_evento('inventario.fallido', evento_fallo)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return # Detener el procesamiento de esta orden

        # Si el bucle termina sin retornos, todos los items fueron reservados con exito
        evento_exito = {
            "id_orden_compra": id_orden_compra,
            "usuario_id": usuario_id,
            "usuario_email": usuario_email,
            "claves_reservadas": reservas_exitosas, # Ahora enviamos una lista completa
            "estado": "RESERVADO",
            "total_estimado": total_estimado
        }
        publicar_evento('inventario.reservado', evento_exito)
        print(f"[Inventario] exito total. Evento 'inventario.reservado' publicado.")

        # Confirmacion Critica
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[!] Error inesperado en consumidor de inventario: {e}")

if __name__ == '__main__':
    print("Iniciando Consumidor del Modulo de Inventario...")
    time.sleep(2) 
    iniciar_consumidor('orden.creada', procesar_orden_creada)