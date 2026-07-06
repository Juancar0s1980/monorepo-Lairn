# Instalacion Local (sin Docker)

Guia para levantar LAIRN directamente en tu maquina con Python y PostgreSQL.

## Requisitos del sistema

- Python 3.12
- PostgreSQL 16
- pip
- Git

---

## 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd backend_lairn
```

## 2. Crear entorno virtual

```bash
python -m venv venv
```

Activar el entorno:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Linux / Mac:**
  ```bash
  source venv/bin/activate
  ```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4. Configurar PostgreSQL

Crear la base de datos y el usuario en PostgreSQL:

```sql
CREATE DATABASE lairn_db;
CREATE USER lairn_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE lairn_db TO lairn_user;
```

## 5. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con los valores correctos para tu entorno local:

```env
SECRET_KEY=una-clave-secreta-larga
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=lairn_db
DB_USER=lairn_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

OPENAI_API_KEY=sk-...
```

Ver la descripcion completa de cada variable en [VARIABLES_ENTORNO.md](VARIABLES_ENTORNO.md).

## 6. Aplicar migraciones

```bash
python manage.py migrate
```

## 7. Crear roles y usuarios iniciales

```bash
python manage.py seed_roles
python manage.py seed_usuarios
```

## 8. Levantar el servidor

```bash
python manage.py runserver
```

El servidor estara disponible en http://localhost:8000.

---

## Verificar la instalacion

Abre http://localhost:8000/api/docs/ en el navegador. Si ves la documentacion de Swagger, la instalacion fue exitosa.

---

## Crear un superusuario (opcional)

Si necesitas acceso al panel de administracion de Django:

```bash
python manage.py createsuperuser
```

El panel estara disponible en http://localhost:8000/admin/.

---

## Posibles errores comunes

| Error | Causa probable | Solucion |
|-------|---------------|----------|
| `django.db.utils.OperationalError` | PostgreSQL no esta corriendo | Iniciar el servicio de PostgreSQL |
| `ModuleNotFoundError` | Dependencias no instaladas | Ejecutar `pip install -r requirements.txt` |
| `OPENAI_API_KEY no configurada` | Falta la variable en `.env` | Agregar la clave al archivo `.env` |
| Error de migraciones | Base de datos no creada | Verificar credenciales en `.env` y crear la DB |
