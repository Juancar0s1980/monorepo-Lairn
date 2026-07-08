# Lairn (PseudoTutor)

Plataforma de exámenes adaptativos con generación de preguntas por IA y
estimación de dominio de conocimiento (Knowledge Tracing). El monorepo
contiene tres servicios propios más una base de datos, orquestados con Docker
Compose:

| Servicio | Carpeta | Tecnología | Rol |
|----------|---------|------------|-----|
| `db` | — | PostgreSQL 16 | Base de datos |
| `web` | `backend_lairn/` | Django + DRF | API REST, autenticación JWT, lógica de negocio |
| `ml` | `microservicio_ml/` | FastAPI | Knowledge Tracing (BKT/DKT) — estima dominio y sugiere dificultad |
| `frontend` | `Lairn_Frontend/` | React + Vite + TS | Interfaz web (Administrador, Docente, Estudiante) |

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose v2)
- Una clave de OpenAI (`OPENAI_API_KEY`) — el backend la usa para generar preguntas de examen
- Node.js 22+ y Python 3.12+ solo si vas a correr algún servicio **sin** Docker

## Puesta en marcha rápida

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Monorepo_Lairn
```

### 2. Configurar variables de entorno del backend

```bash
cp backend_lairn/.env.example backend_lairn/.env
```

Edita `backend_lairn/.env` y completa al menos:

```env
SECRET_KEY=una-clave-secreta-larga-y-aleatoria
DEBUG=True
OPENAI_API_KEY=sk-...          # obligatoria para generar preguntas de examen
```

El resto de variables (`DB_*`, `ML_SERVICE_URL`) ya traen valores por defecto
correctos para levantar todo con Docker Compose — no hace falta tocarlas.
Detalle completo de cada variable en
[`backend_lairn/docs/VARIABLES_ENTORNO.md`](backend_lairn/docs/VARIABLES_ENTORNO.md).

El microservicio `ml` y el `frontend` no requieren un `.env` para correr con
Docker: usan valores por defecto (`docker-compose.yml` ya les pasa lo
necesario).

### 3. Levantar todo con Docker Compose

Desde la raíz del repo:

```bash
docker compose up --build -d
```

Esto construye las 3 imágenes propias y levanta los 4 contenedores. El
backend aplica las migraciones automáticamente al iniciar.

Revisa que todo esté sano:

```bash
docker compose ps
```

Deberías ver `db`, `web`, `ml` y `frontend` en estado `Up` (los dos primeros
además con `healthy`).

### 4. Sembrar roles y usuarios de prueba

En otra terminal:

```bash
docker compose exec web python manage.py seed_roles
docker compose exec web python manage.py seed_usuarios
```

`seed_roles` crea los tres roles del sistema (Administrador, Docente,
Estudiante). `seed_usuarios` crea una cuenta de prueba por cada rol:

| Email | Contraseña | Rol |
|-------|------------|-----|
| `admin@pseudotutor.com` | `Admin1234*` | Administrador |
| `docente@pseudotutor.com` | `Docente1234*` | Docente |
| `estudiante@pseudotutor.com` | `Estudiante1234*` | Estudiante |

Si ya existen (por ejemplo, en una segunda ejecución), el comando los omite
sin duplicarlos ni fallar.

### 5. Verificar que funciona

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| API (Swagger) | http://localhost:8000/api/docs/ |
| API (Redoc) | http://localhost:8000/api/redoc/ |
| Microservicio ML (health) | http://localhost:8002/health |

Entra a http://localhost:5173 e inicia sesión con cualquiera de las cuentas
de la tabla anterior.

## Tour rápido por rol

### Administrador
- **Dashboard** (`/`): métricas del sistema (usuarios, cursos, exámenes, nota promedio, sesiones activas) y actividad reciente.
- **Usuarios** (`/usuarios`): listar todos los usuarios, cambiar su rol, activar/desactivar cuentas, eliminarlas.
- **Exámenes** (`/examenes`): supervisión global de todos los exámenes del sistema (curso, docente, modo, preguntas).
- **Analítica** (`/analitica`): métricas agregadas y rendimiento comparado por curso.
- **Redes** (`/redes`): estado de los modelos de Knowledge Tracing (BKT/DKT) servidos por el microservicio ML.
- **Moderación** (`/moderacion`): revisa reportes de cursos/exámenes enviados por docentes o estudiantes; marca como resuelto/descartado.

### Docente
- **Mis Cursos** (`/mis-cursos`): crea cursos (genera un código de inscripción de 8 caracteres), gestiona sus exámenes y ve la analítica de cada curso.

### Estudiante
- **Mis Cursos** (`/mis-cursos`): se inscribe a cursos con el código del docente, rinde exámenes generados por IA, ve su progreso y puede reportar un examen problemático (ícono de bandera en la card del examen).

## Comandos útiles de Docker Compose

```bash
# Ver logs en vivo de un servicio
docker compose logs -f web
docker compose logs -f ml

# Ejecutar un comando de Django dentro del contenedor
docker compose exec web python manage.py <comando>

# Crear una migración tras cambiar un modelo
docker compose exec web python manage.py makemigrations

# Reconstruir solo un servicio (por ejemplo, tras cambiar el frontend)
docker compose up --build -d frontend

# Detener todo (conserva los datos de Postgres)
docker compose down

# Detener todo y borrar también los datos de la base de datos
docker compose down -v
```

## Desarrollo sin Docker (opcional)

Cada subproyecto puede correr de forma independiente durante el desarrollo:

```bash
# Backend (requiere Postgres accesible en localhost, ver DB_HOST/DB_PORT en .env)
cd backend_lairn
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd Lairn_Frontend
npm install
npm run dev

# Microservicio ML
cd microservicio_ml
pip install -r requirements/api.txt
uvicorn app.main:app --reload --port 8001
```

## Estructura del repositorio

```
Monorepo_Lairn/
├── docker-compose.yml       # orquesta db + web + ml + frontend
├── backend_lairn/           # Django + DRF — API REST
│   ├── apps/                #   users, examenes, motor_adaptativo, analitica, moderacion
│   └── docs/                #   documentación detallada del backend (ver abajo)
├── Lairn_Frontend/          # React + Vite + TypeScript
│   └── src/pages/           #   páginas por rol: dashboard, cursos, examenes, usuarios, analitica, moderacion, redes
└── microservicio_ml/        # FastAPI — Knowledge Tracing (BKT/DKT)
    ├── app/                 #   servicio que corre en producción
    ├── ml/                  #   entrenamiento e investigación (notebooks)
    └── artefactos/          #   modelos entrenados (.pkl)
```

## Documentación adicional

- [`backend_lairn/docs/`](backend_lairn/docs/) — arquitectura, autenticación, base de datos, endpoints, motor de IA, variables de entorno, comandos de gestión, seguridad.
- [`microservicio_ml/README.md`](microservicio_ml/README.md) — modelos servidos, API `/predict`, cómo re-entrenar.

## Solución de problemas

- **Puerto ocupado**: si `5173`, `8000` o `8002` ya están en uso, cambia el mapeo de puertos en `docker-compose.yml` (`"host:contenedor"`).
- **El backend no arranca / error de variables de entorno**: verifica que `backend_lairn/.env` exista y tenga `SECRET_KEY` y `OPENAI_API_KEY` completos.
- **Cambios en el código no se reflejan**: el backend usa `StatReloader` y recarga solo; el frontend está compilado en la imagen de `nginx`, así que tras editar código hay que reconstruir con `docker compose up --build -d frontend`.
- **Reiniciar todo desde cero** (borra la base de datos):
  ```bash
  docker compose down -v
  docker compose up --build -d
  docker compose exec web python manage.py seed_roles
  docker compose exec web python manage.py seed_usuarios
  ```
