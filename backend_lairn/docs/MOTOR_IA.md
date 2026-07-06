# Motor de IA — Como funciona el agente de examenes

Documentacion detallada de como LAIRN genera preguntas, adapta la dificultad y modela el conocimiento del estudiante. Todo lo descrito aqui esta implementado en:

- [apps/motor_adaptativo/services/agente_ia.py](../apps/motor_adaptativo/services/agente_ia.py) — el agente de IA
- [apps/motor_adaptativo/views/vista_iniciar_examen.py](../apps/motor_adaptativo/views/vista_iniciar_examen.py) — inicio de sesion
- [apps/motor_adaptativo/views/vista_responder.py](../apps/motor_adaptativo/views/vista_responder.py) — ciclo de respuesta

---

## Flujo completo de una sesion

```
POST /iniciar/
    │
    ├─ Verifica inscripcion del estudiante
    ├─ Verifica que no agoto los intentos
    ├─ Busca sesion en_progreso existente (reanuda si existe)
    ├─ Si no existe: crea SesionExamen nueva
    ├─ Carga ModeloConocimiento previo del estudiante (si existe)
    ├─ Llama a generar_pregunta() → OpenAI
    └─ Devuelve primera pregunta

        ↓ (el estudiante responde)

POST /<sesion_id>/responder/
    │
    ├─ Evalua si la respuesta es correcta
    ├─ Guarda RespuestaEstudiante en analitica
    ├─ Ajusta dificultad (sube o baja 1 nivel)
    ├─ Actualiza ModeloConocimiento (nivel por concepto)
    ├─ Decide si el examen termina (_debe_terminar)
    │
    ├─ Si termina:
    │   ├─ Calcula puntaje y nota
    │   └─ Devuelve resultado final
    │
    └─ Si continua:
        ├─ Llama a generar_pregunta() con historial actualizado
        └─ Devuelve siguiente pregunta
```

---

## El prompt — como se construye

La funcion `generar_pregunta()` construye el prompt en tres partes antes de llamar a OpenAI.

### Parte 1 — Instruccion base

**Modo normal:**
```
Eres un tutor inteligente adaptativo. Genera UNA pregunta de opción múltiple.
```

**Modo guiado (`es_guiado=True`):**
```
Eres un tutor inteligente adaptativo. Primero escribe una explicación breve
(2-3 oraciones) del concepto clave necesario para responder la pregunta.
La explicación debe ayudar al estudiante a entender el tema, pero SIN revelar
cuál es la respuesta correcta. Luego genera la pregunta.
```

### Parte 2 — Contexto del examen

```
Tema general: "Derivadas de funciones trigonométricas"
Dificultad: fácil.  ← traducido del numero (1=fácil, 2=media, 3=difícil)
```

### Parte 3 — Modelo de conocimiento del estudiante

Si el estudiante ya ha respondido preguntas antes (en intentos anteriores o en la sesion actual), el sistema le informa a la IA el estado de cada concepto:

```
--- Modelo de conocimiento del estudiante ---
Conceptos DÉBILES (priorizar, el estudiante falla aquí): derivada de coseno, regla de la cadena
Conceptos EN DESARROLLO (reforzar): derivada de logaritmo
Conceptos DOMINADOS (no repetir innecesariamente): derivada de seno
---
```

Esta seccion se genera en `_construir_contexto_conocimiento()` clasificando los conceptos por nivel:
- `nivel <= 1` → DEBIL
- `nivel == 2` → EN DESARROLLO
- `nivel >= 3` → DOMINADO

Si es la primera vez del estudiante, esta seccion no aparece en el prompt.

### Parte 4 — Historial de preguntas

Para evitar que la IA repita preguntas dentro de la misma sesion:

```
Preguntas ya realizadas (no repetir):
- ¿Cuál es la derivada de sen(x)?
- ¿Cuál es la derivada de cos(x)?
```

### Parte 5 — Instruccion de priorizacion y formato

```
Si el estudiante tiene conceptos débiles, genera la pregunta sobre uno de esos conceptos.
Si no hay historial de conocimiento, elige el sub-concepto más apropiado para la dificultad.

Responde SOLO con este JSON (sin texto adicional):
{ ... }
```

---

## Prompt completo ensamblado — ejemplo real

```
Eres un tutor inteligente adaptativo. Genera UNA pregunta de opción múltiple.

Tema general: "Derivadas de funciones trigonométricas"
Dificultad: media.

--- Modelo de conocimiento del estudiante ---
Conceptos DÉBILES (priorizar, el estudiante falla aquí): derivada de coseno
Conceptos EN DESARROLLO (reforzar): regla de la cadena
Conceptos DOMINADOS (no repetir innecesariamente): derivada de seno
---

Preguntas ya realizadas (no repetir):
- ¿Cuál es la derivada de sen(x)?

Si el estudiante tiene conceptos débiles, genera la pregunta sobre uno de esos conceptos.
Si no hay historial de conocimiento, elige el sub-concepto más apropiado para la dificultad.

Responde SOLO con este JSON (sin texto adicional):
{
  "concepto": "nombre del sub-concepto específico evaluado",
  "pregunta": "texto de la pregunta",
  "opciones": ["opción A", "opción B", "opción C", "opción D"],
  "respuesta_correcta": "texto exacto de la opción correcta"
}
```

---

## El JSON que genera OpenAI

### Modo normal

```json
{
  "concepto": "derivada de coseno",
  "pregunta": "¿Cuál es la derivada de g(x) = cos(x)?",
  "opciones": ["-sen(x)", "sen(x)", "cos(x)", "-cos(x)"],
  "respuesta_correcta": "-sen(x)"
}
```

### Modo guiado (`es_guiado=True`)

```json
{
  "concepto": "derivada de coseno",
  "explicacion": "La derivada mide la tasa de cambio de una función. Para las funciones trigonométricas existen resultados conocidos: la derivada de coseno cambia de signo respecto a la de seno.",
  "pregunta": "¿Cuál es la derivada de g(x) = cos(x)?",
  "opciones": ["-sen(x)", "sen(x)", "cos(x)", "-cos(x)"],
  "respuesta_correcta": "-sen(x)"
}
```

La diferencia es el campo `explicacion` y que `max_tokens` sube de `600` a `800` para darle espacio a la IA de escribir la explicacion.

### Como se extrae la respuesta de OpenAI

```python
respuesta = client.chat.completions.create(
    model='gpt-4o-mini',
    max_tokens=max_tokens,
    messages=[{'role': 'user', 'content': mensaje}]
)

return json.loads(respuesta.choices[0].message.content)
```

`respuesta.choices[0].message.content` contiene el texto que genero el modelo. Como le pedimos que responda SOLO con JSON, se parsea directamente con `json.loads()`.

---

## Como se evalua la respuesta del estudiante

En `vista_responder.py`, la evaluacion es una comparacion exacta de strings:

```python
es_correcta = respuesta == pregunta_actual['respuesta_correcta']
```

La respuesta del estudiante debe coincidir exactamente con el texto de la opcion correcta tal como vino en el JSON de OpenAI. Por eso el campo `respuesta_correcta` del JSON dice "texto exacto de la opcion correcta" — la IA debe devolver en ese campo el mismo texto que puso en el array `opciones`.

---

## Ajuste de dificultad

Despues de evaluar la respuesta, `_ajustar_dificultad()` modifica la dificultad de la siguiente pregunta:

```python
def _ajustar_dificultad(sesion, es_correcta):
    if es_correcta and sesion.dificultad_actual < 3:
        sesion.dificultad_actual += 1
    elif not es_correcta and sesion.dificultad_actual > 1:
        sesion.dificultad_actual -= 1
```

| Resultado | Dificultad actual | Nueva dificultad |
|-----------|------------------|-----------------|
| Correcta | 1 (Facil) | 2 (Media) |
| Correcta | 2 (Media) | 3 (Dificil) |
| Correcta | 3 (Dificil) | 3 (sin cambio, es el maximo) |
| Incorrecta | 3 (Dificil) | 2 (Media) |
| Incorrecta | 2 (Media) | 1 (Facil) |
| Incorrecta | 1 (Facil) | 1 (sin cambio, es el minimo) |

La nueva dificultad se incluye en el siguiente prompt para que OpenAI genere una pregunta acorde.

---

## Actualizacion del modelo de conocimiento

Despues de cada respuesta, `actualizar_modelo_conocimiento()` actualiza el registro del concepto evaluado:

```python
def actualizar_modelo_conocimiento(conceptos, concepto, es_correcta):
    if concepto not in conceptos:
        conceptos[concepto] = {'intentos': 0, 'correctas': 0, 'nivel': 2}

    conceptos[concepto]['intentos'] += 1
    if es_correcta:
        conceptos[concepto]['correctas'] += 1

    tasa = correctas / intentos
    if tasa >= 0.8:
        nivel = 3   # Dominado
    elif tasa >= 0.5:
        nivel = 2   # En desarrollo
    else:
        nivel = 1   # Débil
```

**Niveles:**
- `1` — Debil: menos del 50% de aciertos en ese concepto
- `2` — En desarrollo: entre 50% y 79% de aciertos
- `3` — Dominado: 80% o mas de aciertos

Si el concepto aparece por primera vez, se inicializa en nivel `2` (neutral) para no penalizar al estudiante antes de tener datos suficientes.

**Ejemplo de evolucion:**

```
Intento 1 — "derivada de coseno" — Incorrecta
→ intentos: 1, correctas: 0, tasa: 0%  → nivel 1 (Débil)

Intento 2 — "derivada de coseno" — Correcta
→ intentos: 2, correctas: 1, tasa: 50% → nivel 2 (En desarrollo)

Intento 3 — "derivada de coseno" — Correcta
→ intentos: 3, correctas: 2, tasa: 67% → nivel 2 (En desarrollo)

Intento 4 — "derivada de coseno" — Correcta
→ intentos: 4, correctas: 3, tasa: 75% → nivel 2 (En desarrollo)

Intento 5 — "derivada de coseno" — Correcta
→ intentos: 5, correctas: 4, tasa: 80% → nivel 3 (Dominado) ✓
```

---

## Como decide si el examen termina

`_debe_terminar()` evalua la condicion de fin segun el modo del examen:

### Modo fijo
```python
if respondidas >= examen.num_preguntas:
    return True, 'preguntas_completadas'
```
Termina cuando el estudiante responde exactamente `num_preguntas` preguntas.

### Modo maestria
```python
limite_alcanzado = respondidas >= examen.max_preguntas
minimo_cumplido  = respondidas >= examen.num_preguntas
todos_dominados  = all(d['nivel'] >= 3 for d in modelo_conceptos.values())

if limite_alcanzado:
    return True, 'limite_alcanzado'
if minimo_cumplido and todos_dominados:
    return True, 'conceptos_dominados'
```

Puede terminar por dos razones:
- `conceptos_dominados` — el estudiante domino todos los conceptos (nivel 3) y ya respondio el minimo de preguntas.
- `limite_alcanzado` — se alcanzo `max_preguntas` aunque no domine todo.

La razon de fin (`razon_fin`) se incluye en la respuesta final para que el frontend la muestre.

---

## Calculo de puntaje y nota

Al terminar el examen:

```python
puntaje = round((correctas / total_real) * 100, 2)   # 0.0 a 100.0
nota    = round(1.0 + (correctas / total_real) * 4.0, 1)  # 1.0 a 5.0
```

| Porcentaje de aciertos | Nota |
|------------------------|------|
| 0% | 1.0 |
| 25% | 2.0 |
| 50% | 3.0 |
| 75% | 4.0 |
| 100% | 5.0 |

En modo maestria, `total_real` es el numero de preguntas que realmente se respondieron (puede ser mayor que `num_preguntas`), no el numero configurado inicialmente.

---

## Retroalimentacion opcional

Si el examen tiene `retroalimentacion=True`, cada respuesta incluye:

```json
{
  "retroalimentacion": {
    "es_correcta": false,
    "respuesta_correcta": "-sen(x)",
    "concepto": "derivada de coseno"
  }
}
```

Si `retroalimentacion=False`, el campo llega como `null`. El estudiante no sabe si acerto hasta ver el resultado final.

---

## Persistencia entre sesiones

El `ModeloConocimiento` persiste entre intentos del mismo examen. Si un estudiante toma el examen por segunda vez, el sistema ya sabe que conceptos domina y cuales son debiles, y el prompt incluye esa informacion desde la primera pregunta del nuevo intento. Esto hace que cada intento sea mas personalizado que el anterior.
