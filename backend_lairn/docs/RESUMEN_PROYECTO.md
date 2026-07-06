# Resumen del Proyecto

## ¿Que es LAIRN?

LAIRN es una plataforma de aprendizaje adaptativo. Su propuesta central es simple: en lugar de dar a todos los estudiantes las mismas preguntas en el mismo orden, el sistema genera preguntas personalizadas en tiempo real usando inteligencia artificial, ajustando la dificultad segun el rendimiento de cada estudiante.

---

## El problema que resuelve

Los examenes tradicionales son estaticos: todos los estudiantes responden las mismas preguntas, independientemente de su nivel. Esto significa que un estudiante que ya domina un tema sigue respondiendo preguntas faciles, y uno que tiene dificultades nunca recibe el refuerzo que necesita.

LAIRN resuelve esto con un motor adaptativo que:
- Genera preguntas nuevas para cada sesion usando IA (no un banco de preguntas fijo).
- Sube la dificultad cuando el estudiante acierta y la baja cuando falla.
- Identifica que conceptos domina y cuales necesita reforzar.
- Puede continuar el examen hasta que el estudiante realmente domine el tema (modo maestria).

---

## Los dos actores principales

### Docente
1. Crea un curso y obtiene un codigo unico de acceso.
2. Define uno o mas examenes: tema, duracion, numero de preguntas, modo (fijo o maestria), dificultad inicial.
3. Comparte el codigo con sus estudiantes.
4. Ve dashboards de analitica: cuantos aprobaron, que conceptos son mas dificiles para el grupo, el mapa de conocimiento individual de cada estudiante.

### Estudiante
1. Se registra e ingresa con su email.
2. Se inscribe al curso usando el codigo del docente.
3. Inicia el examen: el sistema le presenta la primera pregunta generada por IA.
4. Responde pregunta a pregunta. Cada respuesta ajusta la dificultad de la siguiente.
5. Al terminar recibe su puntaje, nota y un resumen de que conceptos domina.

---

## Modos de examen

### Modo Fijo
El examen tiene un numero exacto de preguntas. Cuando el estudiante responde todas, el examen termina y se calcula la nota. Ideal para evaluaciones sumativas.

### Modo Maestria
El examen no tiene un numero fijo de preguntas: termina cuando el estudiante demuestra dominio de todos los conceptos (o alcanza un maximo de preguntas definido). Ideal para practica y refuerzo.

---

## Stack tecnologico

| Componente | Tecnologia | Version |
|-----------|-----------|---------|
| Framework web | Django + Django REST Framework | 6.0.4 / 3.17.1 |
| Lenguaje | Python | 3.12 |
| Base de datos | PostgreSQL | 16 |
| Autenticacion | JWT (SimpleJWT) | 5.5.1 |
| Generacion de preguntas (IA) | GPT-4o Mini (OpenAI) | — |
| Documentacion API | DRF Spectacular (Swagger) | 0.29.0 |
| Contenedores | Docker + Docker Compose | — |

---

## Flujo tecnico simplificado

```
Estudiante inicia examen
        ↓
API verifica inscripcion y crea SesionExamen
        ↓
Llama a Claude Haiku con: tema, dificultad actual, historial de preguntas, conceptos debiles
        ↓
Claude genera pregunta de opcion multiple en JSON
        ↓
Estudiante responde → API evalua
        ↓
Actualiza ModeloConocimiento (nivel por concepto)
Ajusta dificultad (sube si acierta, baja si falla)
        ↓
Genera siguiente pregunta con Claude (repite)
        ↓
Al terminar: crea Resultado con puntaje y nota
```

---

## Apps del sistema

| App | Funcion |
|-----|---------|
| `users` | Registro, login, roles (Administrador, Docente, Estudiante) |
| `examenes` | Cursos, examenes, inscripciones |
| `motor_adaptativo` | Motor de examenes con IA, sesiones, modelo de conocimiento |
| `analitica` | Resultados, avance por estudiante, patrones del curso |
| `moderacion` | Pendiente de implementacion |

---

## Que hace unico a LAIRN

- Las preguntas se generan en el momento, no provienen de un banco. Cada sesion es diferente.
- El sistema conoce el estado de conocimiento de cada estudiante concepto a concepto.
- En modo guiado, Claude tambien genera una explicacion corta antes de cada pregunta.
- Los docentes pueden ver exactamente en que conceptos falla cada estudiante, no solo su nota final.
