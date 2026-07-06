# ---------- Etapa 1: build de la SPA con Node ----------
FROM node:22-alpine AS build
WORKDIR /app

# Instala dependencias con cache eficiente (solo copia manifests primero)
COPY package.json package-lock.json ./
RUN npm ci

# Copia el resto del código y compila
COPY . .
# VITE_API_URL se "hornea" en el bundle en build-time.
# Usamos una ruta relativa /api para que el browser pegue al mismo origen
# y nginx haga proxy al backend (así evitamos CORS por completo).
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---------- Etapa 2: servir con nginx ----------
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
