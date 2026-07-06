# Arquitectura del Sistema

## Vision general

LAIRN es una API REST construida en capas. El cliente (aplicacion web o movil) se comunica con Django REST Framework, que delega en apps especializadas. El motor adaptativo consulta a GPT-4o Mini (OpenAI) para generar preguntas personalizadas.

```
┌─────────────────────────────────────────────────┐
│                  Cliente HTTP                    │
│         (web app, movil, Postman, curl)          │
└─────────────────────┬───────────────────────────┘
                      │ HTTPS / JSON
┌─────────────────────▼───────────────────────────┐
│           Django REST Framework (DRF)            │
│   JWT Auth ─── Permisos por Rol ─── Swagger      │
├──────────┬──────────┬──────────┬────────────────┤
│  users   │ examenes │ analitica│ motor_adaptativo│
│          │          │          │                 │
│ registro │  cursos  │resultados│  sesion examen  │
│  login   │ examenes │ avance   │  ← pregunta →   │
│  perfil  │inscripcion│ patrones│  conocimiento   │
└──────────┴──────────┴──────────┴────────┬────────┘
                      │                   │
         ┌────────────▼───┐    ┌──────────▼──────┐
         │  PostgreSQL 16  │    │  GPT-4o Mini   │
         │  (datos perm.)  │    │    (OpenAI)     │
         └────────────────┘    └─────────────────┘
```

---

## Apps y sus responsabilidades

### `users` — Autenticacion y usuarios
Gestiona el registro, login, logout y datos del perfil. Usa email como identificador unico. Asigna roles a cada usuario.

### `examenes` — Cursos y examenes
Permite a los docentes crear cursos (con codigo unico de acceso) y definir examenes con configuracion detallada. Gestiona las inscripciones de estudiantes.

### `motor_adaptativo` — Motor de examenes con IA
El corazon del sistema. Coordina la sesion de examen, llama a GPT-4o Mini para generar cada pregunta, evalua las respuestas, ajusta la dificultad y actualiza el mapa de conocimiento del estudiante.

### `analitica` — Resultados y estadisticas
Almacena los resultados de cada sesion y expone reportes para estudiantes (mis resultados) y docentes (avance del curso, patrones de aprendizaje, mapas de conocimiento por estudiante).

### `moderacion` — Pendiente
Reservado para funcionalidades de moderacion de contenido. Sin implementar.

### `core` — Utilidades compartidas
Contiene los permisos por rol (`EsAdministrador`, `EsDocente`, `EsEstudiante`) y utilidades reutilizables entre apps.

---

## Flujo completo de un examen

```
Estudiante                    API                         GPT-4o Mini
    │                          │                               │
    │  POST /motor-adaptativo/iniciar/                         │
    │─────────────────────────►│                               │
    │                          │  Verifica inscripcion         │
    │                          │  Crea SesionExamen            │
    │                          │  generar_pregunta(tema, dif=1)│
    │                          │──────────────────────────────►│
    │                          │  {"pregunta", "opciones", ... }│
    │                          │◄──────────────────────────────│
    │  {"pregunta_actual": ...}│                               │
    │◄─────────────────────────│                               │
    │                          │                               │
    │  POST /motor-adaptativo/<id>/responder/                  │
    │─────────────────────────►│                               │
    │                          │  Evalua respuesta             │
    │                          │  Actualiza ModeloConocimiento │
    │                          │  Ajusta dificultad            │
    │                          │  generar_pregunta(tema, dif=2)│
    │                          │──────────────────────────────►│
    │                          │  {"pregunta", "opciones", ... }│
    │                          │◄──────────────────────────────│
    │  {"pregunta_actual": ...}│                               │
    │◄─────────────────────────│                               │
    │          ...             │             ...               │
    │                          │                               │
    │  POST /motor-adaptativo/<id>/responder/ (ultima)         │
    │─────────────────────────►│                               │
    │                          │  Crea Resultado               │
    │                          │  Guarda RespuestasEstudiante  │
    │  {"completado": true,    │                               │
    │   "puntaje": 80,         │                               │
    │   "nota": 4.2}           │                               │
    │◄─────────────────────────│                               │
```

---

## Modos de examen

### Modo Fijo
- Se generan exactamente `num_preguntas` preguntas.
- El examen termina cuando el estudiante responde todas.
- Calificacion: `correctas / total * 100`

### Modo Maestria
- Minimo: `num_preguntas` preguntas.
- Maximo: `max_preguntas` preguntas.
- El examen termina cuando el estudiante domina todos los conceptos (nivel 3) o alcanza el maximo de preguntas.
- Favorece la profundidad sobre la cantidad.

---

## Ajuste de dificultad

La dificultad se ajusta despues de cada respuesta:

| Resultado | Dificultad actual | Nueva dificultad |
|-----------|------------------|-----------------|
| Correcta | 1 (Facil) | 2 (Media) |
| Correcta | 2 (Media) | 3 (Dificil) |
| Correcta | 3 (Dificil) | 3 (se mantiene) |
| Incorrecta | 3 (Dificil) | 2 (Media) |
| Incorrecta | 2 (Media) | 1 (Facil) |
| Incorrecta | 1 (Facil) | 1 (se mantiene) |

---

## Modelo de conocimiento

Para cada par (estudiante, examen) se mantiene un JSON con el nivel de dominio por concepto:

```json
{
  "algebra lineal": {
    "intentos": 5,
    "correctas": 4,
    "nivel": 3
  },
  "derivadas": {
    "intentos": 3,
    "correctas": 1,
    "nivel": 1
  }
}
```

Niveles:
- `1` — Debil (menos del 50% de aciertos)
- `2` — En desarrollo (50-79% de aciertos)
- `3` — Dominado (80%+ de aciertos)

Claude prioriza los conceptos con nivel 1 o 2 al generar nuevas preguntas.

---

## Autenticacion

JWT con dos tokens:
- **Access token:** expira en 5 minutos. Se envia en cada peticion.
- **Refresh token:** expira en 24 horas. Se usa para obtener un nuevo access token.

Ver detalles en [AUTENTICACION.md](AUTENTICACION.md).

---

## Decisiones de diseno

| Decision | Razon |
|----------|-------|
| Django REST Framework | Maduro, serializers potentes, integracion con DRF Spectacular para Swagger automatico |
| JWT en lugar de sesiones | API stateless, compatible con clientes web y movil |
| GPT-4o Mini (OpenAI) | Rapido y economico para generacion de preguntas en tiempo real |
| PostgreSQL | Soporte de JSON nativo para `ModeloConocimiento` y `pregunta_actual` |
| Separacion por apps | Permite escalar o reemplazar modulos de forma independiente |
