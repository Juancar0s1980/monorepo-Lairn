import json
import openai
from django.conf import settings


DIFICULTAD_TEXTO = {
    1: 'fácil',
    2: 'media',
    3: 'difícil',
}


def _construir_contexto_conocimiento(modelo_conocimiento: dict) -> str:
    if not modelo_conocimiento:
        return ''

    debiles = [c for c, d in modelo_conocimiento.items() if d.get('nivel', 2) <= 1]
    en_desarrollo = [c for c, d in modelo_conocimiento.items() if d.get('nivel', 2) == 2]
    dominados = [c for c, d in modelo_conocimiento.items() if d.get('nivel', 2) >= 3]

    contexto = '\n--- Modelo de conocimiento del estudiante ---'
    if debiles:
        contexto += f'\nConceptos DÉBILES (priorizar, el estudiante falla aquí): {", ".join(debiles)}'
    if en_desarrollo:
        contexto += f'\nConceptos EN DESARROLLO (reforzar): {", ".join(en_desarrollo)}'
    if dominados:
        contexto += f'\nConceptos DOMINADOS (no repetir innecesariamente): {", ".join(dominados)}'
    contexto += '\n---'
    return contexto


def generar_pregunta(
    tema: str,
    dificultad: int,
    historial: list,
    guiado: bool = False,
    modelo_conocimiento: dict = None
) -> dict:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    historial_texto = ''
    if historial:
        historial_texto = '\nPreguntas ya realizadas (no repetir):\n'
        for h in historial:
            historial_texto += f'- {h["pregunta"]}\n'

    contexto_conocimiento = _construir_contexto_conocimiento(modelo_conocimiento)

    if guiado:
        instruccion = (
            'Primero escribe una explicación breve (2-3 oraciones) del concepto clave '
            'necesario para responder la pregunta. La explicación debe ayudar al estudiante '
            'a entender el tema, pero SIN revelar cuál es la respuesta correcta. '
            'Luego genera la pregunta.'
        )
        formato_json = """{
  "concepto": "nombre del sub-concepto específico evaluado (ej: 'derivadas parciales', 'regla de la cadena')",
  "explicacion": "explicación del concepto sin revelar la respuesta",
  "pregunta": "texto de la pregunta",
  "opciones": ["opción A", "opción B", "opción C", "opción D"],
  "respuesta_correcta": "texto exacto de la opción correcta"
}"""
        max_tokens = 800
    else:
        instruccion = 'Genera UNA pregunta de opción múltiple.'
        formato_json = """{
  "concepto": "nombre del sub-concepto específico evaluado (ej: 'derivadas parciales', 'regla de la cadena')",
  "pregunta": "texto de la pregunta",
  "opciones": ["opción A", "opción B", "opción C", "opción D"],
  "respuesta_correcta": "texto exacto de la opción correcta"
}"""
        max_tokens = 600

    mensaje = f"""Eres un tutor inteligente adaptativo. {instruccion}

Tema general: "{tema}"
Dificultad: {DIFICULTAD_TEXTO[dificultad]}.
{contexto_conocimiento}
{historial_texto}
Si el estudiante tiene conceptos débiles, genera la pregunta sobre uno de esos conceptos.
Si no hay historial de conocimiento, elige el sub-concepto más apropiado para la dificultad.

Responde SOLO con este JSON (sin texto adicional):
{formato_json}"""

    respuesta = client.chat.completions.create(
        model='gpt-5.5',
        max_completion_tokens=max_tokens,
        messages=[{'role': 'user', 'content': mensaje}]
    )

    return json.loads(respuesta.choices[0].message.content)


def actualizar_modelo_conocimiento(conceptos: dict, concepto: str, es_correcta: bool) -> dict:
    if concepto not in conceptos:
        conceptos[concepto] = {'intentos': 0, 'correctas': 0, 'nivel': 2}

    conceptos[concepto]['intentos'] += 1
    if es_correcta:
        conceptos[concepto]['correctas'] += 1

    c = conceptos[concepto]
    tasa = c['correctas'] / c['intentos']
    if tasa >= 0.8:
        c['nivel'] = 3
    elif tasa >= 0.5:
        c['nivel'] = 2
    else:
        c['nivel'] = 1

    return conceptos
