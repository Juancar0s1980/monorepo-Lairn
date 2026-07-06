# Autenticacion y Endpoints de la API

LAIRN usa JWT (JSON Web Tokens) para autenticacion. Todos los endpoints protegidos requieren enviar el `access` token en el header `Authorization`.

---

## Como autenticarse

### 1. Iniciar sesion

```http
POST /api/usuarios/iniciar-sesion/
Content-Type: application/json

{
  "email": "docente@pseudotutor.com",
  "password": "docente1234"
}
```

Respuesta exitosa (`200 OK`):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "rol": "Docente"
}
```

### 2. Usar el token en cada peticion

```http
GET /api/usuarios/mis-datos/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 3. Renovar el token

El `access` token expira en **5 minutos**. Usa el `refresh` token para obtener uno nuevo:

```http
POST /api/usuarios/token/actualizar/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Respuesta:
```json
{
  "access": "nuevo-access-token..."
}
```

El `refresh` token expira en **24 horas**.

---

## Roles del sistema

| Rol | Descripcion |
|-----|-------------|
| `Administrador` | Acceso total a la plataforma |
| `Docente` | Crea cursos, examenes y ve analitica de sus cursos |
| `Estudiante` | Se inscribe a cursos y toma examenes |

---

## Todos los endpoints de la API

### Usuarios (`/api/usuarios/`)

| Metodo | Endpoint | Descripcion | Acceso |
|--------|----------|-------------|--------|
| `POST` | `/api/usuarios/registrar/` | Registrar nuevo estudiante | Publico |
| `POST` | `/api/usuarios/iniciar-sesion/` | Login, retorna tokens JWT | Publico |
| `POST` | `/api/usuarios/cerrar-sesion/` | Logout (invalida refresh token) | Autenticado |
| `GET` | `/api/usuarios/mis-datos/` | Ver datos del usuario actual | Autenticado |
| `POST` | `/api/usuarios/token/actualizar/` | Renovar access token | Autenticado |

---

### Cursos y Examenes (`/api/examenes/`)

| Metodo | Endpoint | Descripcion | Acceso |
|--------|----------|-------------|--------|
| `POST` | `/api/examenes/cursos/` | Crear un nuevo curso | Docente |
| `GET` | `/api/examenes/cursos/` | Listar mis cursos | Docente |
| `POST` | `/api/examenes/examenes/` | Crear examen en un curso | Docente |
| `POST` | `/api/examenes/inscribirse/` | Inscribirse a un curso por codigo | Estudiante |
| `GET` | `/api/examenes/cursos/<id>/estudiantes/` | Ver estudiantes inscritos | Docente |
| `DELETE` | `/api/examenes/cursos/<id>/estudiantes/` | Eliminar estudiante del curso | Docente |

#### Ejemplo: Crear curso

```http
POST /api/examenes/cursos/
Authorization: Bearer <token-docente>
Content-Type: application/json

{
  "nombre": "Calculo I",
  "descripcion": "Limites, derivadas e integrales"
}
```

Respuesta (`201 Created`):
```json
{
  "id": 1,
  "nombre": "Calculo I",
  "descripcion": "Limites, derivadas e integrales",
  "codigo": "AB3X9KLM",
  "docente": "Juan Perez",
  "creado_en": "2024-01-15T10:30:00Z"
}
```

#### Ejemplo: Crear examen

```http
POST /api/examenes/examenes/
Authorization: Bearer <token-docente>
Content-Type: application/json

{
  "curso": 1,
  "titulo": "Examen de Derivadas",
  "tema": "Derivadas de funciones trigonometricas",
  "tiempo": 30,
  "num_preguntas": 10,
  "retroalimentacion": true,
  "dificultad_inicial": 1,
  "max_intentos": 3,
  "es_guiado": false,
  "modo": "fijo"
}
```

#### Ejemplo: Inscribirse a un curso

```http
POST /api/examenes/inscribirse/
Authorization: Bearer <token-estudiante>
Content-Type: application/json

{
  "codigo": "AB3X9KLM"
}
```

---

### Motor Adaptativo (`/api/motor-adaptativo/`)

| Metodo | Endpoint | Descripcion | Acceso |
|--------|----------|-------------|--------|
| `POST` | `/api/motor-adaptativo/iniciar/` | Iniciar o reanudar un examen | Estudiante |
| `POST` | `/api/motor-adaptativo/<sesion_id>/responder/` | Enviar respuesta y obtener siguiente pregunta | Estudiante |

#### Ejemplo: Iniciar examen

```http
POST /api/motor-adaptativo/iniciar/
Authorization: Bearer <token-estudiante>
Content-Type: application/json

{
  "examen_id": 1
}
```

Respuesta (primera pregunta generada por IA):
```json
{
  "sesion_id": 42,
  "estado": "en_progreso",
  "pregunta_actual": {
    "concepto": "derivada de seno",
    "pregunta": "¿Cual es la derivada de f(x) = sen(x)?",
    "opciones": ["cos(x)", "-cos(x)", "sen(x)", "-sen(x)"],
    "es_guiado": false
  },
  "preguntas_respondidas": 0,
  "dificultad_actual": 1
}
```

#### Ejemplo: Responder pregunta

```http
POST /api/motor-adaptativo/42/responder/
Authorization: Bearer <token-estudiante>
Content-Type: application/json

{
  "respuesta": "cos(x)"
}
```

Respuesta (siguiente pregunta):
```json
{
  "sesion_id": 42,
  "estado": "en_progreso",
  "es_correcta": true,
  "pregunta_actual": {
    "concepto": "derivada de coseno",
    "pregunta": "¿Cual es la derivada de g(x) = cos(x)?",
    "opciones": ["-sen(x)", "sen(x)", "cos(x)", "-cos(x)"],
    "es_guiado": false
  },
  "preguntas_respondidas": 1,
  "dificultad_actual": 2
}
```

Respuesta cuando el examen termina:
```json
{
  "sesion_id": 42,
  "estado": "completado",
  "es_correcta": true,
  "completado": true,
  "puntaje": 80.0,
  "nota": 4.2,
  "correctas": 8,
  "total_preguntas": 10
}
```

---

### Analitica (`/api/analitica/`)

| Metodo | Endpoint | Descripcion | Acceso |
|--------|----------|-------------|--------|
| `GET` | `/api/analitica/mis-resultados/` | Ver mis resultados de examenes | Estudiante |
| `GET` | `/api/analitica/curso/<id>/resumen/` | Resumen general del curso | Docente |
| `GET` | `/api/analitica/curso/<id>/patrones/` | Patrones de aprendizaje del curso | Docente |
| `GET` | `/api/analitica/curso/<id>/resultados/` | Todos los resultados del curso | Docente |
| `GET` | `/api/analitica/curso/<id>/estudiante/<id>/` | Avance de un estudiante especifico | Docente |
| `GET` | `/api/analitica/curso/<id>/estudiante/<id>/conocimiento/` | Mapa de conocimiento del estudiante | Docente |

#### Ejemplo: Mis resultados (estudiante)

```http
GET /api/analitica/mis-resultados/
Authorization: Bearer <token-estudiante>
```

Respuesta:
```json
[
  {
    "examen": "Examen de Derivadas",
    "curso": "Calculo I",
    "puntaje": 80.0,
    "nota": 4.2,
    "correctas": 8,
    "total_preguntas": 10,
    "completado_en": "2024-01-15T11:05:00Z"
  }
]
```

#### Ejemplo: Mapa de conocimiento de un estudiante

```http
GET /api/analitica/curso/1/estudiante/5/conocimiento/
Authorization: Bearer <token-docente>
```

Respuesta:
```json
{
  "estudiante": "Ana Garcia",
  "examen": "Examen de Derivadas",
  "conceptos": {
    "derivada de seno": { "intentos": 3, "correctas": 3, "nivel": 3 },
    "derivada de coseno": { "intentos": 2, "correctas": 1, "nivel": 1 },
    "regla de la cadena": { "intentos": 4, "correctas": 2, "nivel": 2 }
  },
  "actualizado_en": "2024-01-15T11:05:00Z"
}
```

---

## Tabla de permisos por endpoint

| Endpoint | Publico | Estudiante | Docente | Admin |
|----------|---------|------------|---------|-------|
| `POST /registrar/` | ✓ | ✓ | ✓ | ✓ |
| `POST /iniciar-sesion/` | ✓ | ✓ | ✓ | ✓ |
| `GET /mis-datos/` | — | ✓ | ✓ | ✓ |
| `POST /cursos/` | — | — | ✓ | ✓ |
| `POST /inscribirse/` | — | ✓ | — | ✓ |
| `POST /motor-adaptativo/iniciar/` | — | ✓ | — | ✓ |
| `GET /analitica/mis-resultados/` | — | ✓ | — | ✓ |
| `GET /analitica/curso/<id>/resumen/` | — | — | ✓ | ✓ |
