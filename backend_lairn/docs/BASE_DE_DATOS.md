# Base de Datos

LAIRN usa **PostgreSQL 16** como base de datos principal. Los modelos estan organizados en 4 apps: `users`, `examenes`, `motor_adaptativo` y `analitica`.

---

## Diagrama de relaciones

```
┌──────────┐         ┌──────────────┐
│   Role   │────────►│     User     │
│──────────│  n:1    │──────────────│
│ id       │         │ id           │
│ name     │         │ email        │
└──────────┘         │ first_name   │
                     │ second_name  │
                     │ first_last   │
                     │ second_last  │
                     │ role (FK)    │
                     │ is_active    │
                     └──────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   ┌──────────┐      ┌────────────┐   ┌──────────────┐
   │  Curso   │      │Inscripcion │   │SesionExamen  │
   │──────────│      │────────────│   │──────────────│
   │ id       │      │ id         │   │ id           │
   │ nombre   │      │ estudiante │   │ estudiante   │
   │ descripcion│    │ curso (FK) │   │ examen (FK)  │
   │ docente  │      │ fecha      │   │ intento      │
   │ codigo   │      └────────────┘   │ dificultad   │
   │ creado_en│                       │ preg_respondidas│
   └────┬─────┘                       │ pregunta_actual│
        │                             │ estado       │
        ▼                             │ iniciado_en  │
   ┌──────────┐                       │ completado_en│
   │  Examen  │                       └──────┬───────┘
   │──────────│                              │
   │ id       │                    ┌─────────┴──────────┐
   │ curso    │                    │                    │
   │ titulo   │                    ▼                    ▼
   │ tema     │             ┌────────────┐    ┌──────────────────┐
   │ tiempo   │             │  Resultado │    │ModeloConocimiento│
   │ num_preg │             │────────────│    │──────────────────│
   │ retro... │             │ id         │    │ id               │
   │ dif_ini  │             │ sesion     │    │ estudiante       │
   │ max_int  │             │ estudiante │    │ examen           │
   │ es_guiado│             │ examen     │    │ conceptos (JSON) │
   │ modo     │             │ puntaje    │    │ actualizado_en   │
   │ max_preg │             │ nota       │    └──────────────────┘
   └──────────┘             │ total_preg │
                            │ correctas  │
                            │ completado │
                            └─────┬──────┘
                                  │
                                  ▼
                         ┌─────────────────────┐
                         │  RespuestaEstudiante │
                         │─────────────────────│
                         │ id                  │
                         │ resultado (FK)      │
                         │ concepto            │
                         │ pregunta            │
                         │ respuesta_correcta  │
                         │ respuesta_incorrecta│
                         │ tiempo_por_pregunta │
                         │ dificultad          │
                         └─────────────────────┘
```

---

## Detalle de cada modelo

### Role (`apps/users/models/role.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `name` | CharField (unique) | Nombre del rol |

Valores predefinidos: `Administrador`, `Docente`, `Estudiante`

---

### User (`apps/users/models/user.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `email` | EmailField (unique) | Identificador unico de login |
| `first_name` | CharField | Primer nombre |
| `second_name` | CharField | Segundo nombre (opcional) |
| `first_last_name` | CharField | Primer apellido |
| `second_last_name` | CharField | Segundo apellido (opcional) |
| `role` | FK → Role | Rol del usuario |
| `is_active` | BooleanField | Si la cuenta esta activa |
| `is_staff` | BooleanField | Acceso al admin de Django |

> El campo `USERNAME_FIELD` esta configurado como `email`, no como `username`.

---

### Curso (`apps/examenes/models/curso.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `nombre` | CharField | Nombre del curso |
| `descripcion` | TextField | Descripcion del curso |
| `docente` | FK → User | Docente propietario |
| `codigo` | CharField(8, unique) | Codigo de acceso para estudiantes |
| `creado_en` | DateTimeField | Fecha de creacion (auto) |

---

### Examen (`apps/examenes/models/examen.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `curso` | FK → Curso | Curso al que pertenece |
| `titulo` | CharField | Titulo del examen |
| `tema` | CharField | Tema sobre el cual la IA genera preguntas |
| `tiempo` | IntegerField | Duracion en minutos |
| `num_preguntas` | IntegerField | Numero de preguntas (o minimo en modo maestria) |
| `retroalimentacion` | BooleanField | Si muestra si la respuesta fue correcta |
| `dificultad_inicial` | IntegerField (1-3) | Dificultad de la primera pregunta |
| `max_intentos` | IntegerField | Intentos maximos (0 = ilimitado) |
| `es_guiado` | BooleanField | Si incluye explicacion antes de cada pregunta |
| `modo` | CharField | `fijo` o `maestria` |
| `max_preguntas` | IntegerField | Maximo de preguntas (solo modo maestria) |

---

### Inscripcion (`apps/examenes/models/inscripcion.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `estudiante` | FK → User | Estudiante inscrito |
| `curso` | FK → Curso | Curso al que se inscribio |
| `fecha` | DateTimeField | Fecha de inscripcion (auto) |

Restriccion: `unique_together(estudiante, curso)` — un estudiante solo puede inscribirse una vez por curso.

---

### SesionExamen (`apps/motor_adaptativo/models/sesion_examen.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `estudiante` | FK → User | Estudiante que toma el examen |
| `examen` | FK → Examen | Examen que se esta tomando |
| `intento` | IntegerField | Numero de intento (1, 2, 3...) |
| `dificultad_actual` | IntegerField (1-3) | Dificultad de la proxima pregunta |
| `preguntas_respondidas` | IntegerField | Contador de respuestas dadas |
| `pregunta_actual` | JSONField | Pregunta generada por IA (objeto JSON) |
| `estado` | CharField | `en_progreso` o `completado` |
| `iniciado_en` | DateTimeField | Cuando empezo la sesion |
| `completado_en` | DateTimeField | Cuando termino (null si esta activa) |

Restriccion: `unique_together(estudiante, examen, intento)`

#### Estructura de `pregunta_actual`

```json
{
  "concepto": "derivada de seno",
  "pregunta": "¿Cual es la derivada de sen(x)?",
  "opciones": ["cos(x)", "-cos(x)", "sen(x)", "-sen(x)"],
  "respuesta_correcta": "cos(x)",
  "explicacion": "La derivada de sen(x) es cos(x)..."
}
```

El campo `explicacion` solo aparece cuando `es_guiado=True`.

---

### ModeloConocimiento (`apps/motor_adaptativo/models/modelo_conocimiento.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `estudiante` | FK → User | Estudiante |
| `examen` | FK → Examen | Examen al que corresponde |
| `conceptos` | JSONField | Mapa de dominio por concepto |
| `actualizado_en` | DateTimeField | Ultima actualizacion (auto) |

Restriccion: `unique_together(estudiante, examen)`

#### Estructura de `conceptos`

```json
{
  "derivada de seno": {
    "intentos": 5,
    "correctas": 4,
    "nivel": 3
  },
  "derivada de coseno": {
    "intentos": 3,
    "correctas": 1,
    "nivel": 1
  }
}
```

Niveles: `1` = Debil, `2` = En desarrollo, `3` = Dominado

---

### Resultado (`apps/analitica/models/resultado.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `sesion` | OneToOneField → SesionExamen | Sesion que genero este resultado |
| `estudiante` | FK → User | Estudiante |
| `examen` | FK → Examen | Examen |
| `puntaje` | FloatField (0-100) | Porcentaje de aciertos |
| `nota` | FloatField (1.0-5.0) | Calificacion final |
| `total_preguntas` | IntegerField | Total de preguntas respondidas |
| `correctas` | IntegerField | Respuestas correctas |
| `completado_en` | DateTimeField | Cuando se genero el resultado |

Formula de nota: `1.0 + (correctas / total) * 4.0`

---

### RespuestaEstudiante (`apps/analitica/models/respuesta_estudiante.py`)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `id` | AutoField | PK |
| `resultado` | FK → Resultado | Resultado al que pertenece |
| `concepto` | CharField | Concepto evaluado |
| `pregunta` | TextField | Texto de la pregunta |
| `respuesta_correcta` | CharField | La respuesta correcta |
| `respuesta_incorrecta` | CharField | La respuesta dada (si fue incorrecta, null si fue correcta) |
| `tiempo_por_pregunta` | IntegerField | Segundos que tomo responder |
| `dificultad` | IntegerField (1-3) | Dificultad de la pregunta |

---

## Comandos de migracion

```bash
# Aplicar migraciones pendientes
python manage.py migrate

# Crear nuevas migraciones despues de cambiar modelos
python manage.py makemigrations

# Ver el estado de las migraciones
python manage.py showmigrations

# Con Docker
docker-compose exec web python manage.py migrate
```
