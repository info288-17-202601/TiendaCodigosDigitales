# Redis contracts

## User session

### Key
session:\<token>

### Value
{
"usuario_id": "9988-7766",
"usuario": "SquidKid_Chile",
"region": "LATAM",
"correo": "correo.ejemplo@gmail.com",
"moneda": "CLP",
"ultimo_acceso": "2026-03-31T20:40:00Z"
}

## Cart 

### Key
cart\:<usuario_id>

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