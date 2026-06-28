# Matriz de accesos y permisos

| Rol (User DB)  | Microservicio  | Recursos (Tabla) | Acciones (Permisos)            | Notas|
|----------------|----------------|------------------|--------------------------------|------|
|user_usuarios   | mod_usuario    | usuario          | SELECT, INSERT, UPDATE         |------|
|user_catalogo   | mod_busqueda   | catalogo         | SELECT, UPDATE                 |------|
|user_ventas     | mod_ventas     | orden_compra     | SELECT, INSERT, UPDATE, DELETE |------| 
|user_inv        | mod_inventario | clave_digital    | SELECT, INSERT, UPDATE, DELETE |------|
|user_inv        | mod_admin      | catalogo         | INSERT                         |------|
|user_pagos      | mod_pago       | perfil_pago      | SELECT, INSERT, DELETE         |------|
