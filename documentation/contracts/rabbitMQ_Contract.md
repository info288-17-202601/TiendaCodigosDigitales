## Evento: Orden creada
Nombre exacto en codigo: orden.creada

Publicador: Modulo de ventas.

consumidor: Modulo de inventario.

Cuando: El usuario presiona "Pagar".

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "email": "correo.ejemplo@gmail.com",
  "region": "LATAM",
  "items": [
    {"juego_id": "splatoon-3-ext", "cantidad": 1}
  ],
  "metodo_pago": "debito"
  "monto_a_cobrar": 19990
}

## Evento: inventario reservado
Nombre exacto en codigo: inventario.reservado

Publicador: Modulo de inventario.

Consumidor: Modulo de pagos.

Cuando: Hay stock de los productos que se desean comprar, cambia el estado de los productos a "RESERVADO" y les asigna el id_orden_compra de la orden

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "region": "LATAM",
  "usuario_email": "email.email@gmail.com", 
  "items": [
    {"juego_id": "splatoon-3-ext", "cantidad": 1}
  ],
  "metodo_pago": "Debito",
  "estado_reserva": "EXITO",
  "monto_a_cobrar": 19990
}
 
### Evento alternativo: no hay stock
Nombre exacto en codigo: inventario.fallido

Publicador: Modulo de inventario.

Consumidores: Modulo de ventas - Modulo de notificaciones.

Cuando: Un producto en la lista de productos a comprar no tenia stock, los que si se encontraron se dejan como "DISPONIBLE" y se les quita el id de orden, incluye los productos que no tenian stock para que se actualice el carro

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "usuario_email": "email.email@gmail.com", 
  "metodo_pago": "Debito",
  "motivo": "Sin stock en región LATAM"
  "juegos_sin_stock": {
    "juego_id": "splatoon-3-ext"  
    "titulo": "splatoon"
  }
}

## Evento: Pago procesado
Nombre exacto en codigo: pago.procesado

Publicador: Modulo de pago

consumidores: Modulo de inventario - Modulo de ventas - Modulo de notificacione

Cuando: El pago se procesa de forma exitosa o no exitosa, se incluye resultado en payload

Payload:
{
  "id_usuario": "123"
  "usuario_email": "correo.ejemplo@gmail.com"
  "id_orden_compra": "ORD-12345",
  "estado_pago": "APROBADO",
  "motivo": "", 
  "region": "LATAM"
  "id_transaccion_pasarela": "txn_987654321"
}

Payload:
{
  "id_usuario": "123"
  "usuario_email": "correo.ejemplo@gmail.com"
  "id_orden_compra": "ORD-12345",
  "estado_pago": "NO APROBADO",
  "motivo": "motivo",
  "region": "LATAM"
  "id_transaccion_pasarela": "txn_987654321"
}


## Evento: Orden completada
Nombre exacto en codigo: inventario.orden_completada

Publicador: Modulo de inventario

Consumidor: Modulo de notificaciones

Cuando: El pago fue exitoso y el modulo de inventario cambio el estado de reservado a vendido para los productos de la orden

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_email": "correo.ejemplo@gmail.com",
  "items": {
    "juego_id": "splatoon-3-ext",
    "codigo_serial": "123abc"
  }
}

## Evento: cambio de stock
Nombre exacto en codigo: inventario.cambio_stock

Publicador: Modulo de inventario

Consumidor: Modulo de busqueda

Cuando: El modulo de inventario encuentra que despues de cambiar el estado de un producto, no may mas stock de este producto, o se cancela una reserva o venta y pasa de no haber ni uno a haber almenos uno

Payload:
{
  "juego_id": "splatoon-3-ext",
  "region": "LATAM",
  "Motivo": "DISPNIBLE" <- tambien puede ser "AGOTADO"
}

