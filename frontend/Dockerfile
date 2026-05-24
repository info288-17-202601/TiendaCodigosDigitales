# --- ETAPA 1: Construcción (Build) ---
FROM node:18-alpine AS build

WORKDIR /app

# Copiar dependencias e instalarlas
COPY package.json package-lock.json* ./
RUN npm install

# Copiar código fuente y compilar la aplicación React
COPY . .
RUN npm run build

# --- ETAPA 2: Producción (Servir estáticos) ---
FROM nginx:alpine

# Copiar los archivos compilados de React al servidor web interno
COPY --from=build /app/build /usr/share/nginx/html

# Exponer el puerto interno 80
EXPOSE 80

# Arrancar Nginx en primer plano
CMD ["nginx", "-g", "daemon off;"]