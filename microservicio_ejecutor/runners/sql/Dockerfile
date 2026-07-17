# Imagen "runner" para preguntas de codigo en SQL (SQLite en memoria).
# Misma logica que runners/python: contenedor efimero, sin red, limites
# de recursos aplicados desde afuera por el microservicio ejecutor.
FROM python:3.12-alpine

WORKDIR /app
RUN adduser -D -u 1000 sandboxuser
COPY runner.py .
USER sandboxuser

ENTRYPOINT ["python3", "runner.py"]
