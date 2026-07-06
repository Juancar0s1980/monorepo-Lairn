# Variables de Entorno

Todas las variables que LAIRN necesita para funcionar se configuran en el archivo `.env` en la raiz del proyecto. Usa `.env.example` como plantilla.

```bash
cp .env.example .env
```

---

## Variables de Django

| Variable | Obligatoria | Descripcion | Ejemplo |
|----------|-------------|-------------|---------|
| `SECRET_KEY` | Si | Clave secreta de Django. Debe ser larga, aleatoria y unica por entorno. Nunca compartirla. | `django-insecure-xyz123...` |
| `DEBUG` | Si | Modo de depuracion. Usar `True` solo en desarrollo. En produccion debe ser `False`. | `True` |
| `ALLOWED_HOSTS` | Si | Lista de dominios permitidos separados por coma. En desarrollo puede ser `*`. | `localhost,127.0.0.1` |

---

## Variables de Base de Datos

| Variable | Obligatoria | Descripcion | Ejemplo |
|----------|-------------|-------------|---------|
| `DB_NAME` | Si | Nombre de la base de datos PostgreSQL. | `lairn_db` |
| `DB_USER` | Si | Usuario de PostgreSQL. | `postgres` |
| `DB_PASSWORD` | Si | Contrasena del usuario de PostgreSQL. | `mi_password` |
| `DB_HOST` | Si | Host de la base de datos. Usar `db` con Docker, `localhost` en local. | `db` |
| `DB_PORT` | Si | Puerto de PostgreSQL. El valor por defecto es 5432. | `5432` |

---

## Variables de Inteligencia Artificial

| Variable | Obligatoria | Descripcion | Ejemplo |
|----------|-------------|-------------|---------|
| `OPENAI_API_KEY` | Si | Clave de API de OpenAI para usar GPT-4o Mini. Sin esta clave el motor adaptativo no puede generar preguntas. | `sk-...` |

> **Importante:** Sin `OPENAI_API_KEY` el endpoint `POST /api/motor-adaptativo/iniciar/` y `POST /api/motor-adaptativo/<id>/responder/` fallaran con error 500.

---

## Ejemplo de archivo `.env` completo

```env
# Django
SECRET_KEY=django-insecure-cambia-esto-en-produccion
DEBUG=True
ALLOWED_HOSTS=*

# Base de datos
DB_NAME=lairn_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Anthropic / Claude
OPENAI_API_KEY=sk-...
```

---

## Diferencias entre entornos

### Desarrollo (local o Docker)
```env
DEBUG=True
ALLOWED_HOSTS=*
DB_HOST=localhost   # o "db" si usas Docker Compose
```

### Produccion
```env
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
SECRET_KEY=clave-muy-larga-y-aleatoria-generada-de-forma-segura
```

> En produccion nunca uses `DEBUG=True` ni `ALLOWED_HOSTS=*`. Consulta [SEGURIDAD.md](SEGURIDAD.md) para mas detalles.

---

## Como generar una SECRET_KEY segura

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
