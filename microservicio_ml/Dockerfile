# Imagen del microservicio ML (sirve el modelo BKT via FastAPI).
FROM python:3.12-slim

WORKDIR /app

# Instala solo las dependencias de servicio (ligeras, sin torch).
COPY requirements/base.txt requirements/api.txt requirements/
RUN pip install --no-cache-dir -r requirements/api.txt

# Copia el codigo del servicio, las definiciones de modelo y los artefactos.
# (El .dockerignore excluye notebooks, datos y docs para una imagen liviana.)
COPY . .

EXPOSE 8001

# main del paquete app. app.main:app = objeto FastAPI 'app'.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
