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


def _construir_contexto_objetivos(objetivos: list) -> str:
    """
    Bloque del prompt que ancla la pregunta a los objetivos del examen.

    Obliga a la IA a evaluar exactamente uno de los objetivos definidos por el
    docente y a copiar su texto literal en el campo `concepto`: eso impide que
    la generación derive hacia material fuera del temario y estabiliza las
    claves del modelo de conocimiento (sin variantes inventadas por pregunta).
    """
    if not objetivos:
        return ''

    lineas = '\n'.join(f'- {o}' for o in objetivos)
    return (
        '\n--- Objetivos de aprendizaje de este examen ---\n'
        f'{lineas}\n'
        'La pregunta DEBE evaluar exactamente UNO de estos objetivos. '
        'En el campo "concepto" copia el texto del objetivo evaluado '
        'EXACTAMENTE igual, sin reformularlo ni abreviarlo.\n'
        '---'
    )


def generar_pregunta(
    tema: str,
    dificultad: int,
    historial: list,
    guiado: bool = False,
    modelo_conocimiento: dict = None,
    objetivos: list = None
) -> dict:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    historial_texto = ''
    if historial:
        historial_texto = '\nPreguntas ya realizadas (no repetir):\n'
        for h in historial:
            historial_texto += f'- {h["pregunta"]}\n'

    contexto_conocimiento = _construir_contexto_conocimiento(modelo_conocimiento)
    contexto_objetivos = _construir_contexto_objetivos(objetivos)

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
        # gpt-5.5 razona antes de responder y sus tokens de razonamiento consumen
        # este presupuesto: si queda corto, el contenido llega VACÍO. El tope es
        # solo un techo (se factura lo usado), así que se deja margen amplio.
        max_tokens = 2500
    else:
        instruccion = 'Genera UNA pregunta de opción múltiple.'
        formato_json = """{
  "concepto": "nombre del sub-concepto específico evaluado (ej: 'derivadas parciales', 'regla de la cadena')",
  "pregunta": "texto de la pregunta",
  "opciones": ["opción A", "opción B", "opción C", "opción D"],
  "respuesta_correcta": "texto exacto de la opción correcta"
}"""
        max_tokens = 2000

    mensaje = f"""Eres un tutor inteligente adaptativo. {instruccion}

Tema general: "{tema}"
Dificultad: {DIFICULTAD_TEXTO[dificultad]}.
{contexto_objetivos}
{contexto_conocimiento}
{historial_texto}
Si el estudiante tiene conceptos débiles, genera la pregunta sobre uno de esos conceptos.
Si no hay historial de conocimiento, elige el sub-concepto más apropiado para la dificultad.

Responde SOLO con este JSON (sin texto adicional):
{formato_json}"""

    # response_format fuerza JSON válido a nivel de API; la validación posterior
    # garantiza la estructura (claves, 4 opciones, correcta ∈ opciones) antes de
    # entregarla al examen. Un reintento cubre truncamientos o respuestas rotas
    # esporádicas del modelo; si falla dos veces, ValueError con mensaje claro.
    ultimo_error = None
    for _ in range(2):
        respuesta = client.chat.completions.create(
            model='gpt-5.5',
            max_completion_tokens=max_tokens,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}]
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            _validar_pregunta(datos, guiado)
            return datos
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo una pregunta válida tras 2 intentos: {ultimo_error}')


def _validar_pregunta(datos: dict, guiado: bool) -> None:
    """
    Valida la estructura de la pregunta generada antes de usarla en el examen.

    Protege el flujo del estudiante de respuestas rotas del modelo: claves
    faltantes, opciones repetidas o una `respuesta_correcta` que no coincide
    carácter por carácter con ninguna opción (la evaluación en vista_responder
    compara por igualdad exacta, así que ese caso haría la pregunta imposible).
    """
    if not isinstance(datos, dict):
        raise ValueError('la respuesta no es un objeto JSON')

    requeridas = ['concepto', 'pregunta', 'opciones', 'respuesta_correcta']
    if guiado:
        requeridas.append('explicacion')
    faltantes = [c for c in requeridas if not datos.get(c)]
    if faltantes:
        raise ValueError(f'faltan claves o vienen vacías: {", ".join(faltantes)}')

    opciones = datos['opciones']
    if not isinstance(opciones, list) or len(opciones) != 4:
        raise ValueError('debe haber exactamente 4 opciones')
    if not all(isinstance(o, str) and o.strip() for o in opciones):
        raise ValueError('todas las opciones deben ser textos no vacíos')
    if len(set(opciones)) != 4:
        raise ValueError('las opciones deben ser distintas entre sí')
    if datos['respuesta_correcta'] not in opciones:
        raise ValueError('respuesta_correcta no coincide con ninguna opción')


def sugerir_objetivos(
    nombre_curso: str,
    descripcion_curso: str = '',
    existentes: list = None,
    cantidad: int = 5
) -> list:
    """
    Sugiere objetivos de aprendizaje para un curso a partir de su nombre y
    descripción. Devuelve una lista de strings (borradores): el docente los
    curata en la UI y solo se guardan los que él acepte.

    Si ya hay objetivos definidos, se pasan para que las sugerencias los
    complementen en vez de repetirlos. La respuesta del modelo se valida
    (estructura, tipos y longitud) y se reintenta una vez si viene mal; si
    falla de nuevo se lanza ValueError con mensaje claro para los logs.
    """
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    existentes = existentes or []
    bloque_existentes = ''
    if existentes:
        lineas = '\n'.join(f'- {o}' for o in existentes)
        bloque_existentes = (
            f'\nObjetivos que el curso YA tiene (no los repitas ni los reformules):\n{lineas}\n'
        )

    bloque_descripcion = f'Descripción del curso: "{descripcion_curso}"\n' if descripcion_curso.strip() else ''

    mensaje = f"""Genera {cantidad} objetivos de aprendizaje para un curso universitario.
Tu única salida debe ser un objeto JSON válido, sin texto adicional.

Nombre del curso: "{nombre_curso}"
{bloque_descripcion}{bloque_existentes}
Reglas para cada objetivo:
1. Una sola oración de máximo 15 palabras, que empiece con un verbo en
   infinitivo (ej.: "Aplicar la regla de la cadena en funciones compuestas").
2. Concreto y evaluable con preguntas de opción múltiple: nada de objetivos
   vagos como "entender el tema" o "aprender los conceptos básicos".
3. Cada objetivo debe cubrir un sub-tema distinto del curso (sin solaparse
   entre sí ni con los objetivos existentes).
4. En español.

Formato de salida (únicamente esta clave):
{{"objetivos": ["objetivo 1", "objetivo 2", "..."]}}"""

    ultimo_error = None
    for _ in range(2):
        respuesta = client.chat.completions.create(
            model='gpt-5.5',
            # Margen amplio: los tokens de razonamiento de gpt-5.5 consumen este
            # presupuesto y un tope corto devuelve contenido vacío (ver generar_pregunta).
            max_completion_tokens=2000,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}]
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            objetivos = datos.get('objetivos')
            if not isinstance(objetivos, list) or not objetivos:
                raise ValueError('la clave "objetivos" falta o no es una lista con elementos')
            objetivos = [str(o).strip() for o in objetivos if str(o).strip()]
            if not objetivos:
                raise ValueError('todos los objetivos vinieron vacíos')
            # Recorte defensivo: respeta el límite del modelo ObjetivoCurso (200 chars).
            return [o[:200] for o in objetivos[:cantidad]]
        except (json.JSONDecodeError, ValueError) as e:
            ultimo_error = e

    raise ValueError(f'La IA no produjo objetivos válidos tras 2 intentos: {ultimo_error}')


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
