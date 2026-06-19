""" Script para poblar las bases de datos de inventario de manera masiva utilizando 
la API del Módulo Administrador """

import urllib.request # Es una librería nativa de Python que sirve para abrir URLs y hacer peticiones HTTP
import json
import random
import string

# La URL de tu microservicio administrador dentro de la red de Docker
ADMIN_URL = "http://modulo_admin:5005/admin/agregar_stock"

REGIONES = ['LATAM', 'US', 'EU', 'ASIA']

JUEGOS = [
    'splatoon-3-ext', 'splatoon-3', 'mario-odyssey', 
    'zelda-totk', 'mario-kart-8', 'gow-ragnarok', 
    'spiderman-2', 'tlou-part1', 'elden-ring-ps5'
]

def generar_codigo_aleatorio(prefijo):
    """Genera un código serial estilo: LATAM-A1B2-C3D4"""
    parte1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    parte2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefijo}-{parte1}-{parte2}"

def inyectar_via_admin(juego, region, cantidad):
    """Empaqueta los códigos y se los envía al Módulo Administrador"""
    codigos_nuevos = [generar_codigo_aleatorio(region) for _ in range(cantidad)]
    
    payload = {
        "juego_id": juego,
        "region": region,
        "codigos": codigos_nuevos
    }
    
    # Preparamos la petición POST
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(ADMIN_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        # Disparamos la petición hacia el Módulo Admin
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                print(f"  [v] Éxito: {cantidad} códigos inyectados para {juego} en {region}.")
            else:
                print(f"  [!] Advertencia con {juego} en {region}. Código: {response.status}")
                
    except Exception as e:
        print(f"  [X] Error enviando a {region} para {juego}. ¿Está el módulo admin encendido? Error: {e}")

if __name__ == '__main__':
    print("=== INICIANDO LLENADO MASIVO VÍA API ADMIN ===")
    
    STOCK_POR_JUEGO = 10 
    
    for region in REGIONES:
        print(f"\n[*] Procesando región: {region}")
        for juego in JUEGOS:
            inyectar_via_admin(juego, region, STOCK_POR_JUEGO)
            
    print("\n=== PROCESO FINALIZADO ===")