# Redis contracts

## User session

### Key
session:\<token>

### Value
{
"usuario": "SquidKid_Chile",
"correo": "correo.ejemplo@gmail.com",
"region": "LATAM",
"rol": "usuario"
}

## Carrito

### Key
carrito\:<usuario_id>

### Value
{
"items": [
{
"juego_id": "splatoon-3-ext",
"titulo": "Splatoon 3: Expansion Pass",
"precio": 19990,
"cantidad": 1
}
],
"total_estimado": 19990,
"region_compra": "LATAM"
}