# Para conectarse a los shards
from shared.database import get_inventory_db_name, get_connection, release_connection

def reservar_codigo_seguro(id_juego, region, id_orden_compra):
    """
    Busca un codigo disponible en el shard correspondiente,
    lo bloquea transaccionalmente y lo marca como reservado.
    
    Retorna un diccionario con el codigo si tiene exito, o None si no hay stock.
    """
    # Obtener la base de datos correcta según la región
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
        # Pasamos las variables como tupla (%s) para evitar inyección SQL
        cur.execute(query_bloqueo, (id_juego,))
        clave_encontrada = cur.fetchone()
        
        # Validar stock
        if not clave_encontrada:
            # No hay codigos disponibles o todos están bloqueados en este milisegundo
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
        
        # Confirmar la transacción de forma permanente
        conn.commit()
        cur.close()
        
        print(f"[Inventario] Código {codigo_serial} reservado para orden {id_orden_compra} en {db_name}.")
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
    Función de compensación (Rollback).
    Devuelve un código específico a estado 'DISPONIBLE' si la orden falla.
    """
    db_name = get_inventory_db_name(region)
    conn = None
    try:
        conn = get_connection(db_name)
        cur = conn.cursor()
        
        query_rollback = """
            UPDATE clave_digital 
            SET estado = 'DISPONIBLE', id_orden_compra = NULL 
            WHERE id_clave = %s;
        """
        cur.execute(query_rollback, (id_clave,))
        conn.commit()
        cur.close()
        print(f"[Inventario] Código {id_clave} liberado por compensación en {db_name}.")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[!] Error transaccional al liberar código: {e}")
    finally:
        if conn:
            release_connection(db_name, conn)


