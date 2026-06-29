# Guía de despliegue

Este documento describe pasos para desplegar localmente y en entornos simples este proyecto de microservicios.

**Requisitos**
- Docker (>=20.x)
- Docker Compose (v2 recommended)
- Git
- Python 3.10+ para ejecutar scripts locales

**Estructura relevante**
- Servicios docker-compose: archivos `docker-compose*.yml` en la raíz.
- Backend: carpeta `backend/` (APIs, scripts y dependencias).
- Frontend: carpeta `frontend/`.
- Inicialización de Postgres: `postgres-init/init.sh`.
- Scripts de datos: `backend/poblar_shards.py` y `backend/genContraSegura.py`.

## 1) Preparar variables de entorno
Incluir el `.env` en la raíz del proyecto con las variables sensibles (DB_PASSWORD, RABBITMQ credentials, etc.).


## 2) Levantar la infraestructura (Postgres, RabbitMQ, Redis, Nginx)
Usar los archivos de compose que describen la infraestructura.

Primero, crear la red:
```bash
docker network create red_tienda
```
Comando:

```bash
docker-compose -f docker-compose.infra.yml up -d
```

Para ver logs:

```bash
docker-compose logs -f
```

Para detener:

```bash
docker-compose down
```

## 3) Construir y ejecutar microservicios
Hay docker-compose específicos por dominio; por ejemplo para ventas/inventario/búsqueda:

```bash
# Levantar módulos individuales (ejemplo: inventario)
docker-compose -f docker-compose.inventario.yml up -d --build

# O levanta todos los servicios definidos en el compose principal (Útil para etapa de desarrollo)
docker-compose up -d --build
```

Observa la salida de `docker ps` para confirmar contenedores en ejecución.

## 4) Inicializar la base de datos y poblar datos
El repo contiene `postgres-init/init.sh` que puede ejecutarse dentro del contenedor de Postgres al iniciar (composición puede manejarlo). Si necesitas ejecutarlo manualmente:

```bash
# Ejecutar el script de inicialización dentro del contenedor (ajusta nombre de contenedor)
docker cp postgres-init/init.sh <postgres_container>:/init.sh
docker exec -it <postgres_container> bash -c "bash /init.sh"
```

Para poblar shards desde el código del backend:

```bash
# Ejecutar localmente (requiere acceso a la DB)
python backend/poblar_shards.py

# O dentro del contenedor del backend
docker exec -it <backend_container> python /app/poblar_shards.py
```

## 5) Configuración y ejecución del frontend
Se provee `docker-compose.frontend.yml` y un `Dockerfile` en `frontend/`.

Ejemplo para construir y correr el frontend:

```bash
# desde la raíz
docker-compose -f docker-compose.frontend.yml up -d --build
```

La UI por defecto estará disponible en `http://localhost:3000` (o el puerto configurado).

## 6) Tareas comunes de administración
- Ver logs de un servicio: `docker-compose logs -f <service_name>`
- Acceder a un contenedor: `docker exec -it <container> bash`
- Reconstruir una imagen y reiniciar: `docker-compose up -d --build <service_name>`

## 7) Notas para producción
- Usar un archivo `.env` separado con credenciales seguras.
- Poner Nginx/Traefik delante para TLS y terminación HTTPS.
- Monitorizar logs y reinicios con una solución como Prometheus/Grafana o ELK.
- Considerar escalado horizontal de servicios estateless y replicación para la DB.

## 8) Resolución de problemas
- Contenedor no inicia: `docker logs <container>`.
- Problemas de conexión a RabbitMQ/Redis: revisar variables de entorno y que los servicios de infra estén corriendo.