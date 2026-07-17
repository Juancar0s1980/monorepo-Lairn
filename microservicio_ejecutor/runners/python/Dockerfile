# Imagen "runner" para preguntas de codigo en Python.
# No expone ningun servicio: cada ejecucion es un contenedor efimero (--rm)
# lanzado por el microservicio ejecutor, con la red y los recursos limitados
# desde afuera (ver app/servicios/sandbox.py).
FROM python:3.12-alpine

WORKDIR /app
RUN adduser -D -u 1000 sandboxuser
COPY runner.py .
USER sandboxuser

ENTRYPOINT ["python3", "runner.py"]
