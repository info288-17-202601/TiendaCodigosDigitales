# SistemaDistribuido_VentaCodigos
Un sistema distribuido para la venta de codigos de videojuegos que pueden estar bloqueados por pais. Haciendo uso de arquitectura EDA (Event Driven Arquitecture) para asegurar un comportamiento asincrono confiable y resiliente ante momentos de estres o caidas

## Servicios
## Microservicios de negocio
### Ventas
Se ubica en backend/mod_ventas.
Sus tareas incluyen:
* Manejo del carrito de compras: Escucha al frontend para añadir o quitar elementos al carrito de compras de un usuario, actualizando el estimado total a pagar. Ademas de actualizar el carrito si ocurre un error y ya no hay stock de un producto, o vaciarlo si se completa una compra
* Creacion de ordenes de compra: Escucha al frontend por peticiones de checkout y publica eventos de orden creada
* Manejo de la base de datos de ordenes: Maneja la base de datos con historial de ordenes, acutalizando ademas el estado de estas si estan pendientes, rechazadas, o completadas

### Inventario
Se ubica en backend/mod_inventario
Su principal trabajo consiste en el manejo de todo lo que tiene que ver con bases de datos de inventario, que contienes las claves digitales, espera por eventos de orden creada y se asegura que el stock este disponible para reservarlo o publica que esta agotado, tambien recibe peticiones del frontend para obtener el stock exacto de un juego y mantiene al modulo de busquedas actualizado sobre si hay stock o no de un juego a travez de eventos

### Pagos 
Se ubica en backend/mod_pago
Su Trabajo consiste en procesar los pagos de ordenes donde ya se ha reservado el stock, ademas de manejar carteras de usuarios. Este modulo publica eventos de ordenes procesadas que pueden ser rechazadas o aceptadas

### Busqueda
Se ubica en backeend/mod_busqueda
Su trabajo consiste en recibir peticiones de busqueda del frontend, buscar en la base de datos de catalogo, y devolver resultados

### Notificaciones
Se ubica en backend/mod_notificaiones
Su trabajo consiste en el envio de mensajes al usuario, puede ser por fallos de ordenes por stock, rechazo, o el envio de las claves digitales en el caso exitoso

## Servicios de Infraestructura
Para soportar la arquitectura asíncrona y el almacenamiento, el sistema se apoya en los siguientes servicios clave:

* **RabbitMQ (Message Broker):** Actua como el enrutador central que recibe y distribuye los mensajes de forma asincrona entre los distintos microservicios, garantizando que ningún mensaje se pierda si un servicio se cae.
* **Redis (Cache en Memoria):** Utilizado para almacenamiento de datos temporales como la sesion del usuario y los carritos de compra.
* **PostgreSQL:** Motor de base de datos relacional del sistema. Cada microservicio (Ventas, Inventario, Pagos) maneja su propia base de datos dentro de Postgres para mantener el bajo acoplamiento y la independencia de los datos.
* **Apache Solr:** Motor de búsqueda de alto rendimiento. Trabaja en conjunto con el módulo de Búsqueda para indexar el catálogo de juegos y ofrecer respuestas rápidas y precisas a las consultas de los usuarios en el frontend.

## Puertos y Accesos
Para facilitar el desarrollo, el consumo de APIs y la administración, los contenedores exponen los siguientes puertos hacia la máquina host (`localhost`):

### Frontend y Enrutamiento
* **`80`** - Nginx Router (Reverse Proxy / API Gateway)
* **`3000`** - Interfaz de Usuario Frontend (React)

### APIs de Microservicios (Backend)
* **`5001`** - API Módulo de Ventas
* **`5002`** - API Módulo de Búsqueda
* **`5003`** - API Módulo de Pagos
* **`5005`** - API Módulo de Administración
* **`5010`** - API Módulo de Inventario

### Infraestructura y Bases de Datos
* **`5432`** - PostgreSQL (Base de datos relacional)
* **`6379`** - Redis (Caché y gestión de estado/carritos)
* **`8983`** - Apache Solr (Motor de indexación y búsqueda)
* **`5672`** - RabbitMQ (Puerto de comunicación interna AMQP)
* **`15672`** - RabbitMQ Management (Dashboard Web UI para monitorear colas y exchanges)

# Cómo levantar el proyecto (Entorno Distribuido)
Antes que nada, se puede levantar todo de forma unificada con 
```bash
docker-compose -f docker-compose.yml up --build
```

El sistema está diseñado para que cada módulo pueda levantarse de forma independiente. Para que los contenedores puedan comunicarse entre diferentes archivos `docker-compose`, utilizamos una red externa de Docker.

## Paso 1: Crear la red compartida
Antes de levantar cualquier contenedor, debes crear la red puente (esto se hace una única vez en tu máquina):
```bash
docker network create red_tienda
```

## Paso 2: Levantar infraestructura
```bash
docker-compose -f docker-compose.infra.yml up -d
```
## Paso 3: Levantar servicios
```bash
docker-compose -f docker-compose.ventas.yml up -d
docker-compose -f docker-compose.inventario.yml up -d
docker-compose -f docker-compose.pagos.yml up -d
docker-compose -f docker-compose.busqueda_admin.yml up -d
docker-compose -f docker-compose.notificaciones.yml up -d
```
## Paso 4: Levantar frontend y enrutador
```bash
docker-compose -f docker-compose.frontend.yml up -d
```

# Gestion de respaldos
el proyecto cuenta con un script de de administracion de respaldos de las bases de datos en backend/backup_manager.py.
Este se puede ejecutar desde el host mientras docker este corriendo y el contenedor de la base de datos este levantado.
Se puede ejecutar como 
```bash
python3 backend/backup_manager.py 
```
Para que haga respaldos de todas las bases de datos del sistema en el equipo
Tambien se puede ejecutar selectivamente como
```bash
python3 backend/backup_manager.py {nombre_bd}
```
dnode las opciones validas son: 
db_usuarios, db_catalogo, db_ventas, db_perfil, db_inv_latam, db_inv_eu, db_inv_us, db_inv_asia

# Variables de Entorno

El sistema utiliza variables de entorno para configurar las conexiones y el comportamiento de los microservicios de forma dinámica, evitando quemar credenciales en el código fuente.

## Bases de Datos (PostgreSQL)
| Variable | Módulo / Servicio | Descripción |
| :--- | :--- | :--- |
| `POSTGRES_USER` | `db_main`, Todas las APIs | Usuario administrador de la base de datos relacional. |
| `POSTGRES_PASSWORD` | `db_main`, Todas las APIs | Contraseña del usuario administrador de Postgres. |
| `POSTGRES_DB` | `db_main`, Todas las APIs | Nombre de la base de datos principal a crear/utilizar (ej. `tienda_db`). |
| `DB_HOST` | Todas las APIs y Workers | Nombre del host o contenedor de PostgreSQL al que los microservicios deben conectarse. |
| `MAX_DB_POOL_CONNS` | APIs y Workers (Ventas/Inv) | Límite máximo de conexiones concurrentes en la piscina de conexiones (Pool) hacia Postgres. |

## Message Broker (RabbitMQ)
| Variable | Módulo / Servicio | Descripción |
| :--- | :--- | :--- |
| `RABBITMQ_DEFAULT_USER` | `message_broker` | Usuario por defecto que RabbitMQ crea al inicializarse. |
| `RABBITMQ_DEFAULT_PASS` | `message_broker` | Contraseña por defecto para la consola de administración y conexiones AMQP. |
| `RABBITMQ_HOST` | Todas las APIs y Workers | Nombre del host o contenedor de RabbitMQ (ej. `message_broker` o `localhost`). |
| `RABBITMQ_USER` | Admin / Notificaciones | Usuario utilizado por los scripts de Python para autenticarse contra el broker. |
| `RABBITMQ_PASS` | Admin / Notificaciones | Contraseña utilizada por los scripts de Python para conectarse a RabbitMQ. |

## Caché y Sesiones (Redis)
| Variable | Módulo / Servicio | Descripción |
| :--- | :--- | :--- |
| `REDIS_HOST` | APIs y Workers (Ventas/Inv/Pagos)| Nombre del host o contenedor de Redis al que los microservicios envían datos temporales (ej. Carritos). |
| `USER_SESSION_EXPIRATION_TIME` | APIs y Workers | Tiempo en segundos que un carrito de compras o sesión permanece vivo en memoria antes de ser destruido (ej. `3600` para 1 hora). |
| `MAX_CACHE_POOL_CONNS` | APIs y Workers | Límite de conexiones simultáneas que el microservicio puede abrir hacia Redis. |

## Frontend (React)
| Variable | Módulo / Servicio | Descripción |
| :--- | :--- | :--- |
| `PORT` | `react_frontend` | Puerto interno en el que el servidor de desarrollo de Node.js escucha las peticiones. |
| `CHOKIDAR_USEPOLLING` | `react_frontend` | Si está en `true`, fuerza a React a hacer polling de archivos. Vital para que el "Hot Reloading" funcione correctamente en Docker (Windows/Mac). |
| `WDS_SOCKET_PORT` | `react_frontend` | Puerto utilizado por el Webpack Dev Server para inyectar actualizaciones en vivo al navegador web (`0` para usar el puerto actual). |