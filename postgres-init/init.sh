#!/bin/bash
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
        precio_base DECIMAL(10, 2) NOT NULL
    );
    -- Insertar un producto de prueba para que puedan probar mañana
    INSERT INTO catalogo (id_juego, titulo, plataforma, precio_base) 
    VALUES ('splatoon-3-ext', 'Splatoon 3: Expansion Pass', 'Nintendo Switch', 19990.00);
EOSQL

# 4. Sales DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_ventas" <<-EOSQL
    CREATE TABLE orden_compra (
        id_orden_compra VARCHAR(50) PRIMARY KEY,
        id_usuario VARCHAR(50) NOT NULL,
        fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        id_usuario VARCHAR(50) NOT NULL,
        tipo_tarjeta VARCHAR(50) NOT NULL,
        token_pago VARCHAR(100) NOT NULL,
        ultimos_4 VARCHAR(4) NOT NULL
    );
EOSQL