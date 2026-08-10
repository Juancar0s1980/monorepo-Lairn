"""
Generación de preguntas de "respuesta abierta" con IA — la contraparte no-
código de `agente_codigo.py`. Sirve para cualquier carrera (Derecho, Inglés,
Historia, etc.): la IA no genera código ni casos de test, solo un enunciado
de ensayo/respuesta libre y la rúbrica que se usará para calificarlo (ver
`agente_evaluador.evaluar_respuesta_libre`).

Contrato deliberadamente más simple que el de código: sin lenguaje, sin
solución de referencia, sin casos de test que verificar en un sandbox — no
hay nada que "ejecutar" en una respuesta de texto libre.
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia

MAX_INTENTOS = 2


def _validar_borrador(datos: dict) -> None:
    if not isinstance(datos, dict):
        raise ValueError('la respuesta no es un objeto JSON')
    faltantes = [c for c in ('enunciado', 'criterios_ia') if c not in datos]
    if faltantes:
        raise ValueError(f'faltan claves: {", ".join(faltantes)}')
    if not str(datos['enunciado']).strip():
        raise ValueError('enunciado vacío')
    if not str(datos['criterios_ia']).strip():
        raise ValueError('criterios_ia vacío')


def generar_borrador_respuesta_libre(objetivo_texto: str, tema_curso: str) -> dict:
    """
    Pide a la IA un borrador de pregunta de respuesta abierta (ensayo/texto
    libre) para un objetivo puntual de CUALQUIER carrera. Devuelve
    `{"enunciado": "...", "criterios_ia": "..."}` sin guardar nada — el
    docente lo revisa y lo guarda con el POST normal de `/preguntas/`.
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    mensaje = f"""Eres un diseñador de evaluaciones para un curso universitario de CUALQUIER carrera
(puede ser Derecho, Inglés, Historia, Administración, Programación, etc. — no asumas que es técnico).
Genera UNA pregunta de respuesta abierta (ensayo/texto libre, NO de opción múltiple ni de código)
que evalúe exactamente el siguiente objetivo de aprendizaje. Tu única salida debe ser un objeto
JSON válido, sin texto adicional.

Curso: "{tema_curso}"
Objetivo a evaluar: "{objetivo_texto}"

Reglas:
1. "enunciado": la consigna que verá el estudiante, clara y específica sobre qué debe responder
   (ej. redactar un párrafo, analizar un caso, argumentar una posición, traducir un texto).
   Dificultad apropiada para un estudiante universitario.
2. "criterios_ia": la rúbrica de calificación, en 3-5 puntos concretos y verificables, que un
   evaluador (humano o IA) usará para poner una nota de 0 a 100. Sé específico sobre qué distingue
   una respuesta excelente de una insuficiente.
3. En español.

Formato de salida (únicamente estas claves):
{{"enunciado": "consigna para el estudiante", "criterios_ia": "rúbrica de calificación"}}"""

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 1500},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            _validar_borrador(datos)
            return {
                'enunciado': str(datos['enunciado']).strip(),
                'criterios_ia': str(datos['criterios_ia']).strip(),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo una pregunta de respuesta abierta válida tras {MAX_INTENTOS} intentos: {ultimo_error}')


def generar_laboratorio_libre_respuesta_libre(enunciado_docente: str, cantidad_preguntas: int = 3) -> dict:
    """
    Genera un laboratorio COMPLETO (título + instrucciones + N preguntas de
    respuesta abierta) a partir de una descripción libre del docente, para
    CUALQUIER carrera. Devuelve el borrador SIN GUARDAR — mismo patrón que
    `agente_codigo.generar_laboratorio_libre`.
    """
    cantidad_preguntas = max(1, min(cantidad_preguntas, 8))
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    mensaje = f"""Eres un diseñador de evaluaciones para un curso universitario de CUALQUIER carrera
(puede ser Derecho, Inglés, Historia, Administración, Programación, etc. — no asumas que es técnico).
El docente describió qué laboratorio quiere. Genera el laboratorio COMPLETO: un título, unas
instrucciones breves para el estudiante, y exactamente {cantidad_preguntas} preguntas de respuesta
abierta (ensayo/texto libre, NO de opción múltiple ni de código), todas relacionadas con la
descripción del docente pero cada una evaluando algo distinto (sin repetirse entre sí). Tu única
salida debe ser un objeto JSON válido, sin texto adicional.

Descripción del docente: "{enunciado_docente}"

Reglas por pregunta:
1. "enunciado": la consigna que verá el estudiante, clara y específica sobre qué debe responder.
   Dificultad apropiada para un estudiante universitario.
2. "criterios_ia": la rúbrica de calificación, en 3-5 puntos concretos y verificables, que un
   evaluador (humano o IA) usará para poner una nota de 0 a 100.
3. En español.

Formato de salida (únicamente estas claves):
{{
  "titulo": "título del laboratorio",
  "instrucciones": "instrucciones breves para el estudiante",
  "preguntas": [
    {{"enunciado": "consigna para el estudiante", "criterios_ia": "rúbrica de calificación"}}
  ]
}}"""

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 1000 + 600 * cantidad_preguntas},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            if not isinstance(datos, dict):
                raise ValueError('la respuesta no es un objeto JSON')
            if not str(datos.get('titulo', '')).strip():
                raise ValueError('falta "titulo"')
            preguntas = datos.get('preguntas')
            if not isinstance(preguntas, list) or not preguntas:
                raise ValueError('falta "preguntas" o está vacía')
            for pregunta in preguntas:
                _validar_borrador(pregunta)
            return {
                'titulo': str(datos['titulo']).strip()[:200],
                'instrucciones': str(datos.get('instrucciones', '')).strip(),
                'preguntas': [
                    {'enunciado': str(p['enunciado']).strip(), 'criterios_ia': str(p['criterios_ia']).strip()}
                    for p in preguntas
                ],
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo un laboratorio válido tras {MAX_INTENTOS} intentos: {ultimo_error}')
