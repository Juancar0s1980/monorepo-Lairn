"""
Generación de temas de estudio y respuestas de chat con IA, acotadas a un
curso puntual.

Dos flujos:
1. `generar_temas_estudio`: a partir del nombre/descripción del curso (y sus
   objetivos de aprendizaje, si tiene) genera borradores de temas de estudio.
   A diferencia de `sugerir_objetivos` / `generar_borrador_pregunta`, estos
   borradores SÍ se persisten de inmediato (como `pendiente`, ver
   `apps.campo_estudio.models.TemaEstudio`): el docente necesita una cola que
   pueda revisar más tarde, no solo un modal en el momento de generar.
2. `responder_pregunta_tema`: responde una pregunta de un estudiante sobre un
   tema ya aprobado. El prompt ancla la respuesta al tema y al curso, y
   rechaza explícitamente cualquier pregunta fuera de ese alcance para que
   esto no se convierta en un asistente de IA de propósito general.
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia

MAX_INTENTOS = 2


def generar_temas_estudio(
    nombre_curso: str,
    descripcion_curso: str = '',
    objetivos: list = None,
    existentes: list = None,
    cantidad: int = 5,
) -> list[dict]:
    """
    Sugiere temas de estudio para un curso. Devuelve una lista de dicts
    `{"titulo": str, "contenido": str}`. La respuesta se valida (estructura,
    tipos, no vacío) y se reintenta si viene mal formada.
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    objetivos = objetivos or []
    existentes = existentes or []

    bloque_descripcion = f'Descripción del curso: "{descripcion_curso}"\n' if descripcion_curso.strip() else ''

    bloque_objetivos = ''
    if objetivos:
        lineas = '\n'.join(f'- {o}' for o in objetivos)
        bloque_objetivos = f'\nObjetivos de aprendizaje del curso (los temas deben ayudar a cubrirlos):\n{lineas}\n'

    bloque_existentes = ''
    if existentes:
        lineas = '\n'.join(f'- {t}' for t in existentes)
        bloque_existentes = f'\nTemas de estudio que el curso YA tiene (no los repitas ni los reformules):\n{lineas}\n'

    mensaje = f"""Eres un asistente pedagógico que prepara material de estudio para un curso universitario.
Genera {cantidad} temas de estudio distintos para que un estudiante repase por su cuenta.
Tu única salida debe ser un objeto JSON válido, sin texto adicional.

Nombre del curso: "{nombre_curso}"
{bloque_descripcion}{bloque_objetivos}{bloque_existentes}
Reglas para cada tema:
1. "titulo": máximo 12 palabras, específico (nada de "Introducción general").
2. "contenido": explicación clara de 3 a 6 párrafos cortos en español, con
   ejemplos cuando ayude, dirigida a un estudiante que ya vio el tema en
   clase y quiere repasarlo (no es la primera vez que lo ve).
3. Cada tema cubre un sub-tema distinto del curso, sin solaparse entre sí ni
   con los temas existentes.
4. No inventes contenido fuera del alcance del curso descrito arriba.

Formato de salida (únicamente esta clave):
{{"temas": [{{"titulo": "...", "contenido": "..."}}, ...]}}"""

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 3000},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            temas = datos.get('temas')
            if not isinstance(temas, list) or not temas:
                raise ValueError('la clave "temas" falta o no es una lista con elementos')

            validados = []
            for tema in temas:
                if not isinstance(tema, dict):
                    raise ValueError('cada tema debe ser un objeto')
                titulo = str(tema.get('titulo', '')).strip()
                contenido = str(tema.get('contenido', '')).strip()
                if not titulo or not contenido:
                    raise ValueError('cada tema necesita "titulo" y "contenido" no vacíos')
                validados.append({'titulo': titulo[:150], 'contenido': contenido})

            if not validados:
                raise ValueError('todos los temas vinieron vacíos')
            return validados[:cantidad]
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo temas de estudio válidos tras {MAX_INTENTOS} intentos: {ultimo_error}')


def responder_pregunta_tema(
    nombre_curso: str,
    titulo_tema: str,
    contenido_tema: str,
    historial: list,
    pregunta: str,
) -> str:
    """
    Responde una pregunta de un estudiante sobre un tema de estudio ya
    aprobado. `historial` es una lista de dicts `{"rol": "estudiante"|"ia",
    "contenido": str}` con los mensajes previos del hilo (más recientes al
    final), usada para mantener contexto conversacional.
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    sistema = f"""Eres un tutor de IA que ayuda a un estudiante a repasar UN tema puntual del curso "{nombre_curso}".

Tema: "{titulo_tema}"
Contenido del tema:
\"\"\"
{contenido_tema}
\"\"\"

Reglas estrictas:
1. Responde ÚNICAMENTE sobre este tema y su relación con el curso "{nombre_curso}".
2. Si el estudiante pregunta algo sin relación con este tema (otra materia, tareas
   de otro curso, temas generales fuera de este contenido, etc.), NO lo respondas:
   indícale amablemente que solo puedes ayudarlo con "{titulo_tema}" y sugiérele
   volver a esa parte del curso.
3. Responde en español, de forma clara y concisa, con ejemplos cuando ayuden.
4. No inventes datos que contradigan el contenido del tema."""

    mensajes = [{'role': 'system', 'content': sistema}]
    for m in historial:
        rol_openai = 'assistant' if m.get('rol') == 'ia' else 'user'
        mensajes.append({'role': rol_openai, 'content': m.get('contenido', '')})
    mensajes.append({'role': 'user', 'content': pregunta})

    respuesta = client.chat.completions.create(
        model=modelo,
        messages=mensajes,
        **{kwarg_max_tokens: 1200},
    )
    contenido = respuesta.choices[0].message.content
    if not contenido or not contenido.strip():
        raise ValueError('la IA no produjo una respuesta')
    return contenido.strip()
