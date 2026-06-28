#!/bin/sh
set -e

# 1. Create different databases, users, and grant privileges
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE db_usuarios;
    CREATE DATABASE db_catalogo;
    CREATE DATABASE db_ventas;
    CREATE DATABASE db_perfil;
    CREATE DATABASE db_inv_latam;
    CREATE DATABASE db_inv_eu;
    CREATE DATABASE db_inv_us;
    CREATE DATABASE db_inv_asia;

-- Crear Usuarios Aislados (Las contraseñas vendrán del .env)
    CREATE USER ${DB_USER_USUARIOS} WITH PASSWORD '${DB_PASS_USUARIOS}';
    CREATE USER ${DB_USER_CATALOGO} WITH PASSWORD '${DB_PASS_CATALOGO}';
    CREATE USER ${DB_USER_VENTAS} WITH PASSWORD '${DB_PASS_VENTAS}';
    CREATE USER ${DB_USER_INVENTARIO} WITH PASSWORD '${DB_PASS_INVENTARIO}';
    CREATE USER ${DB_USER_PAGOS} WITH PASSWORD '${DB_PASS_PAGOS}';
    CREATE USER ${DB_USER_ADMIN} WITH PASSWORD '${DB_PASS_ADMIN}';

    -- Asignar dueños de las Bases de Datos
    GRANT ALL PRIVILEGES ON DATABASE db_usuarios TO ${DB_USER_USUARIOS};
    GRANT ALL PRIVILEGES ON DATABASE db_catalogo TO ${DB_USER_CATALOGO};
    GRANT ALL PRIVILEGES ON DATABASE db_ventas TO ${DB_USER_VENTAS};
    GRANT ALL PRIVILEGES ON DATABASE db_perfil TO ${DB_USER_PAGOS};
    GRANT ALL PRIVILEGES ON DATABASE db_inv_latam TO ${DB_USER_INVENTARIO};
    GRANT ALL PRIVILEGES ON DATABASE db_inv_eu TO ${DB_USER_INVENTARIO};
    GRANT ALL PRIVILEGES ON DATABASE db_inv_us TO ${DB_USER_INVENTARIO};
    GRANT ALL PRIVILEGES ON DATABASE db_inv_asia TO ${DB_USER_INVENTARIO};
EOSQL

# 2. User DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_usuarios" <<-EOSQL
    CREATE TABLE usuario (
        id_usuario UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        usuario VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        contrasena VARCHAR(255) NOT NULL,
        region VARCHAR(20) NOT NULL,
        rol VARCHAR(20) NOT NULL
    );
    -- Dar permisos a nivel de tablas
    GRANT SELECT, INSERT, UPDATE ON usuario TO ${DB_USER_USUARIOS};
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

    -- Dar permisos a nivel de tablas
    GRANT SELECT, UPDATE ON catalogo TO ${DB_USER_CATALOGO};
    GRANT INSERT ON catalogo TO ${DB_USER_INVENTARIO};
EOSQL

# 4. Sales DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_ventas" <<-EOSQL
    CREATE TABLE orden_compra (
        id_orden_compra VARCHAR(50) PRIMARY KEY,
        id_usuario UUID NOT NULL,
        detalles_carrito JSONB NOT NULL,
        fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metodo_pago VARCHAR(50) NOT NULL,
        total_pagado DECIMAL(10, 2) NOT NULL,
        estado_pago VARCHAR(20) NOT NULL,
        motivo VARCHAR(500)
        -- Estados: PENDIENTE, PAGADO, COMPENSADO, FALLIDO
    );
    -- Dar permisos a nivel de tablas
    GRANT SELECT, INSERT, UPDATE, DELETE ON orden_compra TO ${DB_USER_VENTAS};
EOSQL

# 5. Inventary tables
crear_inventario() {
    local DB_NAME=$1
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
        CREATE TABLE clave_digital (
            id_clave SERIAL PRIMARY KEY,
            id_juego VARCHAR(50) NOT NULL,
            codigo_serial VARCHAR(100) UNIQUE NOT NULL,
            estado VARCHAR(20) NOT NULL, 
            id_orden_compra VARCHAR(50) DEFAULT NULL
        );
        -- Dar permisos a nivel de tablas y secuencias (SERIAL)
    GRANT SELECT, INSERT, UPDATE, DELETE ON clave_digital TO ${DB_USER_INVENTARIO};
    GRANT USAGE, SELECT ON SEQUENCE clave_digital_id_clave_seq TO ${DB_USER_INVENTARIO};
EOSQL
}

crear_inventario "db_inv_latam"
crear_inventario "db_inv_eu"
crear_inventario "db_inv_us"
crear_inventario "db_inv_asia"

# 6. Profile DB tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "db_perfil" <<-EOSQL
    CREATE TABLE perfil_pago (
        id_perfil SERIAL PRIMARY KEY,
        id_usuario UUID NOT NULL,
        tipo_tarjeta VARCHAR(50) NOT NULL,
        token_pago VARCHAR(100) NOT NULL,
        ultimos_4 VARCHAR(4) NOT NULL
    );
    -- Dar permisos a nivel de tablas y secuencias
    GRANT SELECT, INSERT, DELETE ON perfil_pago TO ${DB_USER_PAGOS};
    GRANT USAGE, SELECT ON SEQUENCE perfil_pago_id_perfil_seq TO ${DB_USER_PAGOS};
EOSQL