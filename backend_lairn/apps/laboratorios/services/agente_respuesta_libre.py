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
