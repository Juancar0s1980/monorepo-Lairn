# Inicio Rapido

De cero a servidor corriendo en menos de 5 minutos usando Docker.

## 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd backend_lairn
```

## 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y completa al menos estas variables:

```env
SECRET_KEY=una-clave-secreta-larga-y-aleatoria
DEBUG=True
OPENAI_API_KEY=sk-...          # Obligatoria para generar preguntas
```

Ver todas las variables disponibles en [VARIABLES_ENTORNO.md](VARIABLES_ENTORNO.md).

## 3. Levantar con Docker

```bash
docker-compose up --build
```

Esto levanta dos servicios: la base de datos PostgreSQL y el servidor Django. Las migraciones se ejecutan automaticamente al iniciar.

## 4. Crear roles y usuarios de prueba

En otra terminal:

```bash
docker-compose exec web python manage.py seed_roles
docker-compose exec web python manage.py seed_usuarios
```

## 5. Verificar que funciona

```bash
curl http://localhost:8000/api/docs/
```

O abre http://localhost:8000/api/docs/ en el navegador para ver la documentacion interactiva de Swagger.

---

## Usuarios de prueba disponibles

| Email | Contrasena | Rol |
|-------|------------|-----|
| admin@pseudotutor.com | admin1234 | Administrador |
| docente@pseudotutor.com | docente1234 | Docente |
| estudiante@pseudotutor.com | estudiante1234 | Estudiante |

---

## Flujo minimo de prueba

### 1. Login como docente

```bash
curl -X POST http://localhost:8000/api/usuarios/iniciar-sesion/ \
  -H "Content-Type: application/json" \
  -d '{"email": "docente@pseudotutor.com", "password": "docente1234"}'
```

Guarda el `access` token de la respuesta.

### 2. Crear un curso

```bash
curl -X POST http://localhost:8000/api/examenes/cursos/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Matematicas", "descripcion": "Algebra basica"}'
```

Guarda el `codigo` del curso de la respuesta.

### 3. Login como estudiante e inscribirse

```bash
curl -X POST http://localhost:8000/api/usuarios/iniciar-sesion/ \
  -H "Content-Type: application/json" \
  -d '{"email": "estudiante@pseudotutor.com", "password": "estudiante1234"}'

curl -X POST http://localhost:8000/api/examenes/inscribirse/ \
  -H "Authorization: Bearer <token-estudiante>" \
  -H "Content-Type: application/json" \
  -d '{"codigo": "<codigo-del-curso>"}'
```

### 4. Iniciar un examen

```bash
curl -X POST http://localhost:8000/api/motor-adaptativo/iniciar/ \
  -H "Authorization: Bearer <token-estudiante>" \
  -H "Content-Type: application/json" \
  -d '{"examen_id": 1}'
```

La respuesta contiene la primera pregunta generada por IA.

---

## Detener el servidor

```bash
docker-compose down
```

Para eliminar tambien los datos de la base de datos:

```bash
docker-compose down -v
```
