## Event: Order created 
Publisher: Sales module.

Consumer: Inventory module.

When: User presses "Pagar".

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "email": "correo.ejemplo@gmail.com",
  "region": "LATAM",
  "items": [
    {"juego_id": "splatoon-3-ext", "cantidad": 1}
  ],
  "total": 19990
}

## Event: Reserved inventory - Product ready for purchase
Publisher: Inventory module.

Consumer: Payment module.

When: Stock was found, state on DB was changed to "RESERVADO" and was asigned id_orden_compra.

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "usuario_email": "email.email@gmail.com", 
  "items": [
    {"juego_id": "splatoon-3-ext", "cantidad": 1}
  ],
  "estado_reserva": "EXITO",
  "monto_a_cobrar": 19990
}

### Alternative event: Invetory out of stock
Publisher: Sales module.

Consumer: Payment module.

When: A product on the listed items was found out of stock.

Payload:
{
  "id_orden_compra": "ORD-12345",
  "usuario_id": "9988-7766",
  "usuario_email": "email.email@gmail.com", 
  "motivo": "Sin stock en región LATAM"
}

## Event: Payment processed 
Publisher: Payment module.

Consumers: Inventory module.

When: Payment was succesfully processed.

Payload:
{
  "id_orden_compra": "ORD-12345",
  "estado_pago": "APROBADO",
  "id_transaccion_pasarela": "txn_987654321"
}

### Alternative event: Payment failed
Publisher: Payment module.

Consumers: Sales module.

When: Payment encountered an error.

Payload:
{
  "id_orden_compra": "ORD-12345", 
  "motivo": "Tarjeta rechazada"
}

## Event: Order completed
Publisher: Inventory module.

Consumers: Sales module - Notifications module.

When: Payment was succesful and product state was changed from "RESERVADO" to "SOLD".

Payload:
{
  "id_orden_compra": "ORD-12345",
  "email": "correo.ejemplo@gmail.com",
  "juego_id": "splatoon-3-ext",
  "codigos_entregados": ["ABCD-EFGH-IJKL-MNOP"] 
}

