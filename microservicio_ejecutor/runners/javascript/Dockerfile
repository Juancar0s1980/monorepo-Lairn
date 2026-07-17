# Imagen "runner" para preguntas de codigo en JavaScript (Node.js).
# Mismo patron que runners/python: contenedor efimero, sin red, limites de
# recursos aplicados desde afuera por el microservicio ejecutor.
#
# node:alpine ya trae un usuario "node" en UID 1000 de fabrica (por eso no
# se crea uno propio como en los demas runners: colisionaria con ese UID).
# El microservicio ejecutor igual fuerza `user=1000:1000` al lanzar el
# contenedor, así que el usuario preexistente cumple el mismo proposito.
FROM node:20-alpine

WORKDIR /app
COPY runner.js .
USER node

ENTRYPOINT ["node", "runner.js"]
