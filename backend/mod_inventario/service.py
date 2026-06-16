import json
# Para conectarse a los shards
from shared.database import get_inventory_db_name, get_connection, release_connection
from shared.messaging import publicar_evento


def reservar_codigo_seguro(id_juego, region, id_orden_compra):
    """
    Busca un codigo disponible en el shard correspondiente,
    lo bloquea transaccionalmente y lo marca como reservado.
    
    Retorna un diccionario con el codigo si tiene exito, o None si no hay stock.
    """
    # Obtener la base de datos correcta segun la region
    db_name = get_inventory_db_name(region)
    conn = None
    
    try:
        # Obtener conexion del pool
        conn = get_connection(db_name)
        cur = conn.cursor()

        # Iniciar la transaccion de bloqueo (FOR UPDATE SKIP LOCKED)
        query_bloqueo = """
            SELECT id_clave, codigo_serial 
            FROM clave_digital 
            WHERE id_juego = %s AND estado = 'DISPONIBLE' 
            LIMIT 1 
            FOR UPDATE SKIP LOCKED;
        """
        # Pasamos las variables como tupla (%s) para evitar inyeccion SQL
        cur.execute(query_bloqueo, (id_juego,))
        clave_encontrada = cur.fetchone()

        # Validar stock
        if not clave_encontrada:
            # No hay codigos disponibles o todos estan bloqueados en este milisegundo
            conn.rollback()
            cur.close()
            return None
        
            
        id_clave = clave_encontrada['id_clave']
        codigo_serial = clave_encontrada['codigo_serial']
        
        # Ejecutar la actualizacion en la fila bloqueada
        query_actualizacion = """
            UPDATE clave_digital 
            SET estado = 'RESERVADO', id_orden_compra = %s 
            WHERE id_clave = %s;
        """
        cur.execute(query_actualizacion, (id_orden_compra, id_clave))

        # Contar el stock restante
        query_stock = """
            SELECT COUNT(id_clave) as stock_restante
            FROM clave_digital 
            WHERE id_juego = %s AND estado = 'DISPONIBLE';
        """
        cur.execute(query_stock, (id_juego,))
        resultado_stock = cur.fetchone()

        stock_restante = resultado_stock['stock_restante'] if isinstance(resultado_stock, dict) else resultado_stock[0]
        
        # Confirmar la transaccion de forma permanente
        conn.commit()
        cur.close()
        
        print(f"[Inventario] Codigo {codigo_serial} reservado para orden {id_orden_compra} en {db_name}.")

        # Publicar evento a RabbitMQ sobre stock agotado
        if stock_restante == 0:
            payload = {
                "juego_id": id_juego,
                "region": region,
                "motivo": "AGOTADO"
            }
            publicar_evento('inventario.cambio_stock', payload)
            print(f"[Inventario] Evento emitido: {id_juego} agotado en la region {region}.")

        # Dar clave encontrada
        return clave_encontrada

    except Exception as e:
        # Si algo falla deshacemos los cambios
        if conn:
            conn.rollback()
        print(f"[!] Error transaccional en inventario: {e}")
        return None
        
    finally:
        # Devolver la conexion a la piscina
        if conn:
            release_connection(db_name, conn)

def liberar_codigo_seguro(id_clave, region):
    """
    Funcion de compensacion (Rollback).
    Devuelve un codigo especifico a estado 'DISPONIBLE' si la orden falla.
    y avisa al Modulo de Busqueda que volvio a haber stock.
    """
    db_name = get_inventory_db_name(region)
    conn = None
    try:
        conn = get_connection(db_name)
        cur = conn.cursor()
        
        query_rollback = """
            UPDATE clave_digital 
            SET estado = 'DISPONIBLE', id_orden_compra = NULL 
            WHERE id_clave = %s
            RETURNING id_juego;
        """
        cur.execute(query_rollback, (id_clave,))
        resultado = cur.fetchone()
        conn.commit()
        cur.close()
        print(f"[Inventario] Codigo {id_clave} liberado por compensacion en {db_name}.")

        # Si se actualizo correctamente, avisamos a busquedas que hay stock
        if resultado:
            id_juego = resultado['id_juego'] if isinstance(resultado, dict) else resultado[0]
            
            payload_restaurado = {
                "juego_id": id_juego,
                "region": region,
                "motivo": "DISPONIBLE"
            }
            # Emitimos el evento de que el juego vuelve a estar disponible
            publicar_evento('inventario.cambio_stock', payload_restaurado)
            print(f"[Inventario] Evento emitido: {id_juego} vuelve a estar DISPONIBLE en {region}.")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[!] Error transaccional al liberar codigo: {e}")
    finally:
        if conn:
            release_connection(db_name, conn)

