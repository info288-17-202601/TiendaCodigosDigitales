# SistemaDistribuido_VentaCodigos
Un sistema distribuido para la venta de codigos de videojuegos que pueden estar bloqueados por pais. Haciendo uso de arquitectura EDA (Event Driven Arquitecture) para asegurar un comportamiento asincrono confiable y resiliente ante momentos de estres o caidas

# Estado actual
## Simluacion de multiples contenedores
Para esta version, con tal de probar de forma facil el diseño en un solo computador con recursos limitados, se tiene toda la logica del backend en un solo contenedor docker en vez de uno por cada modulo definido en la arquitectura. 
A pesar de lo anterior, se hace una distincion entre cada modulo por carpetas, con la excepcion de algunos archivos compartidos por utilidades:
* backend/shared/database.py es un hibrido entre servicio y simple utilidad, es un gestor de recursos, es decir una libreria importable que no corre en segundo plano, ni escucha puertos, pero que trabaja con estado, guardando conexiones en la memoria RAM del proceso que lo importo, y administrando su ciclo de vida
* backend/shared/cache.py crea una conexion con el contenedor de redis y maneja envolver y desenvolver los datos de este para trabajar con sesiones de usuario y carros de compra
* backend/sharaed/message.py crea conexiones con rabbitMQ para que se puedan crear consumidores que escuchan en una cierta cola y actuen con un callback especifico

## Modulos
### Inventario
Se ubica en backend/mod_inventario

Su objetivo principal es buscar un codigo digital en alguno de los shards de codigos por region y trabajar sobre su estado para ver disponibilidad, resevar(bloquear), liberar, o dejar como vendido.

Su archivo principal es consumer.py, que define un callback con la logica de su servicio y utiliza utilidades de messaging.py para abrir un consumidor de rabbitMQ. 

Debido al uso de rabbitMQ y la clausula SKIP LOCKED en sus consultas sql este modulo esta hecho para ser levantado multiples veces de ser necesario.

Actualmente tiene implementado un consumidor de colas rabbitMQ para su interaccion con el modulo de ventas, falta implementar interaccion con modulo de pagos para cambiar de reservado a vendido