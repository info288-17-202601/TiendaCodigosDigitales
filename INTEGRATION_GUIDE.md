# Guía de Integración - Frontend + Backend 🔗

## 📋 Resumen

Esta guía explica cómo el frontend React está conectado a los microservicios del backend y qué hacer si encuentras problemas.

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│                   CLIENTE (NAVEGADOR)                        │
│              Frontend React - Port 3000                      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │ SearchBar → GameGrid → GameDetail → Cart           │     │
│  └────────────────────────────────────────────────────┘     │
│                            ↓ HTTP                            │
│                   CORS Enabled                               │
│                            ↓                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                SERVIDOR (DOCKER CONTAINERS)                 │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ mod_busqueda     │  │ mod_ventas       │                 │
│  │ Port: 5002       │  │ Port: 5050       │                 │
│  │ (Flask + Solr)   │  │ (Flask)          │                 │
│  │ GET /buscar      │  │ POST /comprar    │                 │
│  │ GET /juego/{id}  │  │                  │                 │
│  └──────────────────┘  └──────────────────┘                 │
│          ↓                       ↓                           │
│       ┌─────┐              ┌─────────┐                      │
│       │Solr │              │PostgreSQL│                      │
│       │ DB  │              │ (Ventas) │                      │
│       └─────┘              └─────────┘                       │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ mod_pago         │  │ mod_inventario   │                 │
│  │ Port: 5001       │  │ Port: 5003       │                 │
│  │ (No está usado)  │  │ (No está usado)  │                 │
│  └──────────────────┘  └──────────────────┘                 │
│          ↓                       ↓                           │
│       (Futuro)             ┌─────────┐                      │
│                            │PostgreSQL│                      │
│                            │(Inventario)                      │
│                            └─────────┘                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📡 Endpoints Activos

### ✅ Frontend → mod_busqueda (FUNCIONANDO)

```
GET /buscar?q=mario
│
├─ Request Headers:
│   Accept: application/json
│   Origin: http://localhost:3000
│
└─ Response (200 OK):
   {
     "mensaje": "Búsqueda exitosa",
     "cantidad_encontrada": 5,
     "resultados": [
       {
         "id_juego": "game-123",
         "titulo": "Super Mario Bros",
         "precio": 19.99,
         "imagen_url": "https://...",
         "descripcion": "Classic game",
         "developer": "Nintendo",
         "fecha_lanzamiento": "1985-09-13"
       }
     ]
   }
```

```
GET /juego/game-123
│
├─ Request Headers:
│   Accept: application/json
│   Origin: http://localhost:3000
│
└─ Response (200 OK):
   {
     "id_juego": "game-123",
     "titulo": "Super Mario Bros",
     "precio": 19.99,
     "imagen_url": "https://...",
     "descripcion": "Classic game",
     "developer": "Nintendo",
     "fecha_lanzamiento": "1985-09-13"
   }
```

### ⏳ Frontend → mod_ventas (FUTURO)

```
POST /ventas/comprar
│
├─ Request Headers:
│   Content-Type: application/json
│   Origin: http://localhost:3000
│
├─ Request Body:
│   {
│     "usuario_id": "user-123",
│     "email": "user@example.com",
│     "carrito": [
│       {"id_juego": "game-123", "cantidad": 2, "precio": 19.99}
│     ]
│   }
│
└─ Response (200 OK):
   {
     "id_orden_compra": "ORD-ABC12345",
     "estado": "PENDIENTE",
     "total": 39.98
   }
```

---

## 🔧 Configuración Requerida

### 1. Frontend (.env)
```
REACT_APP_BUSQUEDA_API=http://localhost:5002
REACT_APP_VENTAS_API=http://localhost:5050
REACT_APP_PAGO_API=http://localhost:5001
REACT_APP_INVENTARIO_API=http://localhost:5003
```

### 2. Backend (app.py)

**IMPORTANTE**: Agregar CORS para que el frontend pueda comunicarse:

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Habilitar CORS para desarrollo
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/buscar', methods=['GET'])
def buscar():
    # ... tu código
    pass
```

### 3. Docker (si usas contenedores)

El puerto del frontend debe ser accesible desde el navegador:
```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BUSQUEDA_API=http://localhost:5002
      - REACT_APP_VENTAS_API=http://localhost:5050
```

---

## 🚀 Pasos para Ejecutar Todo

### Opción 1: Sin Docker (Local)

```bash
# Terminal 1: Backend búsqueda
cd backend/mod_busqueda
python app.py
# Corre en http://localhost:5002

# Terminal 2: Backend ventas
cd backend
python app.py
# Corre en http://localhost:5050

# Terminal 3: Frontend
cd frontend
npm install
npm start
# Abre http://localhost:3000
```

### Opción 2: Con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose up

# Espera a que todos los servicios estén "healthy"
# Frontend: http://localhost:3000
# mod_busqueda: http://localhost:5002
# mod_ventas: http://localhost:5050
```

---

## 🔍 Debugging: CORS Error

### Síntoma
```
Access to XMLHttpRequest at 'http://localhost:5002/buscar' from origin 
'http://localhost:3000' has been blocked by CORS policy
```

### Causas Comunes
1. ❌ Backend no tiene CORS habilitado
2. ❌ Origen no está permitido
3. ❌ Método HTTP no está permitido

### Soluciones

**Solución 1: Agregar CORS al backend**
```python
from flask_cors import CORS
CORS(app)  # Permite todos los orígenes en desarrollo
```

**Solución 2: Especificar origen exacto**
```python
CORS(app, resources={
    r"/*": {"origins": "http://localhost:3000"}
})
```

**Solución 3: Usar proxy en desarrollo**
Crear `src/setupProxy.js`:
```javascript
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5002',
      changeOrigin: true,
    })
  );
};
```

---

## 📡 Flujo de una Búsqueda Completa

```
1. Usuario escribe "mario" y presiona Enter
   └─→ SearchBar.onSubmit() se ejecuta

2. Se llama: handleSearch("mario")
   └─→ App.js actualiza estado

3. Se ejecuta fetch(SEARCH_ENDPOINTS.buscar("mario"))
   └─→ URL: http://localhost:5002/buscar?q=mario

4. Headers enviados:
   GET /buscar?q=mario HTTP/1.1
   Host: localhost:5002
   Origin: http://localhost:3000
   Accept: application/json

5. Backend (mod_busqueda) recibe request
   └─→ Consulta Solr
   └─→ Devuelve resultados

6. Frontend recibe respuesta
   └─→ JSON.parse(data)
   └─→ setGames(data.resultados)

7. React re-renderiza
   └─→ <GameGrid games={games} />
   └─→ Se muestran tarjetas de juegos

8. Usuario ve resultados en pantalla ✅
```

---

## 🧪 Testing de Endpoints

### Con cURL (Terminal)

```bash
# Buscar juegos
curl http://localhost:5002/buscar?q=mario

# Ver detalles de un juego
curl http://localhost:5002/juego/game-123

# Hacer una compra (POST)
curl -X POST http://localhost:5050/ventas/comprar \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "user-123",
    "email": "user@example.com"
  }'
```

### Con Postman

1. Descarga [Postman](https://www.postman.com/downloads/)
2. Crea una nueva solicitud GET
3. URL: `http://localhost:5002/buscar?q=mario`
4. Haz clic en "Send"
5. Verás la respuesta en JSON

### Desde el navegador

```javascript
// Abre DevTools (F12) → Console

// Prueba buscar
fetch('http://localhost:5002/buscar?q=mario')
  .then(r => r.json())
  .then(d => console.log(d))
  .catch(e => console.error(e));

// Prueba detalle
fetch('http://localhost:5002/juego/game-123')
  .then(r => r.json())
  .then(d => console.log(d))
  .catch(e => console.error(e));
```

---

## 📊 Estados y Códigos HTTP

| Código | Significado | Acción |
|--------|------------|--------|
| 200 | OK | Éxito, procesa datos |
| 201 | Created | Recurso creado |
| 400 | Bad Request | Error en request, verifica parámetros |
| 401 | Unauthorized | Requiere autenticación |
| 404 | Not Found | Endpoint no existe |
| 500 | Server Error | Error en backend, revisa logs |
| 503 | Service Unavailable | Servidor caído |

---

## 🔐 Seguridad

### En Desarrollo ✅
```python
CORS(app)  # Permite todo
```

### En Producción ⚠️
```python
CORS(app, resources={
    r"/*": {
        "origins": "https://tusitio.com",  # Solo tu dominio
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"],
        "max_age": 3600
    }
})
```

### Headers de Seguridad
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

## 📝 Logs Útiles

### Frontend (console del navegador)
```javascript
// Abre DevTools (F12) → Console tab

// Ver todas las peticiones
console.log('Buscando:', query);
console.log('Response:', data);
console.log('Error:', error);
```

### Backend (terminal)
```bash
# Ver logs en tiempo real
tail -f backend.log

# O redirigir a archivo
python app.py > backend.log 2>&1
```

---

## 🚀 Próximos Pasos

1. ✅ Frontend búsqueda funcionando
2. ⏳ Integrar mod_ventas (POST /comprar)
3. ⏳ Integrar mod_pago (procesamiento)
4. ⏳ Integrar mod_inventario (stock)
5. ⏳ Agregar autenticación
6. ⏳ Deploy a producción

---

## 📞 FAQ

**P: ¿Por qué veo "No hay juegos" aunque busco?**
R: Verifica que:
- mod_busqueda esté corriendo (puerto 5002)
- Solr esté iniciado
- La base de datos tenga datos
- CORS esté habilitado

**P: ¿Cómo cambio los puertos?**
R: Edita `.env` en el frontend:
```
REACT_APP_BUSQUEDA_API=http://localhost:NUEVO_PUERTO
```

**P: ¿Puedo usar esto en producción?**
R: Sí, pero:
- Deshabilita hot reload
- Habilita HTTPS
- Usa variables de entorno
- Implementa autenticación

**P: ¿Cómo agrego un nuevo endpoint?**
R: 
1. Crea el endpoint en el backend
2. Agrégalo a `src/config/apiConfig.js`
3. Úsalo en los componentes

---

**Última actualización**: 30 de mayo de 2026
