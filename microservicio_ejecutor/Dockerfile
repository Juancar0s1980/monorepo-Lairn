# Imagen del microservicio ejecutor (sandbox de codigo via FastAPI).
#
# A diferencia de los demas servicios del proyecto, este SI corre como root
# dentro de su propio contenedor: es requisito para poder hablarle al socket
# de Docker del host (/var/run/docker.sock), que es lo que le permite lanzar
# los contenedores efimeros y aislados donde realmente corre el codigo del
# estudiante. El codigo del estudiante nunca corre aqui, siempre en un
# contenedor "runner" separado con su propio usuario sin privilegios
# (ver runners/*/Dockerfile y app/servicios/sandbox.py).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Incluye runners/ (Dockerfiles + runner.py): el propio servicio los
# construye en el daemon de Docker al arrancar si todavia no existen.
COPY . .

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
