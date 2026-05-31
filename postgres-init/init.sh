#!/bin/sh
set -e

# 1. Create different databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE db_usuarios;
    CREATE DATABASE db_catalogo;
    CREATE DATABASE db_ventas;
    CREATE DATABASE db_perfil;
    CREATE DATABASE db_inv_latam;
EOSQL

# 2. User DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_usuarios" <<-EOSQL
    CREATE TABLE usuario (
        id_usuario VARCHAR(50) PRIMARY KEY,
        usuario VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        contrasena VARCHAR(255) NOT NULL,
        region VARCHAR(20) NOT NULL
    );
EOSQL

# 3. Catalog DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_catalogo" <<-EOSQL
    CREATE TABLE catalogo (
        id_juego VARCHAR(50) PRIMARY KEY,
        titulo VARCHAR(150) NOT NULL,
        plataforma VARCHAR(50) NOT NULL,
        precio_base DECIMAL(10, 2) NOT NULL,
        disponibilidad_regional JSONB NOT NULL DEFAULT '{}'::jsonb
    );
    -- Insertar un producto de prueba
    INSERT INTO catalogo (id_juego, titulo, plataforma, precio_base, disponibilidad_regional) 
    VALUES (
        'splatoon-3-ext', 
        'Splatoon 3: Expansion Pass', 
        'Nintendo Switch', 
        19990.00, 
        '{"LATAM": true, "US": true, "EU": false}'::jsonb
    );

    -- Más juegos para el catálogo de Nintendo Switch
    INSERT INTO catalogo (id_juego, titulo, plataforma, precio_base, disponibilidad_regional) VALUES 
    ('splatoon-3', 'Splatoon 3', 'Nintendo Switch', 49990.00, '{"LATAM": true, "US": true, "EU": true}'::jsonb),
    ('mario-odyssey', 'Super Mario Odyssey', 'Nintendo Switch', 49990.00, '{"LATAM": false, "US": true, "EU": true}'::jsonb),
    ('zelda-totk', 'The Legend of Zelda: Tears of the Kingdom', 'Nintendo Switch', 59990.00, '{"LATAM": true, "US": false, "EU": true}'::jsonb),
    ('mario-kart-8', 'Mario Kart 8 Deluxe', 'Nintendo Switch', 49990.00, '{"LATAM": true, "US": true, "EU": true}'::jsonb);

    -- Juegos para el catálogo de PlayStation 5 (Sony)
    INSERT INTO catalogo (id_juego, titulo, plataforma, precio_base, disponibilidad_regional) VALUES 
    ('gow-ragnarok', 'God of War Ragnarök', 'PlayStation 5', 54990.00, '{"LATAM": true, "US": true, "EU": true}'::jsonb),
    ('spiderman-2', 'Marvel''s Spider-Man 2', 'PlayStation 5', 59990.00, '{"LATAM": true, "US": false, "EU": false}'::jsonb),
    ('tlou-part1', 'The Last of Us Part I', 'PlayStation 5', 49990.00, '{"LATAM": false, "US": false, "EU": false}'::jsonb), 
    ('elden-ring-ps5', 'Elden Ring', 'PlayStation 5', 44990.00, '{"LATAM": true, "US": true, "EU": true}'::jsonb);
EOSQL

# 4. Sales DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_ventas" <<-EOSQL
    CREATE TABLE orden_compra (
        id_orden_compra VARCHAR(50) PRIMARY KEY,
        id_usuario VARCHAR(50) NOT NULL,
        fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metodo_pago VARCHAR(50) NOT NULL,
        total_pagado DECIMAL(10, 2) NOT NULL,
        estado_pago VARCHAR(20) NOT NULL 
        -- Estados: PENDIENTE, PAGADO, COMPENSADO, FALLIDO
    );
EOSQL

# 5. Inventory DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_inv_latam" <<-EOSQL
    CREATE TABLE clave_digital (
        id_clave SERIAL PRIMARY KEY,
        id_juego VARCHAR(50) NOT NULL,
        codigo_serial VARCHAR(100) UNIQUE NOT NULL,
        estado VARCHAR(20) NOT NULL, 
        -- Estados: DISPONIBLE, RESERVADO, VENDIDO
        id_orden_compra VARCHAR(50) DEFAULT NULL
    );
    -- Insertar 2 códigos de prueba para simular stock
    INSERT INTO clave_digital (id_juego, codigo_serial, estado) VALUES 
    ('splatoon-3-ext', 'LATAM-ABCD-1234', 'DISPONIBLE'),
    ('splatoon-3-ext', 'LATAM-EFGH-5678', 'DISPONIBLE');
EOSQL

# 6. Profile DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_perfil" <<-EOSQL
    CREATE TABLE perfil_pago (
        id_perfil SERIAL PRIMARY KEY,
        id_usuario VARCHAR(50) NOT NULL,
        tipo_tarjeta VARCHAR(50) NOT NULL,
        token_pago VARCHAR(100) NOT NULL,
        ultimos_4 VARCHAR(4) NOT NULL
    );
EOSQL