Esta sección detalla cómo segmentar e instalar la topología de la tienda utilizando multiples equipos físicos conectados a la misma red local (LAN), optimizando el uso de recursos hardware según el estado de los componentes. 
Para esta guia se usara como ejemplo 3 equipos

### PC1: 
Contiene la infraestructura de componentes que estan mas cerca del usuario, la cercania ayuda a reducir la latencia:
* Frontend
* Nginx
* Ventas_api
* Inventario_api
* Busqueda_api

### PC2:
Contiene workers generales que son sin estado, es decir que no guardan variables:
* Ventas_worker
* Inventario_worker
* Notificaciones_worker
* Pago_worker
Estos componentes son aquellos que trabajan de forma asincrona, aqui es principalmente donde se levantarian copias de modulos como inventario_worker para manejar crecimiento horizontal.

### PC3:
Contiene los contenedores con estado, aquellos que manejan memoria:
* Postgres
* Redis
* RabbitMQ
* ApacheSolR

# Cambios necesarios de desarrollo en un solo equipo a multiples
Necesitamos cambiar variables de entorno que manejen direcciones a otros contenedores dentro de una red docker a las direcciones ip reales, pasamos de algo como 
```bash
- DB_HOST=db_main
- RABBITMQ_HOST=message_broker
- REDIS_HOST=redis_session
- RABBITMQ_HOST=rabbitmq_broker
```
A algo como
```bash
- DB_HOST=192.168.1.30        # IP de PC3
- RABBITMQ_HOST=192.168.1.30  # IP de PC3
- REDIS_HOST=192.168.1.30     # IP de PC3
- RABBITMQ_HOST=192.168.1.30  # IP de PC3
```

# Paso a paso
## Infraestructura
Para levantar el sistema, hay que tener en cuenta las dependencias entre contenedores, la principal es la infraestructura.
En el PC3 se debe ejecutar
```bash
docker-compose -f docker-compose.infra.yml up -d
```
Este levanta: 
* Postgres
* Redis
* RabbitMQ
* ApacheSolR

## Contenedores sin estado
Continuamos con microservicios asincronos en el PC2.
Dentro del mismo equipo podemos definir redes docker, por requerimiento de los docker-compose, y para escalabilidad futura y comunicacion rapida de ser necesaria
```bash
docker network create red_tienda
```
Luego levantamos los microservicios con docker compose
```bash
docker-compose -f docker-compose.ventas.yml up -d ventas_worker
docker-compose -f docker-compose.inventario.yml up -d inventario_worker
docker-compose -f docker-compose.pagos.yml up -d pago_worker
docker-compose -f docker-compose.notificaiones.yml up -d
```

## Capa mas cercana al cliente
Terminamos con el PC1 donde viven los contenedores mas cercanos al cliente.
Necesitamos asegurarnos que la variable de entorno de FRONTEND_URL apunte a la ip de este equipo.
Configuramos nginx, particularmente en este ejemplo se puede dejar como esta porque todas las api viven en PC1 y se pueden comunicar por la red docker, sin embargo, si movemos una api a otro equipo debemos hacer cambios del tipo:
```bash
location /api/pago/ {
    proxy_pass http://192.168.1.20:5003; 
}
```
Creamos la red docker como en PC2
```bash
docker network create red_tienda
```
Y levantamos los contenedores
```bash
docker-compose -f docker-compose.ventas.yml up -d ventas_api
docker-compose -f docker-compose.inventario.yml up -d inventario_api
docker-compose -f docker-compose.pagos.yml up -d pago_api
docker-compose -f docker-compose.busqueda.yml up -d search_api search_worker
docker-compose -f docker-compose.frontend.yml up -d
```




