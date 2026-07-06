# Manejo de Errores

Catalogo de los errores que puede retornar la API, con ejemplos de respuesta JSON para cada caso.

---

## Formato general de error

Todos los errores siguen el mismo formato JSON:

```json
{
  "detail": "Mensaje descriptivo del error"
}
```

O en caso de errores de validacion con multiples campos:

```json
{
  "campo": ["Mensaje de error para ese campo"],
  "otro_campo": ["Otro mensaje de error"]
}
```

---

## Codigos HTTP utilizados

| Codigo | Significado | Cuando ocurre |
|--------|-------------|---------------|
| `200` | OK | Peticion exitosa |
| `201` | Created | Recurso creado exitosamente |
| `400` | Bad Request | Datos invalidos o faltantes |
| `401` | Unauthorized | Token ausente, invalido o expirado |
| `403` | Forbidden | Token valido pero sin permisos para esa accion |
| `404` | Not Found | El recurso no existe |
| `409` | Conflict | Conflicto con el estado actual (ej: ya inscrito) |
| `500` | Internal Server Error | Error inesperado del servidor |

---

## Errores por endpoint

### Autenticacion

#### `POST /api/usuarios/iniciar-sesion/`

```json
// 400 - Credenciales incorrectas
{
  "detail": "Credenciales invalidas."
}

// 400 - Campos faltantes
{
  "email": ["Este campo es requerido."],
  "password": ["Este campo es requerido."]
}
```

#### `POST /api/usuarios/registrar/`

```json
// 400 - Email ya registrado
{
  "email": ["Ya existe un usuario con este email."]
}

// 400 - Campos invalidos
{
  "email": ["Introduce un email valido."]
}
```

#### `POST /api/usuarios/token/actualizar/`

```json
// 401 - Refresh token expirado o invalido
{
  "detail": "El token es invalido o ha expirado.",
  "code": "token_not_valid"
}
```

---

### Token JWT expirado o ausente

Aplica a cualquier endpoint protegido:

```json
// 401 - Sin token
{
  "detail": "Las credenciales de autenticacion no fueron proporcionadas."
}

// 401 - Token expirado
{
  "detail": "El token dado no es valido para ningun tipo de token.",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "message": "El token es invalido o ha expirado."
    }
  ]
}
```

---

### Permisos insuficientes

```json
// 403 - Estudiante intentando acceder a endpoint de Docente
{
  "detail": "No tienes permiso para realizar esta accion."
}
```

---

### Cursos y Examenes

#### `POST /api/examenes/inscribirse/`

```json
// 400 - Codigo de curso incorrecto
{
  "detail": "No se encontro un curso con ese codigo."
}

// 409 - Ya inscrito en ese curso
{
  "detail": "Ya estas inscrito en este curso."
}
```

#### `POST /api/examenes/examenes/`

```json
// 400 - Curso no encontrado o no pertenece al docente
{
  "curso": ["Curso no valido o no tienes permiso sobre el."]
}

// 400 - Modo maestria sin max_preguntas
{
  "max_preguntas": ["Este campo es requerido cuando el modo es 'maestria'."]
}
```

---

### Motor Adaptativo

#### `POST /api/motor-adaptativo/iniciar/`

```json
// 400 - Examen no encontrado
{
  "detail": "El examen especificado no existe."
}

// 403 - Estudiante no inscrito en el curso del examen
{
  "detail": "No estas inscrito en el curso de este examen."
}

// 409 - Maximo de intentos alcanzado
{
  "detail": "Has alcanzado el maximo de intentos permitidos para este examen."
}

// 500 - Fallo al generar pregunta con IA
{
  "detail": "Error al generar la pregunta. Intenta de nuevo."
}
```

#### `POST /api/motor-adaptativo/<sesion_id>/responder/`

```json
// 400 - Respuesta vacia
{
  "respuesta": ["Este campo no puede estar vacio."]
}

// 404 - Sesion no encontrada
{
  "detail": "No se encontro la sesion de examen."
}

// 409 - La sesion ya esta completada
{
  "detail": "Esta sesion de examen ya ha sido completada."
}

// 403 - La sesion pertenece a otro estudiante
{
  "detail": "No tienes permiso para acceder a esta sesion."
}
```

---

### Analitica

#### `GET /api/analitica/curso/<id>/resumen/`

```json
// 403 - El docente no es propietario del curso
{
  "detail": "No tienes permiso para ver la analitica de este curso."
}

// 404 - Curso no encontrado
{
  "detail": "No encontrado."
}
```

#### `GET /api/analitica/curso/<id>/estudiante/<id>/conocimiento/`

```json
// 404 - El estudiante no tiene modelo de conocimiento aun (no ha tomado ningun examen)
{
  "detail": "El estudiante aun no ha completado ningun examen en este curso."
}
```

---

## Error 500 — Error interno del servidor

Ocurre cuando hay un fallo inesperado. El caso mas comun en LAIRN es el fallo de la API de Claude:

```json
{
  "detail": "Error interno del servidor."
}
```

**Causas frecuentes:**
- `OPENAI_API_KEY` no configurada o invalida
- La API de OpenAI no esta disponible
- Respuesta de GPT en formato inesperado (el JSON de la pregunta llego malformado)

Para depurar, revisar los logs del servidor:

```bash
# Con Docker
docker-compose logs web

# Local
python manage.py runserver  # Ver la terminal donde corre el servidor
```
