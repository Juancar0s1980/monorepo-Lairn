"""
Generación de contenido Saber Pro con IA (HU-20).

Dos flujos, uno por tipo de contenido del banco:

1. `generar_preguntas`: preguntas de selección múltiple para las áreas
   estructuradas (con competencia/afirmación/evidencia) y para Inglés (con la
   parte 1 a 7). Respeta la estructura de evaluación de cada área: cantidad de
   opciones, texto base exigido en Lectura Crítica e ítems en inglés para el
   módulo de Inglés (skill de Saber Pro, sección "Reglas para la IA generadora").
2. `generar_consignas`: propuestas de consigna de escritura para Comunicación
   Escrita, sin criterios ni opciones (HU-20.2).

La respuesta del modelo se valida siempre (estructura, tipos, opciones
distintas, correcta ∈ opciones) y se reintenta una vez; si vuelve mal formada
se lanza `ValueError` con mensaje claro y la vista responde 502. Mismo patrón
que `motor_adaptativo/services/agente_ia.py` y `campo_estudio/agente_estudio.py`.

Además se inyectan al prompt ejemplos auténticos del ICFES
(`services/muestras_icfes/`) como referencia de formato, extensión y nivel; la
IA debe imitarlos sin copiarlos (ver `_cargar_muestras`).
"""

import json
import re
from pathlib import Path

from backend_lairn.ia_client import obtener_cliente_ia
from apps.saber_pro.services.catalogo_saber_pro import (
    AREA_CONSIGNA,
    AREAS_ESTRUCTURA_COMPETENCIAS,
    descripciones_de_parte,
    es_parte_relacion,
    opciones_de_parte,
    parte_exige_espacios,
    parte_usa_texto_comun,
    partes_ingles,
    preguntas_de_parte,
    validar_relacion,
)

# Ejemplos auténticos del ICFES (modelo de formato/nivel), un archivo por área.
# Se leen en cada generación; la instrucción del prompt prohíbe copiarlos.
MUESTRAS_DIR = Path(__file__).resolve().parent / 'muestras_icfes'
_NOMBRE_ARCHIVO_MUESTRAS = {
    'Razonamiento Cuantitativo': 'razonamiento_cuantitativo.md',
    'Lectura Crítica': 'lectura_critica.md',
    'Competencias Ciudadanas': 'competencias_ciudadanas.md',
    'Comunicación Escrita': 'comunicacion_escrita.md',
    'Inglés': 'ingles.md',
}

# En Inglés cada parte vigente se mapea a una o más secciones del archivo de muestras
# por TAREA: la numeración del cuadernillo 2018 no coincide con la estructura vigente
# (la tarea de relacionar era la parte 2 en 2018 y es la parte 1 hoy). Las partes 2
# (avisos) y 7 (cloze de 4 opciones) no tienen ítem auténtico y documentan su formato.
_SECCIONES_INGLES_POR_PARTE = {
    1: ('clave_relacionar',),
    2: ('clave_avisos',),
    3: ('clave_conversaciones',),
    4: ('clave_texto_espacios',),
    5: ('clave_lectura_oneida', 'clave_comprension_literal'),
    6: ('clave_lectura_oneida', 'clave_comprension_inferir'),
    7: ('clave_cloze_4',),
}

_BLOQUE_MUESTRAS_ICFES = """
EJEMPLOS AUTÉNTICOS DEL EXAMEN ICFES (solo como modelo de formato, extensión y nivel):
{muestras}

REGLAS DE USO DE LOS EJEMPLOS:
- Úsalos únicamente como referencia de formato, extensión y nivel de dificultad del examen real.
- NO copies el enunciado, las opciones ni los textos base de los ejemplos.
- Crea variaciones nuevas con temáticas, datos, lugares y vocabulario distintos.
- Respeta SIEMPRE la cantidad de opciones y las reglas indicadas arriba, aun si el ejemplo muestra otro número de opciones."""

MAX_INTENTOS = 2

# Reglas académicas por área, tomadas de la skill de Saber Pro. Se inyectan en
# el prompt para que la IA no genere contenidos fuera del alcance del examen.
_BLOQUE_RAZONAMIENTO = """
Contenidos que puedes utilizar (catálogo ICFES del área):
- Estadística: tipos de representación de datos: tablas y gráficos; intersección, unión y contenencia de conjuntos; conteos simples mediante principios de suma y multiplicación; azar y probabilidad; promedio; rango estadístico; población y muestra; nociones de inferencia muestral; error de estimación.
- Álgebra y cálculo: fracciones; razones; números decimales; porcentajes; suma; resta; multiplicación; división; potenciación; notación científica; relaciones lineales y afines; razones de cambio; tasas de interés; tasas cambiarias; velocidad; aceleración.
- Geometría: triángulos; círculos; paralelogramos; esferas; paralelepípedos rectos; cilindros; medidas; paralelismo; ortogonalidad entre rectas; desigualdad triangular; sistema de coordenadas cartesianas.
Contextos (elige siempre uno):
- Familiares o personales: finanzas personales, gestión del hogar, transporte, salud, recreación.
- Laborales u ocupacionales: tareas que se desarrollan en el trabajo siempre y cuando no requieran conocimientos o habilidades técnicas propias de una ocupación específica.
- Divulgación científica: situaciones propias de la ciencia que son de conocimiento público por la naturalidad de su lenguaje o por su importancia social y cultural.
- Comunitarios o sociales: interacción social de los ciudadanos y aquello que es propio de la sociedad en su conjunto; política, economía, convivencia y cuidado del medioambiente.
Distribución oficial aproximada del examen por competencia: Interpretación y representación 33%, Formulación y ejecución 33%, Argumentación 34%."""

_BLOQUE_LECTURA = """
Tipos de texto a usar:
- Continuos literarios: novela, cuento, dramaturgia.
- Continuos informativos: ensayo, columna de opinión, crónica.
- Discontinuos literarios: caricatura, cómic.
- Discontinuos informativos: etiqueta, infografía, tabla, diagrama, aviso publicitario, manual, reglamento.
Distribución aproximada por afirmación: contenidos locales 26%, articulación global 40%, reflexión y evaluación 34%.
Cada pregunta DEBE traer en "contexto" un texto base de máximo 500 palabras sobre el que se pregunta (para textos discontinuos, descríbelos con sus elementos)."""

_BLOQUE_CIUDADANAS = """
Temáticas permitidas:
- Constitución política de Colombia y sus principios fundamentales.
- Derechos y deberes que la Constitución consagra.
- Organización del Estado de acuerdo con la Constitución.
- Pertinencia y solidez de enunciados y discursos: prejuicios, intenciones, solidez y pertinencia de argumentos.
- Existencia y análisis de diferentes perspectivas en situaciones donde interactúan diferentes partes: posiciones, intereses, conflicto, cosmovisiones, ideologías y roles sociales.
- Problemas y soluciones entendidos como dimensiones relacionadas: relaciones entre dimensiones y efectos de una solución en cada dimensión.
Contextos: situaciones ciudadanas, sociales o públicas concretas, en español neutro.
Distribución oficial aproximada del examen por competencia: Conocimientos 30%, Argumentación 20%, Multiperspectivismo 30%, Pensamiento sistémico 20%."""

# Reglas fijas de cada pregunta; el bloque de idioma cambia en Inglés.
_REGLAS_PREGUNTA = """
Reglas para cada pregunta:
1. "enunciado": la pregunta clara y autocontenida. {idioma}
2. "opciones": exactamente {opciones} textos distintos entre sí; solo uno es correcto.
3. "respuesta_correcta": el texto EXACTO de una de las opciones, idéntico carácter por carácter.
4. "contexto": texto base o situación que enmarca la pregunta; vacío si no aplica{nota_contexto}.
5. Dificultad media de examen; nada de trampas ni redacciones ambiguas.
6. Las preguntas deben ser distintas entre sí y no repetir material ya existente del banco."""

# Parte 1 de Inglés: tarea de relacionar, no es de opción múltiple, así que no
# existe "respuesta_correcta" única; la respuesta vive en cada relación.
_REGLAS_RELACION = """
Reglas para cada ejercicio (es una tarea de RELACIONAR, NO es opción múltiple):
1. "enunciado": las instrucciones de la tarea, claras y autocontenidas. {idioma}
2. "opciones": exactamente {opciones} palabras distintas entre sí, presentadas como listado de respuesta de la letra A a la H.
3. "relaciones": exactamente {descripciones} objetos, uno por cada descripción: {{"descripcion": "...", "respuesta": "..."}}.
   - "descripcion": una frase breve que el estudiante debe emparejar con una de las {opciones} palabras.
   - "respuesta": EXACTAMENTE una de las {opciones} opciones, idéntica carácter por carácter.
   - Dos descripciones nunca comparten la misma palabra.
   - Solo {descripciones} de las {opciones} palabras se usan: las otras {distractores} son distractores y NO deben corresponder a ninguna descripción.
4. "contexto": déjalo vacío ("").
5. Dificultad media de examen; nada de trampas ni redacciones ambiguas.
6. Los ejercicios deben ser distintos entre sí y no repetir material ya existente del banco."""


# Tarea académica específica de cada parte de Inglés (2 a 7) cuando el bloque se
# genera completo. La parte 1 es de relacionar y usa `_REGLAS_RELACION`; estas
# reglas describen la tarea del examen real para el resto de las partes.
_BLOQUE_TAREA_POR_PARTE_INGLES = {
    2: 'La parte son AVISOS breves: cada pregunta muestra un aviso y el estudiante '
       'identifica en qué lugar probablemente lo encontraría.',
    3: 'La parte son CONVERSACIONES incompletas: cada pregunta muestra la primera '
       'parte de una conversación y el estudiante selecciona la opción que mejor la completa.',
    4: 'La parte es un TEXTO de conocimiento general con espacios numerados '
       '(__1__, __2__, ...): cada pregunta se basa en un espacio y el estudiante '
       'selecciona la palabra adecuada para completarlo.',
    5: 'La parte es un TEXTO de conocimiento general: cada pregunta es un enunciado '
       'sobre información EXPLÍCITA del texto, reformulado con paráfrasis.',
    6: 'La parte es un TEXTO de conocimiento general: cada pregunta exige INFERIR '
       'información que no está literal en el texto.',
    7: 'La parte es un TEXTO de conocimiento general con espacios numerados '
       '(__1__, __2__, ...): cada pregunta se basa en un espacio y el estudiante '
       'selecciona la palabra adecuada según el contexto.',
}

# Reglas de un bloque completo de una parte de Inglés (2 a 7). El bloque replica
# la estructura del examen: un texto base (cuando la parte lo usa) + todas sus
# preguntas, por eso no existe "respuesta_correcta" a nivel de bloque.
_REGLAS_BLOQUE_INGLES = """
Reglas para el bloque (respeta la estructura del examen real):
1. "enunciado": las instrucciones generales del bloque, claras y autocontenidas. {idioma}
2. "contexto": {contexto_indicacion}
3. "preguntas": exactamente {cantidad} preguntas distintas. Cada pregunta:
   - "enunciado": la pregunta o situación, clara y autocontenida. {idioma}
   - "opciones": exactamente {opciones} textos distintos entre sí; solo uno es correcto.
   - "respuesta_correcta": el texto EXACTO de una de las opciones, idéntico carácter por carácter.
4. Dificultad media de examen; nada de trampas ni redacciones ambiguas.
5. No repitas material ya existente del banco."""


def generar_preguntas(
    area_nombre: str,
    cantidad: int = 3,
    competencia: str = '',
    afirmacion: str = '',
    evidencia: str = '',
    parte: int = None,
) -> list[dict]:
    """
    Genera preguntas de selección múltiple del banco (HU-20.1).

    Parámetros:
    - `area_nombre`: nombre del área; define las reglas y la cantidad de opciones.
    - `competencia`/`afirmacion`/`evidencia`: criterios seleccionados por el
      docente en áreas estructuradas (la evidencia es opcional, ver el modelo).
    - `parte`: parte 1 a 7 del examen de Inglés; si viene, se ignoran los criterios.

    Devuelve:
    - Para áreas estructuradas: dicts `{"enunciado", "opciones",
      "respuesta_correcta", "contexto"}`.
    - Para la parte 1 de Inglés: dicts `{"enunciado", "opciones", "relaciones",
      "respuesta_correcta": "", "contexto"}` (relacionar descripciones con palabras).
    - Para las partes 2 a 7: UN solo dict `{"enunciado", "contexto", "preguntas":
      [{"enunciado", "opciones", "respuesta_correcta"}]}` que replica el bloque del
      examen real (la vista fuerza `cantidad=1` en Inglés).
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    es_relacion = False
    if parte is not None:
        detalle_parte = next((p for p in partes_ingles() if p['numero'] == parte), None)
        if detalle_parte is None:
            raise ValueError(f'la parte {parte} no existe (debe estar entre 1 y 7)')
        es_relacion = es_parte_relacion(parte)
        if not es_relacion:
            # Partes 2 a 7: la parte completa se genera como un SOLO bloque que
            # replica el examen (texto base + sus preguntas) y se persiste en una
            # fila del banco. La generación ignora `cantidad`: la cantidad de
            # preguntas la define el examen real (ver PREGUNTAS_POR_PARTE_INGLES).
            return _generar_bloque_parte_ingles(client, modelo, kwarg_max_tokens, parte, detalle_parte)
        opciones = detalle_parte['opciones']
        contexto_requerido = False
        es_relacion = es_parte_relacion(parte)
        idioma = (
            'Redacta TODO el contenido en inglés (enunciado, descripciones y palabras).'
            if es_relacion
            else 'Redacta TODO el contenido en inglés (enunciado y opciones).'
        )
        bloque_area = (
            f'Genera la parte {parte} del examen de Inglés de nivel universitario: '
            f'{detalle_parte["descripcion"]}\n'
            f'Peso de la parte en el examen: {detalle_parte["peso"]}%.\n'
            'El módulo evalúa la competencia para comunicarse efectivamente en inglés y '
            'clasifica el desempeño según niveles del MCER.\n'
            'Usa un texto de conocimiento general apropiado cuando la parte lo requiera.'
        )
    elif area_nombre in AREAS_ESTRUCTURA_COMPETENCIAS:
        opciones = 4
        contexto_requerido = area_nombre == 'Lectura Crítica'
        idioma = 'Redacta en español neutro.'
        bloques = {
            'Razonamiento Cuantitativo': _BLOQUE_RAZONAMIENTO,
            'Lectura Crítica': _BLOQUE_LECTURA,
            'Competencias Ciudadanas': _BLOQUE_CIUDADANAS,
        }
        bloque_criterios = f'Criterios de evaluación que la pregunta DEBE cubrir:\n- Competencia: {competencia}'
        if afirmacion:
            bloque_criterios += f'\n- Afirmación: {afirmacion}'
        if evidencia:
            bloque_criterios += f'\n- Evidencia observable: {evidencia}'
        bloque_area = (
            f'{bloque_criterios}\n{bloques[area_nombre]}\n'
            'La afirmación y la evidencia deben reflejarse en el contenido de la pregunta, '
            'sin copiarlas literalmente en el enunciado.'
        )
    else:
        # Ámbito de seguridad: solo las áreas con evaluación de selección múltiple
        # llegan acá; Comunicación Escrita se genera con `generar_consignas` y la
        # validación de estructura ocurre en el serializador y en la vista.
        raise ValueError(f'el área "{area_nombre}" no admite generación de selección múltiple')

    if es_relacion:
        descripciones = descripciones_de_parte(parte)
        encabezado = (
            f'Genera {cantidad} ejercicios de relacionar distintos, cada uno con '
            f'{descripciones} descripciones y {opciones} palabras listadas de la letra A a la H.'
        )
        reglas = _REGLAS_RELACION.format(
            idioma=idioma,
            opciones=opciones,
            descripciones=descripciones,
            distractores=opciones - descripciones,
        )
        contrato = (
            '{"preguntas": [{"enunciado": "...", "opciones": ["palabra", ...], '
            '"relaciones": [{"descripcion": "...", "respuesta": "..."}, ...], "contexto": ""}, ...]}'
        )
    else:
        encabezado = (
            f'Genera {cantidad} preguntas de selección múltiple distintas, cada una con '
            f'{opciones} opciones y UNA única respuesta correcta.'
        )
        reglas = _REGLAS_PREGUNTA.format(
            idioma=idioma,
            opciones=opciones,
            nota_contexto=_nota_contexto(contexto_requerido),
        )
        contrato = (
            '{"preguntas": [{"enunciado": "...", "opciones": ["...", "...", "...", "..."], '
            '"respuesta_correcta": "...", "contexto": "..."}, ...]}'
        )

    bloque_muestras = _bloque_muestras_icfes(_cargar_muestras(area_nombre, parte))
    mensaje = f"""Eres diseñador de ítems del examen Saber Pro de Colombia.
{encabezado}
Área: {area_nombre}.
{bloque_area}
{reglas}
{bloque_muestras}

Tu única salida debe ser un objeto JSON válido, sin texto adicional, usando EXACTAMENTE estos nombres de clave en español:
{contrato}"""

    return _llamar_y_validar(
        client,
        modelo,
        kwarg_max_tokens,
        mensaje,
        clave='preguntas',
        cantidad=cantidad,
        validador=(
            _validar_relacion
            if es_relacion
            else lambda datos: _validar_pregunta(datos, opciones, contexto_requerido)
        ),
        max_tokens=8000,
        tipo='preguntas',
    )


def _generar_bloque_parte_ingles(client, modelo, kwarg_max_tokens, parte: int, detalle_parte: dict) -> list[dict]:
    """Genera la parte completa de Inglés (2 a 7) como un solo bloque del examen.

    Devuelve `[{"enunciado", "contexto", "preguntas": [{enunciado, opciones,
    respuesta_correcta}]}]`. El bloque replica el examen real: las partes 4 a 7
    comparten un texto base en `contexto` (con espacios numerados `__N__` en 4 y
    7) y las partes 2 y 3 son ítems autocontenidos por pregunta. La cantidad de
    preguntas la fija `PREGUNTAS_POR_PARTE_INGLES`, no el docente.
    """
    opciones = detalle_parte['opciones']
    cantidad = preguntas_de_parte(parte)
    usa_texto = parte_usa_texto_comun(parte)
    exige_espacios = parte_exige_espacios(parte)
    idioma = 'Redacta TODO el contenido en inglés (instrucción del bloque, texto y preguntas).'

    if usa_texto:
        if exige_espacios:
            contexto_indicacion = (
                f'un texto de conocimiento general con exactamente {cantidad} espacios '
                f'numerados __N__ (__1__ a __{cantidad}__); cada pregunta hace referencia a su espacio.'
            )
        else:
            contexto_indicacion = (
                'un texto de conocimiento general (de 3 a 4 párrafos) del que dependen '
                'todas las preguntas del bloque.'
            )
    else:
        contexto_indicacion = 'déjalo vacío (""): cada pregunta es autocontenida.'

    bloque_area = (
        f'Genera la parte {parte} del examen de Inglés de nivel universitario como UN solo bloque.\n'
        f'{_BLOQUE_TAREA_POR_PARTE_INGLES[parte]}\n'
        f'Peso de la parte en el examen: {detalle_parte["peso"]}%.\n'
        'El módulo evalúa la competencia para comunicarse efectivamente en inglés y '
        'clasifica el desempeño según niveles del MCER.'
    )
    reglas = _REGLAS_BLOQUE_INGLES.format(
        idioma=idioma,
        contexto_indicacion=contexto_indicacion,
        cantidad=cantidad,
        opciones=opciones,
    )
    contrato = (
        '{"bloques": [{"enunciado": "...", "contexto": "...", '
        '"preguntas": [{"enunciado": "...", "opciones": ["...", "..."], '
        '"respuesta_correcta": "..."}, ...]}]}'
    )

    bloque_muestras = _bloque_muestras_icfes(_cargar_muestras('Inglés', parte))
    mensaje = f"""Eres diseñador de ítems del examen Saber Pro de Colombia.
{bloque_area}
{reglas}
{bloque_muestras}

Tu única salida debe ser un objeto JSON válido, sin texto adicional, usando EXACTAMENTE estos nombres de clave en español:
{contrato}"""

    return _llamar_y_validar(
        client,
        modelo,
        kwarg_max_tokens,
        mensaje,
        clave='bloques',
        cantidad=1,
        validador=lambda datos: _validar_bloque_ingles(datos, parte),
        max_tokens=8000,
        tipo='bloques de la parte de Inglés',
    )


def generar_consignas(cantidad: int = 3) -> list[dict]:
    """
    Genera consignas de producción escrita para Comunicación Escrita (HU-20.2).

    Devuelve dicts `{"tema", "contexto", "enunciado"}` listos para persistirse
    como `tipo='consigna_escrita'`: `tema` es la problemática, `contexto` la
    situación que la enmarca y `enunciado` la consigna que lee el estudiante.
    """
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    muestras = _bloque_muestras_icfes(_cargar_muestras(AREA_CONSIGNA))
    mensaje = f"""Eres docente de escritura universitaria y diseñas consignas de Comunicación Escrita del examen Saber Pro.
Genera {cantidad} consignas de producción escrita distintas.

Área: {AREA_CONSIGNA}.
Estructura de la tarea (NO uses competencia, afirmación ni evidencia):
Comunicación Escrita → tipo de tarea: texto argumentativo → tema/problemática → contexto → pregunta/consigna.
Cada consigna pide producir un TEXTO ARGUMENTATIVO de máximo dos páginas a partir de una temática propuesta.

Aspectos que la consigna debe permitir evaluar:
1. Planteamiento del texto: desarrollar claramente el tema propuesto y construir y defender una posición; indicar el sentido en que se toma cada elemento informativo del contexto y analizarlo desde perspectivas propias; elaborar la información del contexto sin copiarla. Se penalizan ambigüedades, repeticiones innecesarias, redundancias y la copia sin elaboración.
2. Organización del texto: evidencia de planeación, secuencialidad, cohesión, conectores, puntuación y jerarquización de la información, con las partes definidas de manera apropiada al tipo de tarea. Se penalizan la jerarquización deficiente, las unidades no cohesionadas y la información impertinente o irrelevante.
3. Forma de expresión: lenguaje apropiado para el auditorio y afín al propósito comunicativo (sustentar un planteamiento, demostrar una afirmación, justificar una opinión, explicar un punto de vista), vocabulario adecuado y cierta elaboración del lenguaje con recursos estilísticos (metáforas, comparaciones, citas). Se penaliza el manejo deficiente del lenguaje que impida la comprensión.

Reglas para cada consigna:
1. "tema": la temática o problemática, concreta y debatible (máximo 20 palabras).
2. "contexto": la situación o información que enmarca la tarea (2 a 4 oraciones).
3. "enunciado": la consigna tal como la lee el estudiante: qué debe escribir, de cuánto y con qué propósito.
4. Temáticas variadas y pertinentes para estudiantes universitarios de Colombia.
5. NO generes preguntas de opción múltiple: esto es escritura abierta.
{muestras}

Tu única salida debe ser un objeto JSON válido, sin texto adicional, usando EXACTAMENTE estos nombres de clave en español:
{{"consignas": [{{"tema": "...", "contexto": "...", "enunciado": "..."}}, ...]}}"""

    return _llamar_y_validar(
        client,
        modelo,
        kwarg_max_tokens,
        mensaje,
        clave='consignas',
        cantidad=cantidad,
        validador=_validar_consigna,
        max_tokens=3000,
        tipo='consignas',
    )


def _nota_contexto(contexto_requerido: bool) -> str:
    """Frase de la regla 4 según el área: Lectura Crítica exige texto base."""
    if contexto_requerido:
        return ', OBLIGATORIO en Lectura Crítica (texto base de máximo 500 palabras)'
    return ''


def _cargar_muestras(area_nombre: str, parte: int = None) -> str:
    """Devuelve las muestras ICFES del área (y parte) o '' si no hay archivo.

    Para las áreas de competencias y Comunicación Escrita devuelve el archivo
    completo. Para Inglés devuelve solo las secciones `## ` de la parte vigente
    (mapeada por tarea con `_SECCIONES_INGLES_POR_PARTE`) y '' si la parte no
    tiene muestras definidas.
    """
    archivo = _NOMBRE_ARCHIVO_MUESTRAS.get(area_nombre)
    if not archivo:
        return ''
    ruta = MUESTRAS_DIR / archivo
    if not ruta.exists():
        return ''
    texto = ruta.read_text(encoding='utf-8')

    if area_nombre != 'Inglés' or parte is None:
        return texto

    prefijos = {f'## {clave} ' for clave in _SECCIONES_INGLES_POR_PARTE.get(parte, ())}
    secciones = [
        seccion
        for seccion in re.split(r'\n(?=## )', texto)
        if any(seccion.startswith(prefijo) for prefijo in prefijos)
    ]
    return '\n\n'.join(secciones).strip()


def _bloque_muestras_icfes(muestras: str) -> str:
    """Bloque de contexto con los ejemplos auténticos, o '' si no hay muestras."""
    if not muestras.strip():
        return ''
    return _BLOQUE_MUESTRAS_ICFES.format(muestras=muestras.strip())


# Alias de la clave contenedora del JSON que devuelve el modelo. El prompt pide
# `preguntas`/`bloques`/`consignas`, pero un modelo puede renombrarla al inglés
# (visto con openai/gpt-oss-120b en Groq): se acepta cualquiera de las variantes
# para no descartar una respuesta cuyo contenido sí es válido.
_CLAVES_RAIZ = {
    'preguntas': ('preguntas', 'questions', 'items', 'exercises'),
    'bloques': ('bloques', 'blocks', 'preguntas', 'questions', 'items'),
    'consignas': ('consignas', 'prompts', 'tasks', 'writing_prompts', 'consignas_escritura'),
}


def _extraer_items(datos, clave):
    """Devuelve la lista de ítems del JSON aceptando nombres alternos de la clave."""
    if isinstance(datos, list):
        return datos
    if not isinstance(datos, dict):
        return None
    for nombre in _CLAVES_RAIZ.get(clave, (clave,)):
        valor = datos.get(nombre)
        if isinstance(valor, list):
            return valor
    return None


def _llamar_y_validar(client, modelo, kwarg_max_tokens, mensaje, clave, cantidad, validador, max_tokens, tipo):
    """Invoca al modelo con `response_format` JSON y valida con reintento.

    Centraliza el ciclo intento → parseo → validación de ambos flujos: si la
    respuesta viene truncada o mal formada se reintenta una vez y, en caso
    contrario, se lanza `ValueError` con el último error para que la vista lo
    traduzca en 502. El resultado se recorta a `cantidad` por si el modelo
    devuelve ítems de más.
    """
    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            # Techo amplio: los tokens de razonamiento del modelo consumen el
            # presupuesto y un tope corto devuelve contenido vacío (ver agente_ia).
            **{kwarg_max_tokens: max_tokens},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            items = _extraer_items(datos, clave)
            if not isinstance(items, list) or not items:
                raise ValueError(f'la clave "{clave}" falta o no es una lista con elementos')
            validados = [validador(item) for item in items]
            if not validados:
                raise ValueError('todos los elementos vinieron vacíos')
            return validados[:cantidad]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(
        f'La IA no produjo {tipo} válidas tras {MAX_INTENTOS} intentos: {ultimo_error}'
    )


# Alias de claves en inglés que algunos modelos devuelven pese a que el prompt
# pide las claves en español: openai/gpt-oss-120b (Groq) renombra `contexto` a
# `context` y `enunciado` a `statement`. Se normalizan ANTES de validar para no
# rechazar un contenido correcto solo por el nombre de una clave.
_ALIAS_CLAVES = {
    'context': 'contexto',
    'statement': 'enunciado',
    'question': 'enunciado',
    'prompt': 'enunciado',
    'options': 'opciones',
    'choices': 'opciones',
    'correct_answer': 'respuesta_correcta',
    'answer': 'respuesta_correcta',
    'topic': 'tema',
    'theme': 'tema',
    'description': 'descripcion',
    'relationships': 'relaciones',
    'matches': 'relaciones',
    'questions': 'preguntas',
}

# Alias propios del par descripción→palabra de la parte 1 de Inglés: ahí la
# palabra correcta se llama `respuesta`, no `respuesta_correcta`.
_ALIAS_RELACION = {
    'description': 'descripcion',
    'answer': 'respuesta',
    'word': 'respuesta',
    'match': 'respuesta',
}


def _normalizar_claves(datos, alias: dict = None):
    """Traduce a español las claves en inglés que devuelven algunos modelos.

    Recibe un dict y devuelve una copia con las claves renombradas según la
    tabla `alias` (o `_ALIAS_CLAVES` por defecto). Si no es dict lo devuelve tal
    cual, para que la validación informe del error de forma real.
    """
    if not isinstance(datos, dict):
        return datos
    tabla = alias or _ALIAS_CLAVES
    return {tabla.get(clave, clave): valor for clave, valor in datos.items()}


def _validar_pregunta(datos: dict, opciones_esperadas: int, contexto_requerido: bool) -> dict:
    """
    Valida una pregunta de selección múltiple generada por la IA.

    Protege al banco de respuestas rotas: claves faltantes, cantidad de
    opciones distinta a la del área/parte, opciones repetidas y una
    `respuesta_correcta` que no coincide exactamente con ninguna opción (la
    evaluación compara por igualdad, así que esa pregunta sería imposible).
    """
    if not isinstance(datos, dict):
        raise ValueError('cada pregunta debe ser un objeto JSON')

    datos = _normalizar_claves(datos)

    requeridas = ['enunciado', 'opciones', 'respuesta_correcta']
    faltantes = [c for c in requeridas if not str(datos.get(c) or '').strip()]
    if faltantes:
        raise ValueError(f'faltan claves o vienen vacías: {", ".join(faltantes)}')

    opciones = datos['opciones']
    if not isinstance(opciones, list) or len(opciones) != opciones_esperadas:
        raise ValueError(f'debe haber exactamente {opciones_esperadas} opciones')
    if not all(isinstance(o, str) and o.strip() for o in opciones):
        raise ValueError('todas las opciones deben ser textos no vacíos')
    if len(set(opciones)) != opciones_esperadas:
        raise ValueError('las opciones deben ser distintas entre sí')
    if datos['respuesta_correcta'] not in opciones:
        raise ValueError('respuesta_correcta no coincide con ninguna opción')

    contexto = str(datos.get('contexto') or '').strip()
    if contexto_requerido:
        if not contexto:
            raise ValueError('la clave "contexto" es obligatoria en Lectura Crítica')
        if len(contexto.split()) > 500:
            raise ValueError('el "contexto" de Lectura Crítica excede las 500 palabras')

    return {
        'enunciado': str(datos['enunciado']).strip(),
        'opciones': [o.strip() for o in opciones],
        'respuesta_correcta': str(datos['respuesta_correcta']).strip(),
        'contexto': contexto,
    }


def _validar_relacion(datos: dict) -> dict:
    """
    Valida un ejercicio de relacionar (parte 1 de Inglés) generado por la IA.

    Delega la forma en `catalogo_saber_pro.validar_relacion`: 8 palabras
    distintas, exactamente 5 descripciones y cada respuesta dentro de esa
    lista sin repetirse. `respuesta_correcta` se fija vacía porque este ítem
    no es de opción múltiple.
    """
    if not isinstance(datos, dict):
        raise ValueError('cada ejercicio debe ser un objeto JSON')

    datos = _normalizar_claves(datos)
    relaciones = [
        _normalizar_claves(relacion, _ALIAS_RELACION) if isinstance(relacion, dict) else relacion
        for relacion in (datos.get('relaciones') or [])
    ]

    enunciado = str(datos.get('enunciado') or '').strip()
    if not enunciado:
        raise ValueError('falta la clave "enunciado" o viene vacía')

    opciones, relaciones = validar_relacion(datos.get('opciones'), relaciones)
    return {
        'enunciado': enunciado,
        'opciones': opciones,
        'relaciones': relaciones,
        'respuesta_correcta': '',
        'contexto': str(datos.get('contexto') or '').strip(),
    }


def _validar_bloque_ingles(datos: dict, parte: int) -> dict:
    """
    Valida un bloque completo de una parte de Inglés (2 a 7) generado por la IA.

    Replica la validación de `_validar_pregunta` pregunta por pregunta y aplica
    las reglas del bloque: `enunciado` obligatorio, cantidad exacta de preguntas
    según `PREGUNTAS_POR_PARTE_INGLES` y, en las partes que comparten texto,
    un `contexto` presente (con los espacios `__N__` completos en las partes
    4 y 7). Se fijan vacíos `opciones`/`respuesta_correcta`/`relaciones` porque
    este ítem no es de opción múltiple a nivel del bloque.
    """
    if not isinstance(datos, dict):
        raise ValueError('cada bloque debe ser un objeto JSON')

    datos = _normalizar_claves(datos)

    enunciado = str(datos.get('enunciado') or '').strip()
    if not enunciado:
        raise ValueError('falta la clave "enunciado" del bloque o viene vacía')

    preguntas = datos.get('preguntas')
    esperadas = preguntas_de_parte(parte)
    if not isinstance(preguntas, list) or len(preguntas) != esperadas:
        raise ValueError(f'el bloque debe tener exactamente {esperadas} preguntas')

    opciones_esperadas = opciones_de_parte(parte)
    validadas = []
    for pregunta in preguntas:
        validada = _validar_pregunta(pregunta, opciones_esperadas, False)
        validadas.append({k: validada[k] for k in ('enunciado', 'opciones', 'respuesta_correcta')})

    contexto = str(datos.get('contexto') or '').strip()
    if parte_usa_texto_comun(parte):
        if not contexto:
            raise ValueError('el "contexto" es obligatorio: el bloque comparte un texto base')
        if parte_exige_espacios(parte):
            marcas = set(re.findall(r'__(\d+)__', contexto))
            faltantes = [numero for numero in range(1, esperadas + 1) if str(numero) not in marcas]
            if faltantes:
                raise ValueError(
                    'el "contexto" debe numerar los espacios __N__ del 1 al '
                    f'{esperadas}; faltan: {", ".join(map(str, faltantes))}'
                )

    return {
        'enunciado': enunciado,
        'contexto': contexto,
        'preguntas': validadas,
        'opciones': [],
        'respuesta_correcta': '',
        'relaciones': [],
    }


def _validar_consigna(datos: dict) -> dict:
    """Valida una consigna de Comunicación Escrita generada por la IA."""
    if not isinstance(datos, dict):
        raise ValueError('cada consigna debe ser un objeto JSON')

    datos = _normalizar_claves(datos)

    requeridas = ['tema', 'contexto', 'enunciado']
    faltantes = [c for c in requeridas if not str(datos.get(c) or '').strip()]
    if faltantes:
        raise ValueError(f'faltan claves o vienen vacías: {", ".join(faltantes)}')

    return {
        'tema': str(datos['tema']).strip()[:200],
        'contexto': str(datos['contexto']).strip(),
        'enunciado': str(datos['enunciado']).strip(),
    }
