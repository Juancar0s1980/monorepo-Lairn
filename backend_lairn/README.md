# Lairn — Sistema Adaptativo de Aprendizaje

> API backend para una plataforma de tutoría inteligente que genera exámenes adaptativos con IA y modela el conocimiento del estudiante en tiempo real.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [Por Donde Empezar](docs/POR_DONDE_EMPEZAR.md) | Punto de entrada según tu rol |
| [Inicio Rápido](docs/INICIO_RAPIDO.md) | De cero a servidor corriendo con Docker |
| [Instalación](docs/INSTALACION.md) | Instalación local sin Docker |
| [Variables de Entorno](docs/VARIABLES_ENTORNO.md) | Configuración de entorno y secretos |
| [Estructura](docs/ESTRUCTURA.md) | Mapa del repositorio y convenciones |
| [Arquitectura](docs/ARQUITECTURA.md) | Diagrama del sistema y decisiones de diseño |
| [Autenticación y Endpoints](docs/AUTENTICACION.md) | Todos los endpoints con ejemplos |
| [Base de Datos](docs/BASE_DE_DATOS.md) | Modelos, relaciones y migraciones |
| [Manejo de Errores](docs/MANEJO_ERRORES.md) | Catálogo de errores HTTP |
| [Seguridad](docs/SEGURIDAD.md) | Configuración segura para producción |
| [Contribuir](docs/CONTRIBUIR.md) | Flujo de trabajo y convenciones |
| [Resumen del Proyecto](docs/RESUMEN_PROYECTO.md) | Visión general sin tecnicismos |
| [Comandos](docs/COMANDOS.md) | Referencia de comandos Docker y Django |
| [Guía Completa de Endpoints](docs/GUIA_COMPLETA_ENDPOINTS.md) | Explicación de cada endpoint en lenguaje simple |
| [Motor de IA](docs/MOTOR_IA.md) | Prompt, agente, ajuste de dificultad y modelo de conocimiento a detalle |

---

## Vista Rápida

```
Rol: Docente                  Rol: Estudiante
──────────────────            ──────────────────
1. Crea un curso              1. Se inscribe al curso
2. Crea un examen             2. Inicia el examen
3. Consulta analítica         3. Responde preguntas IA
                              4. Recibe resultado y nota
```

### Stack Principal

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Python | 3.12 | Lenguaje base |
| Django | 6.0.4 | Framework web |
| Django REST Framework | 3.17.1 | API REST |
| PostgreSQL | 16 | Base de datos |
| GPT-4o Mini (OpenAI) | — | Generación de preguntas IA |
| SimpleJWT | 5.5.1 | Autenticación JWT |
| Docker / Compose | latest | Contenedorización |

---

## Inicio Rápido

### Con Docker (recomendado)

```bash
# 1. Clonar el repositorio
git clone <url-repositorio>
cd backend_lairn

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (especialmente OPENAI_API_KEY)

# 3. Levantar servicios
docker-compose up --build

# 4. Crear roles y usuarios de prueba
docker-compose exec web python manage.py seed_roles
docker-compose exec web python manage.py seed_usuarios

# 5. La API estará disponible en:
# http://localhost:8000/api/
```

### Sin Docker

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_roles
python manage.py seed_usuarios
python manage.py runserver
```

---

## Documentación Interactiva

Una vez el servidor esté corriendo:

| URL | Descripción |
|-----|-------------|
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |
| `http://localhost:8000/api/schema/` | OpenAPI 3.0 (JSON) |

---

## Usuarios de Prueba

Creados por `python manage.py seed_usuarios`:

| Email | Contraseña | Rol |
|-------|-----------|-----|
| `admin@pseudotutor.com` | `admin1234` | Administrador |
| `docente@pseudotutor.com` | `docente1234` | Docente |
| `estudiante@pseudotutor.com` | `estudiante1234` | Estudiante |

---

## Estructura del Proyecto

```
backend_lairn/
├── README.md
├── .env.example                 ← Plantilla de variables de entorno
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── backend_lairn/               ← Configuración Django
├── core/                        ← Utilidades compartidas (permisos por rol)
├── apps/                        ← Módulos de negocio
│   ├── users/                   ← Autenticación y usuarios
│   ├── examenes/                ← Cursos, exámenes e inscripciones
│   ├── motor_adaptativo/        ← Motor de IA y sesiones de examen
│   ├── analitica/               ← Resultados y estadísticas
│   └── moderacion/              ← Pendiente de implementación
└── docs/                        ← Documentación completa
```

---

*Lairn — Adaptive Learning API · Django 6 · Python 3.12 · PostgreSQL 16 · OpenAI GPT-4o Mini*
