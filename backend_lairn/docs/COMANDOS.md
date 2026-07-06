# Comandos de Referencia

Todos los comandos que necesitas en el dia a dia para trabajar con LAIRN.

---

## Docker

### Levantar el proyecto

```bash
# Primera vez (construye la imagen)
docker-compose up --build

# Veces siguientes
docker-compose up

# En segundo plano
docker-compose up -d
```

### Detener el proyecto

```bash
# Detener contenedores (conserva los datos)
docker-compose down

# Detener y eliminar volumenes (borra la base de datos)
docker-compose down -v
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs

# Solo el servidor web
docker-compose logs web

# En tiempo real
docker-compose logs -f web
```

### Ejecutar comandos dentro del contenedor

```bash
# Abrir shell dentro del contenedor web
docker-compose exec web bash

# Ejecutar un comando de Django directamente
docker-compose exec web python manage.py <comando>
```

### Reconstruir la imagen

```bash
# Util cuando cambias requirements.txt o el Dockerfile
docker-compose build
docker-compose up
```

---

## Django (local o dentro de Docker)

### Migraciones

```bash
# Aplicar migraciones pendientes
python manage.py migrate

# Crear nuevas migraciones despues de cambiar modelos
python manage.py makemigrations

# Ver estado de todas las migraciones
python manage.py showmigrations

# Crear migraciones solo para una app especifica
python manage.py makemigrations users
python manage.py makemigrations examenes
python manage.py makemigrations motor_adaptativo
python manage.py makemigrations analitica
```

### Comandos personalizados

```bash
# Crear los 3 roles base (Administrador, Docente, Estudiante)
python manage.py seed_roles

# Crear usuarios de prueba (requiere seed_roles primero)
python manage.py seed_usuarios
```

### Administracion

```bash
# Crear superusuario para acceder al panel de admin
python manage.py createsuperuser

# Levantar servidor de desarrollo
python manage.py runserver

# Levantar en puerto especifico
python manage.py runserver 0.0.0.0:8000

# Shell interactivo de Django (para consultas rapidas a la BD)
python manage.py shell
```

### Utilidades

```bash
# Ver todas las rutas registradas en el sistema
python manage.py show_urls

# Limpiar todos los datos de la base de datos (mantiene la estructura)
python manage.py flush

# Revertir una migracion especifica
python manage.py migrate <app_name> <numero_anterior>
# Ejemplo: python manage.py migrate examenes 0002
```

---

## Con Docker (equivalencias)

Todos los comandos de Django se pueden ejecutar en Docker con el prefijo:

```bash
docker-compose exec web python manage.py <comando>
```

Ejemplos rapidos:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_roles
docker-compose exec web python manage.py seed_usuarios
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

---

## Accesos en el navegador

Una vez levantado el servidor:

| Recurso | URL |
|---------|-----|
| Swagger (API docs interactiva) | http://localhost:8000/api/docs/ |
| ReDoc (API docs alternativa) | http://localhost:8000/api/redoc/ |
| OpenAPI JSON | http://localhost:8000/api/schema/ |
| Panel de administracion | http://localhost:8000/admin/ |

---

## Usuarios de prueba

| Email | Contrasena | Rol |
|-------|------------|-----|
| admin@pseudotutor.com | admin1234 | Administrador |
| docente@pseudotutor.com | docente1234 | Docente |
| estudiante@pseudotutor.com | estudiante1234 | Estudiante |

---

## Probar la API con curl

### Login

```bash
curl -X POST http://localhost:8000/api/usuarios/iniciar-sesion/ \
  -H "Content-Type: application/json" \
  -d '{"email": "docente@pseudotutor.com", "password": "docente1234"}'
```

### Peticion autenticada

```bash
curl http://localhost:8000/api/usuarios/mis-datos/ \
  -H "Authorization: Bearer <token>"
```

### Crear curso

```bash
curl -X POST http://localhost:8000/api/examenes/cursos/ \
  -H "Authorization: Bearer <token-docente>" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Curso", "descripcion": "Descripcion del curso"}'
```

### Inscribirse a un curso

```bash
curl -X POST http://localhost:8000/api/examenes/inscribirse/ \
  -H "Authorization: Bearer <token-estudiante>" \
  -H "Content-Type: application/json" \
  -d '{"codigo": "AB3X9KLM"}'
```

### Iniciar un examen

```bash
curl -X POST http://localhost:8000/api/motor-adaptativo/iniciar/ \
  -H "Authorization: Bearer <token-estudiante>" \
  -H "Content-Type: application/json" \
  -d '{"examen_id": 1}'
```

### Responder una pregunta

```bash
curl -X POST http://localhost:8000/api/motor-adaptativo/1/responder/ \
  -H "Authorization: Bearer <token-estudiante>" \
  -H "Content-Type: application/json" \
  -d '{"respuesta": "cos(x)"}'
```
