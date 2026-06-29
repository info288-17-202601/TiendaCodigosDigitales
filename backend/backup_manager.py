import os
import sys
import subprocess
from datetime import datetime

CONTAINER_NAME = "db_main"  # Asegúrate de que coincida con el nombre de tu contenedor de Postgres
BACKUP_DIR = "./backups"
ENV_FILE_PATH = "./.env"        # Ruta al archivo .env en la raíz de tu proyecto

def cargar_env_local(ruta_env):
    """
    Parsea manualmente el archivo .env e inyecta las variables 
    en os.environ si no están cargadas en el sistema.
    """
    if os.path.exists(ruta_env):
        with open(ruta_env, "r") as f:
            for linea in f:
                # Ignorar comentarios y líneas vacías
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                # Separar por el primer signo '='
                if "=" in linea:
                    clave, valor = linea.split("=", 1)
                    # Limpiar comillas si existen
                    valor = valor.strip().strip("'").strip('"')
                    os.environ[clave.strip()] = valor
        print("[Env] Archivo .env cargado dinámicamente.")
    else:
        print("[Advertencia] No se encontró el archivo .env local, se usarán las variables del sistema.")

# Ejecutar la carga del entorno antes de definir el mapa de respaldos
cargar_env_local(ENV_FILE_PATH)

# Mapeo estructurado leyendo directamente el entorno (Cultura de No Hardcoding)
CONFIG_RESPALDOS = {
    "db_usuarios": {
        "user": os.environ.get("DB_USER_USUARIOS"), 
        "pass": os.environ.get("DB_PASS_USUARIOS")
    },
    "db_catalogo": {
        "user": os.environ.get("DB_USER_CATALOGO"), 
        "pass": os.environ.get("DB_PASS_CATALOGO")
    },
    "db_ventas": {
        "user": os.environ.get("DB_USER_VENTAS"), 
        "pass": os.environ.get("DB_PASS_VENTAS")
    },
    "db_perfil": {
        "user": os.environ.get("DB_USER_PAGOS"), 
        "pass": os.environ.get("DB_PASS_PAGOS")
    },
    "db_inv_latam": {
        "user": os.environ.get("DB_USER_INVENTARIO"), 
        "pass": os.environ.get("DB_PASS_INVENTARIO")
    },
    "db_inv_eu": {
        "user": os.environ.get("DB_USER_INVENTARIO"), 
        "pass": os.environ.get("DB_PASS_INVENTARIO")
    },
    "db_inv_us": {
        "user": os.environ.get("DB_USER_INVENTARIO"), 
        "pass": os.environ.get("DB_PASS_INVENTARIO")
    },
    "db_inv_asia": {
        "user": os.environ.get("DB_USER_INVENTARIO"), 
        "pass": os.environ.get("DB_PASS_INVENTARIO")
    }
}

def ejecutar_pg_dump(db_name):
    """Ejecuta pg_dump dentro de Docker usando las variables extraídas del .env."""
    credenciales = CONFIG_RESPALDOS[db_name]
    usuario = credenciales["user"]
    contrasena = credenciales["pass"]

    if not usuario or not contrasena:
        print(f"  -> [!] Error: Credenciales faltantes en el entorno para {db_name}.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{db_name}_{fecha}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    print(f"[Backup] Respaldando: {db_name} a través del contenedor '{CONTAINER_NAME}'...")

    # Comando Docker Exec inyectando de forma segura la contraseña del entorno
    comando = [
        "docker", "exec",
        "-e", f"PGPASSWORD={contrasena}",
        CONTAINER_NAME,
        "pg_dump",
        "-U", usuario,
        "-d", db_name,
        "-F", "c"
    ]

    try:
        with open(filepath, "wb") as f_out:
            subprocess.run(comando, check=True, stdout=f_out, stderr=subprocess.PIPE)
        print(f"  -> [ÉXITO] Guardado localmente en: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"  -> [!] Error en {db_name}: {e.stderr.decode().strip()}")
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if len(sys.argv) > 1:
        db_solicitada = sys.argv[1]
        if db_solicitada in CONFIG_RESPALDOS:
            ejecutar_pg_dump(db_solicitada)
        else:
            print(f"[!] '{db_solicitada}' no es una base de datos válida.")
            sys.exit(1)
    else:
        print("[Backup] Iniciando respaldo total distribuido desde variables de entorno...")
        for db in CONFIG_RESPALDOS.keys():
            ejecutar_pg_dump(db)
        print("[Backup] ¡Proceso finalizado!")