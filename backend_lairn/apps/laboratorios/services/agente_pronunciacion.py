"""
Práctica de pronunciación (`Pregunta.tipo='pronunciacion'`): el estudiante
escucha una palabra/frase pronunciada correctamente y graba su propia voz
intentando repetirla.

Dos capacidades de IA, ninguna necesita API key propia del proyecto más allá
de lo que ya está configurado:

- `generar_audio_referencia`: texto → audio, con Edge TTS (paquete
  `edge-tts`, sin API key — usa la función "Leer en voz alta" de Microsoft
  Edge). Determinista y gratis: se puede regenerar en cualquier momento sin
  depender de guardar bytes de un paso anterior.
- `transcribir_audio`: audio → texto, con Whisper de Groq. Usa un cliente
  DEDICADO a Groq (no `obtener_cliente_ia()` de `ia_client.py`, que podría
  estar apuntando a openai/grok según `AI_PROVIDER`) porque Whisper solo lo
  ofrece Groq de los tres proveedores configurados en este proyecto.

La calificación (`calcular_similitud`) es una comparación de texto entre lo
que se esperaba y lo que Whisper transcribió — NO hay evaluación fonética
fina de acento (eso requeriría modelos especializados de pago); esto solo
detecta si el estudiante dijo la palabra/frase correcta o una distinta.
"""

import asyncio
import difflib
import json
import re

import edge_tts
import openai

from django.conf import settings

from backend_lairn.ia_client import obtener_cliente_ia

VOZ_INGLES_DEFAULT = 'en-US-AriaNeural'
MODELO_WHISPER = 'whisper-large-v3-turbo'


def generar_audio_referencia(texto: str, voz: str = VOZ_INGLES_DEFAULT) -> bytes:
    async def _generar():
        comunicar = edge_tts.Communicate(texto, voice=voz)
        audio = bytearray()
        async for trozo in comunicar.stream():
            if trozo['type'] == 'audio':
                audio.extend(trozo['data'])
        return bytes(audio)

    return asyncio.run(_generar())


def generar_practica_pronunciacion(objetivo_texto: str, tema_curso: str) -> dict:
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    mensaje = f"""Eres un docente de inglés que diseña ejercicios de pronunciación para
estudiantes universitarios de cualquier carrera.

Curso: "{tema_curso}"
Objetivo a evaluar: "{objetivo_texto}"

Elige UNA palabra o frase corta EN INGLÉS (máximo 6 palabras) relacionada con el
objetivo del curso, que sea útil practicar pronunciando (vocabulario técnico del
tema, o una frase típica del área). No traduzcas el objetivo, solo toma un término
o frase relevante que ya seria natural usar en ese campo en inglés.

Tu única salida debe ser un objeto JSON válido, sin texto adicional:
{{"enunciado": "instrucción breve para el estudiante, en español", "texto_pronunciar": "la palabra o frase en inglés"}}"""

    ultimo_error = None
    for _ in range(2):
        try:
            respuesta = client.chat.completions.create(
                model=modelo,
                response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}],
                **{kwarg_max_tokens: 500},
            )
            datos = json.loads(respuesta.choices[0].message.content)
            if not isinstance(datos, dict):
                raise ValueError('la respuesta no es un objeto JSON')
            enunciado = str(datos.get('enunciado', '')).strip()
            texto_pronunciar = str(datos.get('texto_pronunciar', '')).strip()
            if not enunciado or not texto_pronunciar:
                raise ValueError('faltan "enunciado" o "texto_pronunciar"')
            return {'enunciado': enunciado, 'texto_pronunciar': texto_pronunciar[:300]}
        except (json.JSONDecodeError, ValueError, TypeError, openai.APIError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo una práctica de pronunciación válida tras 2 intentos: {ultimo_error}')


def generar_laboratorio_libre_pronunciacion(enunciado_docente: str, tema_curso: str, cantidad_preguntas: int = 3) -> dict:
    """
    Genera un laboratorio COMPLETO (título + instrucciones + N prácticas de
    pronunciación distintas) a partir de una descripción libre del docente.
    A diferencia de `generar_practica_pronunciacion` (una frase por objetivo
    del curso), acá se piden las N frases en un solo llamado para que no se
    repitan entre sí. El audio de referencia NO se genera aquí — se genera
    recién al aceptar cada pregunta (mismo patrón que el resto del proyecto).
    """
    cantidad_preguntas = max(1, min(cantidad_preguntas, 8))
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    mensaje = f"""Eres un docente de inglés que diseña ejercicios de pronunciación para
estudiantes universitarios de cualquier carrera.

Curso: "{tema_curso}"
Descripción del docente de qué laboratorio quiere: "{enunciado_docente}"

Genera exactamente {cantidad_preguntas} palabras o frases cortas EN INGLÉS (máximo 6 palabras
cada una), relacionadas con la descripción del docente, DISTINTAS entre sí, útiles para practicar
pronunciación (vocabulario técnico del tema, o frases típicas del área).

Tu única salida debe ser un objeto JSON válido, sin texto adicional:
{{
  "titulo": "título del laboratorio",
  "instrucciones": "instrucciones breves para el estudiante, en español",
  "preguntas": [
    {{"enunciado": "instrucción breve para el estudiante, en español", "texto_pronunciar": "la palabra o frase en inglés"}}
  ]
}}"""

    ultimo_error = None
    for _ in range(2):
        try:
            respuesta = client.chat.completions.create(
                model=modelo,
                response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}],
                **{kwarg_max_tokens: 400 + 250 * cantidad_preguntas},
            )
            datos = json.loads(respuesta.choices[0].message.content)
            if not isinstance(datos, dict):
                raise ValueError('la respuesta no es un objeto JSON')
            if not str(datos.get('titulo', '')).strip():
                raise ValueError('falta "titulo"')
            preguntas = datos.get('preguntas')
            if not isinstance(preguntas, list) or not preguntas:
                raise ValueError('falta "preguntas" o está vacía')
            for p in preguntas:
                if not isinstance(p, dict):
                    raise ValueError('cada pregunta debe ser un objeto')
                if not str(p.get('enunciado', '')).strip() or not str(p.get('texto_pronunciar', '')).strip():
                    raise ValueError('faltan "enunciado" o "texto_pronunciar"')
            return {
                'titulo': str(datos['titulo']).strip()[:200],
                'instrucciones': str(datos.get('instrucciones', '')).strip(),
                'preguntas': [
                    {
                        'enunciado': str(p['enunciado']).strip(),
                        'texto_pronunciar': str(p['texto_pronunciar']).strip()[:300],
                    }
                    for p in preguntas
                ],
            }
        except (json.JSONDecodeError, ValueError, TypeError, openai.APIError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo un laboratorio de pronunciación válido tras 2 intentos: {ultimo_error}')


def transcribir_audio(audio_bytes: bytes, nombre_archivo: str = 'audio.webm') -> str:
    client = openai.OpenAI(api_key=settings.GROQ_API_KEY, base_url='https://api.groq.com/openai/v1')
    respuesta = client.audio.transcriptions.create(
        model=MODELO_WHISPER,
        file=(nombre_archivo, audio_bytes),
        language='en',
    )
    return respuesta.text.strip()


def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    return re.sub(r'\s+', ' ', texto)


def calcular_similitud(esperado: str, transcrito: str) -> float:
    a, b = _normalizar(esperado), _normalizar(transcrito)
    if not a or not b:
        return 0.0
    return round(difflib.SequenceMatcher(None, a, b).ratio() * 100, 1)
