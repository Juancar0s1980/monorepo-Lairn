# Imagen "runner" para preguntas de codigo en C++.
FROM alpine:3.20

RUN apk add --no-cache python3 g++ musl-dev
WORKDIR /app
RUN adduser -D -u 1000 sandboxuser
COPY runner.py .
USER sandboxuser

ENTRYPOINT ["python3", "runner.py"]
