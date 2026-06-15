# --- Build react app ---

# Node version - uses alpine to save storage
FROM node:18-alpine AS build

# Work directory inside container - Following commands run here
WORKDIR /app

# ENV variables for dev
ARG VITE_CORREO_PRUEBA
ENV VITE_CORREO_PRUEBA=$VITE_CORREO_PRUEBA

# Copy and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code and build react application
COPY . .
RUN npm run build

# --- For production, serve static assets ---

# Switch to nginx image - Doesn't inherit node, app is already built
FROM nginx:alpine

# Copy compiled react files to internal web server
COPY --from=build /app/build /usr/share/nginx/html

# Exposes port
EXPOSE 80

# Runs nginx
CMD ["nginx", "-g", "daemon off;"]