# Imagen "runner" para preguntas de codigo en Java.
# python3 solo se usa como "conductor" del runner (orquesta compilar +
# ejecutar + timeout); el codigo del estudiante corre con javac/java.
FROM eclipse-temurin:21-jdk-alpine

RUN apk add --no-cache python3
WORKDIR /app
RUN adduser -D -u 1000 sandboxuser
COPY runner.py .
USER sandboxuser

ENTRYPOINT ["python3", "runner.py"]
