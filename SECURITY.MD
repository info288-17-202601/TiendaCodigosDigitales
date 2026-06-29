# Matriz de accesos y permisos

| Rol (User DB)  | Microservicio  | Recursos (Tabla) | Acciones (Permisos)            | Notas|
|----------------|----------------|------------------|--------------------------------|------|
|user_usuarios   | mod_usuario    | usuario          | SELECT, INSERT, UPDATE         |------|
|user_catalogo   | mod_busqueda   | catalogo         | SELECT, UPDATE                 |------|
|user_ventas     | mod_ventas     | orden_compra     | SELECT, INSERT, UPDATE, DELETE |------| 
|user_inv        | mod_inventario | clave_digital    | SELECT, INSERT, UPDATE, DELETE |------|
|user_inv        | mod_admin      | catalogo         | INSERT                         |------|
|user_pagos      | mod_pago       | perfil_pago      | SELECT, INSERT, DELETE         |------|


# Generación de claves
Para la generación de claves seguras, se debe utilizar el programa `'genContraSegura.py'`, ubicado en la carpeta `backend`, el cual utiliza Secrets para la generación segura de contraseñas.

Para utilizarlo basta con ejecutar en la raiz del proyecto: 
```python
python backend/genContraSegura.py
```
El programa le pedirá la cantidad de contraseñas a crear, y la longitud (Se recomienda crear una contraseña entre 32, 64 incluso 128 caracteres para más seguridad)
```python
# Ejemplo rápido de ejecución
Ingrese la cantidad de claves a generar: 3
Ingrese la longitud de las claves a generar (entre 64 a 128 caracteres): 64
```
### **Recomendación para rotación de credenciales**
Se recomienda cambiar las claves en estas situaciones:

* **Cada 90 días:** de esta forma, aunque una credencial sea robada, se garantiza que el atacante no tendrá acceso permanente por tiempo indefinido, sino que su acceso será revocado cuando venza el plazo.

* **En cada despliegue mayor (Release):** Cada vez que hagan una actualización importante del sistema, es un momento ideal para cambiar las claves y asegurar que el sistema nuevo no arrastre llaves viejas que podrían estar en riesgo.

* **De forma inmediata (Rotación de emergencia):** Si un integrante del equipo deja el grupo o si sospechan que un archivo .env se subió por error a GitHub, el cambio de claves debe ser instantánea.

# Firewall lógico

Actualmente el proyecto se encuentra en una etapa de desarrollo y pruebas, ejecutándose en un entorno controlado mediante Docker. Debido a ello, no se ha configurado un firewall lógico, ya que durante el desarrollo es necesario exponer distintos puertos para facilitar las pruebas, la depuración y la comunicación entre los distintos microservicios.

### Configuración recomendada para producción

En un entorno de producción se recomienda instalar un firewall lógico en el sistema operativo del servidor (por ejemplo, **UFW** sobre Ubuntu Server), con el objetivo de restringir el acceso únicamente a los servicios que deban ser públicos.

La configuración recomendada consiste en:

* Permitir únicamente los puertos necesarios para el funcionamiento del sistema (HTTP, HTTPS y SSH para administración).
* Bloquear el acceso externo a servicios internos como PostgreSQL, Redis, RabbitMQ y Apache Solr.
* Mantener la comunicación entre microservicios a través de la red interna de Docker, evitando la exposición directa de estos servicios a Internet.
* Revisar periódicamente las reglas del firewall para asegurar que solo permanezcan abiertos los puertos estrictamente necesarios.

De esta forma se reduce la superficie de ataque del sistema y se evita el acceso directo a componentes internos que no requieren comunicación desde el exterior.

# Protocolos seguros (HTTPS / OAuth2 / OpenID Connect)

Actualmente el proyecto usa sesiones en Redis y autenticación propia en los microservicios. Para producción se recomienda migrar a comunicaciones cifradas y delegar autenticación a un proveedor OIDC/OAuth2, manteniendo compatibilidad temporal con el flujo de sesiones existente.

### Configuración recomendada para producción
* Forzar TLS: terminar TLS en el proxy inverso, redirigir HTTP → HTTPS, habilitar HSTS y encabezados de seguridad. Revisar nginx.conf.  
* No exponer servicios internos: mantener PostgreSQL, Redis, RabbitMQ y Solr únicamente en la red interna de Docker y bloquear accesos externos en el host y en `docker-compose` (docker-compose.yml).  
* Proveedor OIDC/OAuth2: seleccionar un proveedor (externo o interno) y usar Authorization Code + PKCE para la SPA del frontend.  
* Validación en backend: añadir middleware en cada microservicio que valide tokens (firma JWT, `iss`, `aud`, `exp`) o use introspección para tokens opacos; permitir un modo de transición que valide también las sesiones actuales en Redis. Ver security.py y puntos de entrada como api.py.  
* Almacenamiento en frontend: evitar `localStorage` para tokens de larga vida; preferir `httpOnly, Secure` cookies para refresh tokens y mantener access token en memoria. Actualizar AuthContext.js.  
* Gestión de secretos: almacenar client secrets, certificados y claves en un gestor seguro (Vault, AWS/Azure Key Vault) y automatizar rotación y revocación (usar `genContraSegura.py` para contraseñas seguras).  
* Comunicación entre microservicios: conservar tráfico por la red interna; en producción considerar mTLS o service mesh para autenticación mutua.  
* Políticas de tokens: usar access tokens de corta duración, refresh tokens con rotación y revocación; diseñar scopes/roles mínimos y auditar uso.  
* Observabilidad y respuesta: registrar intentos de autenticación y fallos, exponer métricas y endpoints/operaciones para revocar sesiones o tokens comprometidos.

### Pasos prácticos mínimos
- Configurar TLS en el proxy (nginx.conf) y exponer solo 443 en producción.  
- Definir variables de entorno: `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `FRONTEND_URL`.  
- Implementar middleware de validación en security.py y aplicarlo en los microservicios (ej. `mod_usuario`).  
- Migrar `AuthContext` a Authorization Code+PKCE y manejo seguro de tokens en frontend.  
- Mover secretos a un gestor seguro y documentar la rotación.  
- Probar E2E en staging antes de desactivar el flujo legacy.
