# Por Donde Empezar

Bienvenido al backend de **LAIRN**, una plataforma de aprendizaje adaptativo que genera examenes personalizados con inteligencia artificial.

## ¿Que es LAIRN?

LAIRN es una API REST construida con Django que permite a docentes crear cursos y examenes, y a estudiantes tomarlos con preguntas generadas en tiempo real por Claude Haiku (IA de Anthropic). El sistema ajusta la dificultad de cada pregunta segun el rendimiento del estudiante.

## ¿Por donde empiezo?

Depende de lo que necesitas:

| Objetivo | Documento |
|----------|-----------|
| Levantar el proyecto rapido con Docker | [INICIO_RAPIDO.md](INICIO_RAPIDO.md) |
| Instalar sin Docker (entorno local) | [INSTALACION.md](INSTALACION.md) |
| Entender como esta organizado el codigo | [ESTRUCTURA.md](ESTRUCTURA.md) |
| Entender como funciona el sistema | [ARQUITECTURA.md](ARQUITECTURA.md) |
| Ver todos los endpoints disponibles | [AUTENTICACION.md](AUTENTICACION.md) |
| Configurar variables de entorno | [VARIABLES_ENTORNO.md](VARIABLES_ENTORNO.md) |
| Contribuir al proyecto | [CONTRIBUIR.md](CONTRIBUIR.md) |

## Requisitos minimos

- Docker y Docker Compose (recomendado)
- O bien: Python 3.12 + PostgreSQL 16
- Una clave de API de OpenAI (`OPENAI_API_KEY`) — obligatoria para el motor de examenes

## Accesos rapidos una vez levantado

| Recurso | URL |
|---------|-----|
| API principal | http://localhost:8000/api/ |
| Swagger (documentacion interactiva) | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Admin de Django | http://localhost:8000/admin/ |
