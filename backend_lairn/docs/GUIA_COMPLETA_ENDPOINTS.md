# Guia Completa de la API — Para quien no sabe programacion

Esta guia explica en lenguaje simple que hace cada accion disponible en LAIRN, por que existe, cuando usarla y exactamente que informacion enviar y recibir.

---

## Antes de empezar: conceptos basicos

### ¿Que es un endpoint?
Un endpoint es simplemente una **direccion** a la que le puedes enviar o pedir informacion. Como cuando llenas un formulario en una pagina web y le das clic a "Enviar" — por detras, eso es lo que ocurre.

### ¿Que es un token?
Cuando inicias sesion, el sistema te entrega una **llave temporal** llamada token. Esa llave debes presentarla en cada accion que hagas despues, para que el sistema sepa que eres tu y no otra persona. Si no presentas la llave, el sistema te rechaza.

El token de acceso dura **5 minutos**. El de refresco dura **24 horas** y sirve para pedir un token de acceso nuevo sin volver a escribir tu contrasena.

### ¿Que es JSON?
Es la forma en que la aplicacion recibe y envia informacion. Piensalo como un formulario digital:
```
{
  "email": "tunombre@correo.com",
  "password": "tucontrasena"
}
```
Cada linea es un campo con su valor.

---

## Orden recomendado para empezar

```
1. Registrarte (si eres nuevo)
2. Iniciar sesion → obtienes tu token
3. Usar el token para todo lo demas
```

---

---

# SECCION 1 — Usuarios y sesion

---

## 1. Registrarse

**¿Para que sirve?**
Crea una cuenta nueva en LAIRN. Solo aplica para estudiantes. Los docentes y administradores son creados por el administrador del sistema.

**Direccion:** `POST /api/usuarios/registrar/`

**¿Necesito estar conectado?** No. Es el primer paso, no necesitas llave.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `primer_nombre` | Tu primer nombre | `"Ana"` |
| `segundo_nombre` | Tu segundo nombre (opcional) | `"Maria"` |
| `primer_apellido` | Tu primer apellido | `"Garcia"` |
| `segundo_apellido` | Tu segundo apellido (opcional) | `"Lopez"` |
| `email` | Tu correo electronico. Sera tu usuario para entrar. | `"ana@correo.com"` |
| `password` | Tu contrasena | `"micontrasena123"` |

**Ejemplo de lo que envias:**
```json
{
  "primer_nombre": "Ana",
  "primer_apellido": "Garcia",
  "email": "ana@correo.com",
  "password": "micontrasena123"
}
```

**Que recibes si todo sale bien:**
```json
{
  "mensaje": "Usuario registrado exitosamente.",
  "email": "ana@correo.com"
}
```

**Que puede salir mal:**
- Si el correo ya esta registrado, el sistema te avisa y no crea la cuenta de nuevo.
- Si falta algun campo obligatorio, el sistema te dice cual campo falta.

---

## 2. Iniciar sesion

**¿Para que sirve?**
Le dices al sistema quien eres con tu correo y contrasena. El sistema te entrega dos llaves: una para usar ya (token de acceso) y otra de reserva para cuando la primera expire (token de refresco).

**Direccion:** `POST /api/usuarios/iniciar-sesion/`

**¿Necesito estar conectado?** No. Este es el paso que te da acceso.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `email` | Tu correo con el que te registraste | `"ana@correo.com"` |
| `password` | Tu contrasena | `"micontrasena123"` |

**Ejemplo de lo que envias:**
```json
{
  "email": "ana@correo.com",
  "password": "micontrasena123"
}
```

**Que recibes si todo sale bien:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "rol": "Estudiante"
}
```

**Que significa cada campo recibido:**
- `access` → Tu llave de acceso. La necesitas para todo lo que hagas a partir de ahora. Dura 5 minutos.
- `refresh` → Tu llave de reserva para renovar el acceso sin volver a escribir tu contrasena. Dura 24 horas.
- `rol` → Tu rol en el sistema: `"Estudiante"`, `"Docente"` o `"Administrador"`. El frontend lo usa para mostrar las pantallas correctas.

**Que puede salir mal:**
- Si el correo o la contrasena son incorrectos, el sistema responde con un mensaje de credenciales invalidas. No especifica cual de los dos esta mal (por seguridad).

---

## 3. Ver mis datos

**¿Para que sirve?**
Te muestra la informacion de tu propia cuenta: tu nombre completo, tu correo y tu rol en el sistema.

**Direccion:** `GET /api/usuarios/mis-datos/`

**¿Necesito estar conectado?** Si. Debes enviar tu llave de acceso.

**Como enviar la llave:**
En el encabezado de la peticion incluyes:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci...
```
(Reemplaza el texto largo con tu token de acceso real)

**Que debes enviar:** Nada en el cuerpo. Solo la llave en el encabezado.

**Que recibes si todo sale bien:**
```json
{
  "id": 5,
  "email": "ana@correo.com",
  "nombre_completo": "Ana Garcia",
  "rol": "Estudiante"
}
```

**Que puede salir mal:**
- Si no envias el token o ya expiro, el sistema te dice que no tienes permiso.

---

## 4. Renovar el token de acceso

**¿Para que sirve?**
El token de acceso dura solo 5 minutos. Cuando expira, en lugar de volver a escribir tu correo y contrasena, usas tu token de refresco (que dura 24 horas) para obtener un token de acceso nuevo.

**Direccion:** `POST /api/usuarios/token/actualizar/`

**¿Necesito estar conectado?** Si, pero con el token de **refresco**, no el de acceso.

**Que debes enviar:**

| Campo | Descripcion |
|-------|-------------|
| `refresh` | Tu token de refresco (el que obtuviste al iniciar sesion) |

**Ejemplo de lo que envias:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

**Que recibes si todo sale bien:**
```json
{
  "access": "eyJ0eXAiOiJKV1Qi...nuevo-token..."
}
```

Este nuevo `access` lo usas a partir de ahora en lugar del anterior.

**Que puede salir mal:**
- Si el token de refresco tambien expiro (pasaron mas de 24 horas), debes iniciar sesion de nuevo.

---

## 5. Cerrar sesion

**¿Para que sirve?**
Invalida tu token de refresco. A partir de ese momento, aunque alguien tenga ese token, no podra usarlo para obtener nuevos accesos. El token de acceso sigue valido hasta que expire naturalmente (5 minutos), pero al no poder renovarlo, la sesion queda efectivamente cerrada.

**Direccion:** `POST /api/usuarios/cerrar-sesion/`

**¿Necesito estar conectado?** Si.

**Que debes enviar:**

| Campo | Descripcion |
|-------|-------------|
| `refresh` | Tu token de refresco actual |

**Ejemplo de lo que envias:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

**Que recibes si todo sale bien:**
```json
{
  "mensaje": "Sesion cerrada exitosamente."
}
```

---

---

# SECCION 2 — Cursos y examenes

---

## 6. Crear un curso (solo Docentes)

**¿Para que sirve?**
Un docente crea un curso, que es el contenedor de todo: los examenes y los estudiantes inscritos. Al crearlo, el sistema genera automaticamente un **codigo unico de 8 caracteres** que el docente comparte con sus estudiantes para que puedan unirse.

**Direccion:** `POST /api/examenes/cursos/`

**¿Necesito estar conectado?** Si. Ademas, debes tener el rol de **Docente**.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `nombre` | Nombre del curso | `"Calculo I"` |
| `descripcion` | Descripcion breve del curso | `"Limites, derivadas e integrales"` |

**Ejemplo de lo que envias:**
```json
{
  "nombre": "Calculo I",
  "descripcion": "Limites, derivadas e integrales"
}
```

**Que recibes si todo sale bien:**
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

El campo `codigo` es lo que el docente debe compartir con sus estudiantes. Sin ese codigo, nadie puede inscribirse.

**Que puede salir mal:**
- Si no tienes rol de Docente, el sistema te rechaza con un error de permisos.

---

## 7. Ver mis cursos (solo Docentes)

**¿Para que sirve?**
Lista todos los cursos que el docente ha creado, con su informacion basica y el codigo de acceso de cada uno.

**Direccion:** `GET /api/examenes/cursos/`

**¿Necesito estar conectado?** Si. Solo Docentes.

**Que debes enviar:** Nada en el cuerpo. Solo tu token en el encabezado.

**Que recibes:**
```json
[
  {
    "id": 1,
    "nombre": "Calculo I",
    "descripcion": "Limites, derivadas e integrales",
    "codigo": "AB3X9KLM",
    "creado_en": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "nombre": "Algebra Lineal",
    "descripcion": "Vectores y matrices",
    "codigo": "ZK7YWQ21",
    "creado_en": "2024-01-20T09:00:00Z"
  }
]
```

---

## 8. Ver el detalle de un curso (solo Docentes)

**¿Para que sirve?**
Retorna la informacion completa de un solo curso del docente. Util para mostrar la pantalla de detalle del curso o para volver a consultar el codigo de acceso antes de compartirlo con un estudiante nuevo.

**Direccion:** `GET /api/examenes/cursos/<id>/`

Reemplaza `<id>` con el numero del curso. Por ejemplo, para el curso 1: `/api/examenes/cursos/1/`

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes si todo sale bien:**
```json
{
  "id": 1,
  "nombre": "Calculo I",
  "descripcion": "Limites, derivadas e integrales",
  "codigo": "AB3X9KLM",
  "creado_en": "2024-01-15T10:30:00Z"
}
```

**Que puede salir mal:**
- Si el curso no existe o pertenece a otro docente, el sistema responde 404 (por seguridad, no diferencia entre "no existe" y "no es tuyo").

---

## 9. Actualizar un curso (solo Docentes)

**¿Para que sirve?**
Modifica los datos del curso: nombre y descripcion. El codigo de acceso y la fecha de creacion son generados por el sistema y no se pueden modificar.

Existen dos formas de actualizar:
- `PUT` reemplaza todos los campos editables (debes enviarlos todos).
- `PATCH` actualiza solo los campos que envies (los demas quedan como estaban).

**Direccion:**
- `PUT /api/examenes/cursos/<id>/` — actualizacion completa
- `PATCH /api/examenes/cursos/<id>/` — actualizacion parcial

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `nombre` | Nuevo nombre del curso | `"Calculo Diferencial"` |
| `descripcion` | Nueva descripcion del curso | `"Derivadas e integrales aplicadas"` |

**Ejemplo PUT (reemplaza todo):**
```json
{
  "nombre": "Calculo Diferencial",
  "descripcion": "Derivadas e integrales aplicadas"
}
```

**Ejemplo PATCH (cambia solo el nombre):**
```json
{
  "nombre": "Calculo Diferencial"
}
```

**Que recibes si todo sale bien:**
El curso completo con los cambios aplicados:
```json
{
  "id": 1,
  "nombre": "Calculo Diferencial",
  "descripcion": "Derivadas e integrales aplicadas",
  "codigo": "AB3X9KLM",
  "creado_en": "2024-01-15T10:30:00Z"
}
```

**Que puede salir mal:**
- Si el curso no existe o pertenece a otro docente: 404.
- Si los datos son invalidos (por ejemplo nombre vacio): 400 con el detalle del campo en error.

---

## 10. Eliminar un curso (solo Docentes)

**¿Para que sirve?**
Borra un curso completo. Esta accion **elimina en cascada** todas las inscripciones de estudiantes y todos los examenes asociados al curso. Es irreversible: no hay papelera ni recuperacion.

**Direccion:** `DELETE /api/examenes/cursos/<id>/`

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes si todo sale bien:**
No recibes contenido en el cuerpo. El sistema responde con el codigo HTTP `204 No Content`, que indica que la eliminacion fue exitosa.

**Que puede salir mal:**
- Si el curso no existe o pertenece a otro docente: 404.

---

## 11. Crear un examen (solo Docentes)

**¿Para que sirve?**
Dentro de un curso, el docente define un examen. Aqui configura el tema, cuantas preguntas quiere, cuanto tiempo tiene el estudiante, si el examen sube y baja de dificultad automaticamente, si da pistas, y cuantos intentos puede hacer el estudiante.

**Direccion:** `POST /api/examenes/examenes/`

**¿Necesito estar conectado?** Si. Solo Docentes.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `curso` | El ID del curso donde va este examen | `1` |
| `titulo` | Titulo del examen | `"Examen de Derivadas"` |
| `tema` | Tema sobre el que la IA generara las preguntas. Mientras mas especifico, mejor. | `"Derivadas de funciones trigonometricas"` |
| `tiempo` | Duracion en minutos | `30` |
| `num_preguntas` | Cuantas preguntas tendra (o el minimo en modo maestria) | `10` |
| `retroalimentacion` | Si el estudiante ve si acerto o no despues de cada respuesta | `true` o `false` |
| `dificultad_inicial` | Con que dificultad empieza el examen: `1`=Facil, `2`=Media, `3`=Dificil | `1` |
| `max_intentos` | Cuantas veces puede intentarlo. `0` significa sin limite. | `3` |
| `es_guiado` | Si la IA da una explicacion corta antes de cada pregunta | `true` o `false` |
| `modo` | `"fijo"` = numero exacto de preguntas. `"maestria"` = continua hasta dominar el tema. | `"fijo"` |
| `max_preguntas` | Solo para modo maestria: el maximo de preguntas antes de terminar igual. | `20` |

**Ejemplo de lo que envias (modo fijo):**
```json
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

**Ejemplo modo maestria:**
```json
{
  "curso": 1,
  "titulo": "Practica de Integrales",
  "tema": "Integrales por sustitucion",
  "tiempo": 60,
  "num_preguntas": 5,
  "retroalimentacion": true,
  "dificultad_inicial": 1,
  "max_intentos": 0,
  "es_guiado": true,
  "modo": "maestria",
  "max_preguntas": 25
}
```

**Que recibes si todo sale bien:**
```json
{
  "id": 1,
  "titulo": "Examen de Derivadas",
  "tema": "Derivadas de funciones trigonometricas",
  "modo": "fijo",
  "num_preguntas": 10,
  "creado_en": "2024-01-15T10:35:00Z"
}
```

---

## 12. Ver el detalle de un examen (solo Docentes)

**¿Para que sirve?**
Retorna la configuracion completa de un solo examen, incluyendo todos sus parametros (tema, tiempo, dificultad, modo, intentos, etc.). Util para mostrar la pantalla de edicion o revision antes de actualizar.

**Direccion:** `GET /api/examenes/examenes/<id>/`

Reemplaza `<id>` con el numero del examen. Por ejemplo: `/api/examenes/examenes/1/`

**¿Necesito estar conectado?** Si. Solo el Docente cuyo curso contiene el examen.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes si todo sale bien:**
```json
{
  "id": 1,
  "curso": 1,
  "titulo": "Examen de Derivadas",
  "tema": "Derivadas de funciones trigonometricas",
  "tiempo": 30,
  "num_preguntas": 10,
  "retroalimentacion": true,
  "dificultad_inicial": 1,
  "max_intentos": 3,
  "es_guiado": false,
  "modo": "fijo",
  "max_preguntas": 20,
  "creado_en": "2024-01-15T10:35:00Z"
}
```

**Que puede salir mal:**
- Si el examen no existe o pertenece a un curso de otro docente: 404.

---

## 13. Actualizar un examen (solo Docentes)

**¿Para que sirve?**
Modifica la configuracion de un examen del docente: titulo, tema, tiempo, dificultad, modo, numero de preguntas, intentos, etc.

**Importante — bloqueo por sesion activa:**
Si en este momento **al menos un estudiante esta presentando el examen**, la actualizacion se rechaza. Esto evita que las reglas del examen cambien a mitad de un intento (por ejemplo, que se le aumente la dificultad o se le reduzca el tiempo a un estudiante que ya empezo). Una vez que todos los estudiantes en curso terminen, el examen vuelve a ser editable.

**Direccion:**
- `PUT /api/examenes/examenes/<id>/` — actualizacion completa (debes enviar todos los campos)
- `PATCH /api/examenes/examenes/<id>/` — actualizacion parcial (solo los campos que envies)

**¿Necesito estar conectado?** Si. Solo el Docente cuyo curso contiene el examen.

**Que debes enviar:**
Los mismos campos que en el endpoint 11 (Crear un examen). En `PATCH` puedes enviar solo los que quieras cambiar.

**Ejemplo PATCH (cambia solo el tiempo y la dificultad inicial):**
```json
{
  "tiempo": 45,
  "dificultad_inicial": 2
}
```

**Que recibes si todo sale bien:**
El examen completo con los cambios aplicados (mismo formato que el GET del endpoint 12).

**Que puede salir mal:**
- Si el examen no existe o pertenece a otro docente: 404.
- Si hay estudiantes presentando el examen ahora: 400 con el mensaje `"No se puede editar el examen porque hay estudiantes presentandolo en este momento."`.
- Si los datos son invalidos (por ejemplo `max_preguntas` menor que `num_preguntas` en modo maestria): 400 con el detalle del campo en error.

---

## 14. Eliminar un examen (solo Docentes)

**¿Para que sirve?**
Borra un examen completo. Esta accion **elimina en cascada** todas las sesiones, respuestas y resultados de estudiantes asociados al examen. Es irreversible.

**Importante — bloqueo por sesion activa:**
Si en este momento **al menos un estudiante esta presentando el examen**, la eliminacion se rechaza con codigo `409 Conflict`. Esto protege a los estudiantes en curso para que no queden con un examen a medias que ya no existe.

**Direccion:** `DELETE /api/examenes/examenes/<id>/`

**¿Necesito estar conectado?** Si. Solo el Docente cuyo curso contiene el examen.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes si todo sale bien:**
No recibes contenido en el cuerpo. El sistema responde con el codigo HTTP `204 No Content`.

**Que puede salir mal:**
- Si el examen no existe o pertenece a otro docente: 404.
- Si hay estudiantes presentando el examen ahora: 409 con el mensaje `"No se puede eliminar el examen porque hay estudiantes presentandolo en este momento."`.

---

## 15. Inscribirse a un curso (solo Estudiantes)

**¿Para que sirve?**
El estudiante ingresa el codigo que le dio el docente y queda inscrito en el curso. A partir de ese momento puede ver y tomar los examenes de ese curso.

**Direccion:** `POST /api/examenes/inscribirse/`

**¿Necesito estar conectado?** Si. Solo Estudiantes.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `codigo` | El codigo de 8 caracteres que te dio el docente | `"AB3X9KLM"` |

**Ejemplo de lo que envias:**
```json
{
  "codigo": "AB3X9KLM"
}
```

**Que recibes si todo sale bien:**
```json
{
  "mensaje": "Te has inscrito exitosamente al curso Calculo I."
}
```

**Que puede salir mal:**
- Si el codigo es incorrecto, el sistema dice que no encontro el curso.
- Si ya estas inscrito en ese curso, el sistema te avisa y no te inscribe dos veces.

---

## 16. Ver estudiantes de un curso (solo Docentes)

**¿Para que sirve?**
El docente puede ver la lista de todos los estudiantes que se han inscrito en uno de sus cursos.

**Direccion:** `GET /api/examenes/cursos/<id>/estudiantes/`

Reemplaza `<id>` con el numero del curso. Por ejemplo, para el curso 1: `/api/examenes/cursos/1/estudiantes/`

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes:**
```json
[
  {
    "id": 5,
    "nombre_completo": "Ana Garcia",
    "email": "ana@correo.com",
    "fecha_inscripcion": "2024-01-16T08:00:00Z"
  },
  {
    "id": 6,
    "nombre_completo": "Carlos Ruiz",
    "email": "carlos@correo.com",
    "fecha_inscripcion": "2024-01-16T09:30:00Z"
  }
]
```

---

## 17. Eliminar un estudiante del curso (solo Docentes)

**¿Para que sirve?**
El docente puede retirar a un estudiante de su curso. Esta accion elimina la inscripcion del estudiante; ya no podra acceder a los examenes de ese curso. No borra al usuario ni su historial de resultados en otros cursos.

**Direccion:** `DELETE /api/examenes/cursos/<curso_id>/estudiantes/<estudiante_id>/`

Reemplaza `<curso_id>` con el numero del curso y `<estudiante_id>` con el numero del estudiante a retirar. Por ejemplo, para retirar al estudiante 5 del curso 1: `/api/examenes/cursos/1/estudiantes/5/`

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que debes enviar:** Nada en el cuerpo. Los IDs van en la URL.

**Que recibes si todo sale bien:**
```json
{
  "detalle": "Estudiante eliminado del curso."
}
```

**Que puede salir mal:**
- Si el curso no existe o pertenece a otro docente: 404 con `{"detalle": "Curso no encontrado."}`.
- Si el estudiante no esta inscrito en ese curso: 404 con `{"detalle": "Estudiante no encontrado en este curso."}`.

---

---

# SECCION 3 — Tomar el examen

---

## 18. Iniciar un examen (solo Estudiantes)

**¿Para que sirve?**
El estudiante le dice al sistema que quiere empezar (o continuar) un examen. El sistema verifica que este inscrito en el curso, crea una sesion de examen, y le pide a la inteligencia artificial que genere la primera pregunta personalizada para ese estudiante.

Esto es el corazon de LAIRN: la pregunta que recibiras fue creada en ese momento por Claude (la IA), adaptada a tu nivel y a los conceptos que necesitas reforzar.

**Direccion:** `POST /api/motor-adaptativo/iniciar/`

**¿Necesito estar conectado?** Si. Solo Estudiantes.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `examen_id` | El numero ID del examen que quieres tomar | `1` |

**Ejemplo de lo que envias:**
```json
{
  "examen_id": 1
}
```

**Que recibes si todo sale bien:**
```json
{
  "sesion_id": 42,
  "estado": "en_progreso",
  "pregunta_actual": {
    "concepto": "derivada de seno",
    "pregunta": "¿Cual es la derivada de la funcion f(x) = sen(x)?",
    "opciones": [
      "cos(x)",
      "-cos(x)",
      "sen(x)",
      "-sen(x)"
    ]
  },
  "preguntas_respondidas": 0,
  "dificultad_actual": 1
}
```

**Que significa cada campo recibido:**
- `sesion_id` → El numero de tu sesion activa. Lo necesitas para responder.
- `estado` → `en_progreso` significa que el examen esta activo.
- `pregunta_actual` → La pregunta que la IA genero para ti.
  - `concepto` → El tema especifico que evalua esa pregunta.
  - `pregunta` → El texto de la pregunta.
  - `opciones` → Las 4 posibles respuestas. Solo una es correcta.
- `preguntas_respondidas` → Cuantas preguntas llevas respondidas (empieza en 0).
- `dificultad_actual` → Nivel de dificultad actual: 1=Facil, 2=Media, 3=Dificil.

**Si el examen es en modo guiado**, la pregunta tambien incluye:
```json
{
  "concepto": "derivada de seno",
  "explicacion": "La derivada de una funcion mide su tasa de cambio en cada punto. Para funciones trigonometricas existen derivadas conocidas que vale la pena memorizar.",
  "pregunta": "¿Cual es la derivada de la funcion f(x) = sen(x)?",
  "opciones": ["cos(x)", "-cos(x)", "sen(x)", "-sen(x)"]
}
```

**Que puede salir mal:**
- Si no estas inscrito en el curso del examen, el sistema te rechaza.
- Si ya alcanzaste el maximo de intentos del examen, el sistema te avisa.
- Si la IA falla por alguna razon tecnica, recibiras un error 500. En ese caso intenta de nuevo.

---

## 19. Responder una pregunta (solo Estudiantes)

**¿Para que sirve?**
El estudiante envia su respuesta a la pregunta actual. El sistema la evalua, actualiza su perfil de conocimiento, ajusta la dificultad para la siguiente pregunta, y le pide a la IA que genere la siguiente pregunta. Este ciclo se repite hasta que el examen termina.

**Direccion:** `POST /api/motor-adaptativo/<sesion_id>/responder/`

Reemplaza `<sesion_id>` con el numero de sesion que obtuviste al iniciar el examen. Por ejemplo: `/api/motor-adaptativo/42/responder/`

**¿Necesito estar conectado?** Si. Solo el Estudiante dueno de esa sesion.

**Que debes enviar:**

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `respuesta` | La opcion que elegiste, exactamente como aparece en la lista de opciones | `"cos(x)"` |

**Ejemplo de lo que envias:**
```json
{
  "respuesta": "cos(x)"
}
```

**Que recibes si la respuesta fue correcta y el examen continua:**
```json
{
  "sesion_id": 42,
  "estado": "en_progreso",
  "es_correcta": true,
  "pregunta_actual": {
    "concepto": "derivada de coseno",
    "pregunta": "¿Cual es la derivada de g(x) = cos(x)?",
    "opciones": ["-sen(x)", "sen(x)", "cos(x)", "-cos(x)"]
  },
  "preguntas_respondidas": 1,
  "dificultad_actual": 2
}
```

Nota: la dificultad subio de 1 a 2 porque respondiste correctamente.

**Que recibes si la respuesta fue incorrecta:**
```json
{
  "sesion_id": 42,
  "estado": "en_progreso",
  "es_correcta": false,
  "pregunta_actual": {
    "concepto": "derivada de seno",
    "pregunta": "Si f(x) = sen(x), ¿cual es f'(x)?",
    "opciones": ["cos(x)", "-cos(x)", "tan(x)", "sec(x)"]
  },
  "preguntas_respondidas": 1,
  "dificultad_actual": 1
}
```

La IA genero otra pregunta sobre el mismo concepto (derivada de seno) porque no lo dominaste aun. La dificultad no subio.

**Que recibes cuando el examen termina:**
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

**Que significa cada campo al terminar:**
- `puntaje` → Porcentaje de aciertos. 80.0 significa que acertaste el 80%.
- `nota` → Calificacion en escala de 1.0 a 5.0.
- `correctas` → Cuantas preguntas respondiste bien.
- `total_preguntas` → Total de preguntas que respondiste.

**Formula de la nota:**
```
nota = 1.0 + (correctas / total_preguntas) × 4.0
```
- 0% de aciertos → nota 1.0
- 100% de aciertos → nota 5.0
- 80% de aciertos → nota 4.2

**Que puede salir mal:**
- Si envias una respuesta vacia, el sistema te pide que la completes.
- Si la sesion ya estaba completada y intentas responder de nuevo, el sistema te avisa.

---

---

# SECCION 4 — Ver resultados y estadisticas

---

## 20. Ver mis resultados (solo Estudiantes)

**¿Para que sirve?**
El estudiante ve el historial de todos los examenes que ha completado: en que curso, que nota obtuvo, cuantas preguntas respondio bien y cuando lo hizo.

**Direccion:** `GET /api/analitica/mis-resultados/`

**¿Necesito estar conectado?** Si. Solo Estudiantes.

**Que debes enviar:** Nada en el cuerpo.

**Que recibes:**
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
  },
  {
    "examen": "Examen de Limites",
    "curso": "Calculo I",
    "puntaje": 60.0,
    "nota": 3.4,
    "correctas": 6,
    "total_preguntas": 10,
    "completado_en": "2024-01-18T10:30:00Z"
  }
]
```

---

## 21. Ver resumen del curso (solo Docentes)

**¿Para que sirve?**
El docente ve un resumen general de como le fue al grupo en su curso: cuantos estudiantes han completado examenes, el promedio de notas, cuantos aprobaron.

**Direccion:** `GET /api/analitica/curso/<id>/resumen/`

Reemplaza `<id>` con el numero del curso.

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que recibes:**
```json
{
  "curso": "Calculo I",
  "total_estudiantes": 25,
  "examenes_completados": 18,
  "promedio_puntaje": 72.5,
  "promedio_nota": 3.9,
  "tasa_aprobacion": "78%"
}
```

---

## 22. Ver patrones de aprendizaje del curso (solo Docentes)

**¿Para que sirve?**
El docente ve que conceptos son los mas dificiles para el grupo en general. Por ejemplo, si todos los estudiantes fallan en "derivada de coseno", el docente sabe que ese tema necesita mas atencion en clase.

**Direccion:** `GET /api/analitica/curso/<id>/patrones/`

**¿Necesito estar conectado?** Si. Solo Docentes.

**Que recibes:**
```json
{
  "conceptos_dificiles": [
    {
      "concepto": "regla de la cadena",
      "promedio_aciertos": 35.0,
      "nivel_promedio": 1
    },
    {
      "concepto": "derivada de coseno",
      "promedio_aciertos": 48.0,
      "nivel_promedio": 1
    }
  ],
  "conceptos_dominados": [
    {
      "concepto": "derivada de seno",
      "promedio_aciertos": 85.0,
      "nivel_promedio": 3
    }
  ]
}
```

---

## 23. Ver todos los resultados del curso (solo Docentes)

**¿Para que sirve?**
Lista los resultados de todos los estudiantes en todos los examenes del curso. Util para tener una vision completa del rendimiento del grupo.

**Direccion:** `GET /api/analitica/curso/<id>/resultados/`

**¿Necesito estar conectado?** Si. Solo Docentes.

**Que recibes:**
```json
[
  {
    "estudiante": "Ana Garcia",
    "examen": "Examen de Derivadas",
    "puntaje": 80.0,
    "nota": 4.2,
    "completado_en": "2024-01-15T11:05:00Z"
  },
  {
    "estudiante": "Carlos Ruiz",
    "examen": "Examen de Derivadas",
    "puntaje": 50.0,
    "nota": 3.0,
    "completado_en": "2024-01-15T11:30:00Z"
  }
]
```

---

## 24. Ver el avance de un estudiante especifico (solo Docentes)

**¿Para que sirve?**
El docente selecciona a un estudiante de su curso y ve en detalle como le ha ido: cuantos examenes completo, sus notas, y su progreso en el tiempo.

**Direccion:** `GET /api/analitica/curso/<id_curso>/estudiante/<id_estudiante>/`

Reemplaza `<id_curso>` con el numero del curso y `<id_estudiante>` con el numero del estudiante.

**¿Necesito estar conectado?** Si. Solo el Docente propietario del curso.

**Que recibes:**
```json
{
  "estudiante": "Ana Garcia",
  "curso": "Calculo I",
  "examenes_completados": 3,
  "promedio_nota": 4.0,
  "resultados": [
    {
      "examen": "Examen de Derivadas",
      "nota": 4.2,
      "puntaje": 80.0,
      "completado_en": "2024-01-15T11:05:00Z"
    },
    {
      "examen": "Examen de Limites",
      "nota": 3.8,
      "puntaje": 70.0,
      "completado_en": "2024-01-18T10:30:00Z"
    }
  ]
}
```

---

## 25. Ver el mapa de conocimiento de un estudiante (solo Docentes)

**¿Para que sirve?**
Esta es la informacion mas detallada que ofrece LAIRN. El docente puede ver, concepto por concepto, que tan bien domina el tema cada estudiante. No solo sabe si aprobo o no, sino exactamente en que partes del tema necesita ayuda.

**Direccion:** `GET /api/analitica/curso/<id_curso>/estudiante/<id_estudiante>/conocimiento/`

**¿Necesito estar conectado?** Si. Solo Docentes.

**Que recibes:**
```json
{
  "estudiante": "Ana Garcia",
  "examen": "Examen de Derivadas",
  "conceptos": {
    "derivada de seno": {
      "intentos": 5,
      "correctas": 5,
      "nivel": 3
    },
    "derivada de coseno": {
      "intentos": 4,
      "correctas": 2,
      "nivel": 1
    },
    "regla de la cadena": {
      "intentos": 3,
      "correctas": 2,
      "nivel": 2
    }
  },
  "actualizado_en": "2024-01-15T11:05:00Z"
}
```

**Como interpretar los niveles:**
- `nivel 1` → **Debil.** El estudiante acerto menos del 50% de las preguntas sobre ese concepto. Necesita refuerzo urgente.
- `nivel 2` → **En desarrollo.** Acerto entre el 50% y el 79%. Va bien pero aun no lo domina.
- `nivel 3` → **Dominado.** Acerto el 80% o mas. El estudiante comprende ese concepto.

En el ejemplo de Ana: domina la derivada de seno (nivel 3), esta desarrollando la regla de la cadena (nivel 2), y necesita refuerzo en la derivada de coseno (nivel 1).

---

---

# Resumen de todos los endpoints

| # | Que hace | Direccion | Rol necesario |
|---|----------|-----------|---------------|
| 1 | Registrarse | `POST /api/usuarios/registrar/` | Ninguno (publico) |
| 2 | Iniciar sesion | `POST /api/usuarios/iniciar-sesion/` | Ninguno (publico) |
| 3 | Ver mis datos | `GET /api/usuarios/mis-datos/` | Cualquier usuario |
| 4 | Renovar token | `POST /api/usuarios/token/actualizar/` | Cualquier usuario |
| 5 | Cerrar sesion | `POST /api/usuarios/cerrar-sesion/` | Cualquier usuario |
| 6 | Crear curso | `POST /api/examenes/cursos/` | Docente |
| 7 | Ver mis cursos | `GET /api/examenes/cursos/` | Docente |
| 8 | Ver detalle de curso | `GET /api/examenes/cursos/<id>/` | Docente |
| 9 | Actualizar curso | `PUT/PATCH /api/examenes/cursos/<id>/` | Docente |
| 10 | Eliminar curso | `DELETE /api/examenes/cursos/<id>/` | Docente |
| 11 | Crear examen | `POST /api/examenes/examenes/` | Docente |
| 12 | Ver detalle de examen | `GET /api/examenes/examenes/<id>/` | Docente |
| 13 | Actualizar examen | `PUT/PATCH /api/examenes/examenes/<id>/` | Docente (bloqueado si hay sesion activa) |
| 14 | Eliminar examen | `DELETE /api/examenes/examenes/<id>/` | Docente (bloqueado si hay sesion activa) |
| 15 | Inscribirse al curso | `POST /api/examenes/inscribirse/` | Estudiante |
| 16 | Ver estudiantes del curso | `GET /api/examenes/cursos/<id>/estudiantes/` | Docente |
| 17 | Retirar estudiante | `DELETE /api/examenes/cursos/<id>/estudiantes/<id>/` | Docente |
| 18 | Iniciar examen | `POST /api/motor-adaptativo/iniciar/` | Estudiante |
| 19 | Responder pregunta | `POST /api/motor-adaptativo/<sesion_id>/responder/` | Estudiante |
| 20 | Ver mis resultados | `GET /api/analitica/mis-resultados/` | Estudiante |
| 21 | Resumen del curso | `GET /api/analitica/curso/<id>/resumen/` | Docente |
| 22 | Patrones del curso | `GET /api/analitica/curso/<id>/patrones/` | Docente |
| 23 | Resultados del curso | `GET /api/analitica/curso/<id>/resultados/` | Docente |
| 24 | Avance de un estudiante | `GET /api/analitica/curso/<id>/estudiante/<id>/` | Docente |
| 25 | Mapa de conocimiento | `GET /api/analitica/curso/<id>/estudiante/<id>/conocimiento/` | Docente |
