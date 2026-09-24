# Monorepo Lairn (PseudoTutor)

Plataforma de exámenes adaptativos con generación de preguntas por IA y Knowledge Tracing (BKT).
Cuatro servicios propios + PostgreSQL, orquestados por el `docker-compose.yml` de la raíz. Ejecutar siempre desde la raíz del repo.

## Servicios y cómo corren

| Servicio | Carpeta | Stack | Host→contenedor | ¿Recarga sin rebuild? |
|----------|---------|-------|-----------------|----------------------|
| `db` | — | PostgreSQL 16 | — | — |
| `web` | `backend_lairn/` | Django 6 + DRF + SimpleJWT | 8000 | Sí (volumen montado + StatReloader) |
| `ml` | `microservicio_ml/` | FastAPI (BKT) | 8002→8001 | No |
| `ejecutor` | `microservicio_ejecutor/` | FastAPI (sandbox) | **no expuesto al host** | No |
| `frontend` | `Lairn_Frontend/` | React+Vite+TS, servido por nginx | 5173→80 | No |

- Nombres de la red interna de compose: `web:8000`, `ml:8001`, `ejecutor:8003`, `db:5432`.
- `ML_SERVICE_URL` y `EJECUTOR_SERVICE_URL` las inyecta el docker-compose raíz (los defaults del `.env` apuntan a esos nombres internos); no las cambies.
- `ejecutor` es el **único** servicio con el socket de Docker del host (`/var/run/docker.sock`): construye sus imágenes runner al arrancar y lanza un contenedor efímero por ejecución de código. No publica puerto a propósito. Sin Docker daemon, no arranca.

## Puesta en marcha

```bash
cp backend_lairn/.env.example backend_lairn/.env   # completar SECRET_KEY y OPENAI_API_KEY
docker compose up --build -d
docker compose exec web python manage.py seed_roles
docker compose exec web python manage.py seed_usuarios   # requiere seed_roles previo
```

- Las migraciones corren automáticamente al arrancar `web`.
- Cuentas seed reales (`apps/users/management/commands/seed_usuarios.py`): `admin@pseudotutor.com`/`Admin1234*`, `docente@pseudotutor.com`/`Docente1234*`, `estudiante@pseudotutor.com`/`Estudiante1234*`.
  **Alto riesgo:** `backend_lairn/README.md` y `docs/COMANDOS.md` muestran contraseñas en minúscula (`admin1234`) que están desactualizadas.
- Verificar: `docker compose ps` (db/ml/ejecutor con healthcheck) y URLs http://localhost:5173, /api/docs/ (Swagger), /admin/.

## Cambios según servicio

- Backend: se refleja solo (volumen). Frontend, `ml` y `ejecutor` requieren `docker compose up --build -d <servicio>`.
- El frontend "hornea" `VITE_API_URL=/api` en build-time; nginx proxya `/api/` y `/media/` a `web:8000`. Editar el frontend sin reconstruir no surte efecto contra el contenedor.
- Puertos ocupados: se cambian en el `docker-compose.yml` de la raíz (ej. host 8002→contenedor 8001 del `ml`).

## Frontend

El detalle vive en `Lairn_Frontend/AGENTS.md` (se carga automáticamente). Lo mínimo:
- Comandos (en `Lairn_Frontend/`): `npm run dev`, `npm run build` (= `tsc -b` + `vite build`; TS falla = sin build), `npm run lint`. No hay tests.
- **Los directorios reales son en inglés** (`src/pages/`, `src/services/`, `src/types/`, `src/utilities/`, `src/context/`, `src/hooks/`, `src/app/`). Algunos docs usan `paginas`/`tipos`/`utilidades`/`servicios`/`contextos`: no existen, sigue el código.
- Convenciones: código/comentarios en español, alias `@/*`→`src/`, UI solo con Shadcn (`src/components/ui/`, no editar a mano), sin `enum`, `import type` para tipos, páginas siempre con `lazy()`.

## Backend

- Apps en `backend_lairn/apps/`: `users`, `examenes`, `motor_adaptativo`, `analitica`, `moderacion`, `laboratorios`, `campo_estudio`, `saber_pro`.
- Estructura por app: paquetes `models/`, `views/`, `serializers/`, `migrations/`; vistas como `vista_<accion>.py` registradas en `urls.py` local; permisos por rol en `core/permissions/permisos_rol.py` (`EsAdministrador`, `EsDocente`, `EsEstudiante`).
- Nombrado de dominio en español. Migraciones: `docker compose exec web python manage.py makemigrations <app>`.
- Proveedor de IA configurable con `AI_PROVIDER` (`openai`/`grok`/`groq`); generación de imágenes aparte con Gemini/HF. El cliente del ML (`apps/motor_adaptativo/services/cliente_ml.py`) es resiliente: si el microservicio no responde, cae a heurístico sin romper el examen.
- Docs por feature en `backend_lairn/docs/` (ARQUITECTURA, AUTENTICACION, MOTOR_IA, BASE_DE_DATOS, VARIABLES_ENTORNO, CONTRIBUIR) — son la mejor fuente para endpoints y flujos.

## ML (`microservicio_ml`)

- `app/` (servir, FastAPI, sin torch) vs `ml/` (entrenamiento/notebooks, no entra a la imagen). `requirements/` partido: `api.txt` (servir), `train.txt` (entrenar).
- Modelo default `bkt_sintetico` (único cuyo vocabulario mapea a exámenes reales); cambiar con `ML_MODELO`. Vocabulario en `artefactos/concept_vocab.json`.
- Tests: `cd microservicio_ml; pip install -r requirements/api.txt pytest; pytest` (`tests/test_predictor.py`).
- Si reorganizas `ml/modelos/`, re-guarda los `.pkl` con `python scripts/migrar_artefactos.py`. Más en `microservicio_ml/README.md`.

## Ejecutor (`microservicio_ejecutor`)

- Endpoints: `POST /ejecutar/codigo` (`python|javascript|java|cpp|c`) y `POST /ejecutar/sql` (SQLite en memoria). Límites default: timeout 5s, RAM 128m, 0.5 CPU (ver `app/config.py`).
- Sin README propio; la lógica está en `app/servicios/sandbox.py`. Lo consume `apps/laboratorios/services/cliente_ejecutor.py`.

## Verificación

No hay CI, pre-commit hooks ni tests para backend/frontend/ejecutor (solo el `ml`). "Verificar" = `docker compose build` + `ps` + probar el flujo real; en frontend además `npm run build` / `npm run lint`.
Reset total: `docker compose down -v` y repetir puesta en marcha.