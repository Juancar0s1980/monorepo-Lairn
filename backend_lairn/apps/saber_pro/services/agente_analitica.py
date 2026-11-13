"""
Análisis de acciones recomendadas con IA sobre la analítica Saber Pro (HU-24).

`generar_analisis_acciones_curso` recibe el payload que ya calculó
`construir_analitica_curso` (con los filtros aplicados por el docente) y le
pide a la IA un diagnóstico breve del grupo y una lista de acciones concretas
(título, descripción y prioridad) para reforzar los criterios más débiles.
`generar_analisis_acciones_institucional` hace lo propio con el payload de
`construir_analitica_institucional` para coordinación y vicerrectoría.

- No se envían datos personales a la IA: del payload solo viajan el resumen,
  la distribución, los desgloses y los focos de refuerzo (agregados). Los
  resultados individuales (nombres y correos) se excluyen siempre.
- La respuesta se valida siempre (estructura, tipos y prioridades) y se
  reintenta una vez; si vuelve mal formada se lanza `ValueError` con mensaje
  claro y la vista responde 502. Mismo patrón que `agente_saber_pro.py`.
"""

import json

from backend_lairn.ia_client import obtener_cliente_ia

MAX_INTENTOS = 2
MAX_ACCIONES = 8

# Alias de claves en inglés que algunos modelos devuelven pese a que el prompt
# pide las claves en español (mismo problema documentado en `agente_saber_pro`).
_ALIAS_CLAVES = {
    'title': 'titulo',
    'name': 'titulo',
    'summary': 'resumen',
    'description': 'descripcion',
    'actions': 'acciones',
    'priority': 'prioridad',
}

# Prioridades aceptadas, con equivalentes en inglés por si el modelo las usa.
_ALIAS_PRIORIDAD = {
    'alta': 'alta',
    'high': 'alta',
    'media': 'media',
    'medium': 'media',
    'baja': 'baja',
    'low': 'baja',
}


def _compactar(filas, campos):
    """Deja de cada fila solo los campos indicados; las referencias quedan en su nombre."""
    compactadas = []
    for fila in filas or []:
        item = {}
        for campo in campos:
            valor = fila.get(campo)
            if isinstance(valor, dict):
                valor = valor.get('nombre')
            item[campo] = valor
        compactadas.append(item)
    return compactadas


def _contexto_para_ia(payload):
    """Resume el payload de analítica en un contexto acotado y sin datos personales.

    Se omite `resultados_individuales` (nombres y correos): la IA solo necesita
    agregados, desgloses y focos para proponer acciones de refuerzo. Los filtros
    viajan completos para que el análisis refleje el alcance que ve el docente.
    """
    
    return {
        'curso': payload['curso']['nombre'],
        'area': payload['curso']['area']['nombre'],
        'filtros': payload['filtro'],
        'resumen': payload['resumen'],
        'distribucion_calificaciones': payload['distribucion_calificaciones'],
        'por_area': _compactar(
            payload['por_area'],
            ('area', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_competencia': _compactar(
            payload['por_competencia'],
            ('competencia', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_afirmacion': _compactar(
            payload['por_afirmacion'],
            ('afirmacion', 'competencia', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_parte': _compactar(
            payload['por_parte'],
            ('parte', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'focos_bajos': payload['focos_bajos'],
    }


def _contexto_para_ia_institucional(payload):
    """Resume la analítica institucional en un contexto agregado y sin datos personales.

    La analítica institucional no expone resultados individuales; además de los
    desgloses y focos se envían las comparativas por curso, carrera y periodo
    para que el plan de acción tenga alcance institucional.
    """
    return {
        'alcance': payload['filtro'],
        'resumen': payload['resumen'],
        'distribucion_calificaciones': payload['distribucion_calificaciones'],
        'por_area': _compactar(
            payload['por_area'],
            ('area', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_competencia': _compactar(
            payload['por_competencia'],
            ('competencia', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_afirmacion': _compactar(
            payload['por_afirmacion'],
            ('afirmacion', 'competencia', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_parte': _compactar(
            payload['por_parte'],
            ('parte', 'total_estudiantes', 'aciertos', 'total_preguntas', 'porcentaje_acierto'),
        ),
        'por_curso': _compactar(
            payload['por_curso'],
            (
                'curso',
                'total_estudiantes',
                'total_intentos',
                'promedio_puntaje',
                'promedio_calificacion',
                'porcentaje_acierto',
                'tasa_aprobacion',
            ),
        ),
        'por_programa': _compactar(
            payload['por_programa'],
            (
                'programa',
                'total_estudiantes',
                'total_intentos',
                'promedio_puntaje',
                'promedio_calificacion',
                'porcentaje_acierto',
                'tasa_aprobacion',
            ),
        ),
        'por_periodo': _compactar(
            payload['por_periodo'],
            (
                'periodo',
                'total_estudiantes',
                'total_intentos',
                'promedio_puntaje',
                'promedio_calificacion',
                'porcentaje_acierto',
                'tasa_aprobacion',
            ),
        ),
        'focos_bajos': payload['focos_bajos'],
    }


def _normalizar_claves(datos):
    """Traduce a español las claves en inglés que devuelven algunos modelos."""
    if not isinstance(datos, dict):
        return datos
    return {_ALIAS_CLAVES.get(clave, clave): valor for clave, valor in datos.items()}


def _validar_accion(accion):
    """Valida una acción recomendada generada por la IA."""
    if not isinstance(accion, dict):
        raise ValueError('cada acción debe ser un objeto JSON')

    accion = _normalizar_claves(accion)
    titulo = str(accion.get('titulo') or '').strip()
    descripcion = str(accion.get('descripcion') or '').strip()
    if not titulo or not descripcion:
        raise ValueError('cada acción necesita "titulo" y "descripcion" no vacíos')

    prioridad = _ALIAS_PRIORIDAD.get(str(accion.get('prioridad') or '').strip().lower())
    if prioridad is None:
        raise ValueError('la prioridad debe ser "alta", "media" o "baja"')

    return {
        'titulo': titulo[:150],
        'descripcion': descripcion[:800],
        'prioridad': prioridad,
    }


def _validar_analisis(datos):
    """Valida la respuesta completa del análisis (resumen + acciones)."""
    if not isinstance(datos, dict):
        raise ValueError('la respuesta debe ser un objeto JSON')

    datos = _normalizar_claves(datos)
    resumen = str(datos.get('resumen') or '').strip()
    if not resumen:
        raise ValueError('falta la clave "resumen" o viene vacía')

    acciones = datos.get('acciones')
    if not isinstance(acciones, list) or not acciones:
        raise ValueError('la clave "acciones" falta o no es una lista con elementos')

    validadas = [_validar_accion(accion) for accion in acciones]
    return {
        'resumen': resumen,
        'acciones': validadas[:MAX_ACCIONES],
    }


def _generar_analisis(mensaje):
    """Invoca a la IA, valida el JSON y reintenta una vez si llega mal formado."""
    client, modelo, kwarg_max_tokens = obtener_cliente_ia()

    ultimo_error = None
    for _ in range(MAX_INTENTOS):
        respuesta = client.chat.completions.create(
            model=modelo,
            response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': mensaje}],
            **{kwarg_max_tokens: 2500},
        )
        try:
            datos = json.loads(respuesta.choices[0].message.content)
            return _validar_analisis(datos)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            ultimo_error = e

    raise ValueError(
        f'La IA no produjo un análisis válido tras {MAX_INTENTOS} intentos: {ultimo_error}'
    )


def generar_analisis_acciones_curso(payload: dict) -> dict:
    """
    Genera con IA el análisis de acciones a partir de la analítica de un curso.

    Devuelve `{"resumen": str, "acciones": [{"titulo", "descripcion",
    "prioridad"}]}` con las acciones ordenadas como las entregó el modelo
    (se piden de mayor a menor prioridad). Requiere el payload de
    `construir_analitica_curso`; si el curso no tiene intentos elegibles la
    vista debe responder 400 antes de llamar aquí.
    """
    contexto = json.dumps(_contexto_para_ia(payload), ensure_ascii=False, indent=2)

    mensaje = f"""Eres asistente pedagógico de un docente que prepara estudiantes para el examen Saber Pro de Colombia.
Recibes los indicadores agregados de su curso (sin datos personales) y debes proponer un plan de acción de refuerzo.

DATOS DEL CURSO (JSON):
{contexto}

Reglas:
1. "resumen": diagnóstico breve del grupo (3 a 5 oraciones), en español, basado ÚNICAMENTE en los datos entregados; no inventes resultados.
2. "acciones": entre 3 y 6 acciones concretas y accionables para el docente, ordenadas de mayor a menor prioridad. Cada acción:
   - "titulo": máximo 12 palabras, sin puntuación final.
   - "descripcion": qué hacer, sobre qué criterio y con qué propósito, en 1 a 3 oraciones.
   - "prioridad": exactamente "alta", "media" o "baja".
3. Apóyate en los focos de refuerzo y desgloses entregados; no menciones estudiantes por nombre ni datos que no estén en el JSON.
4. Sugiere usos concretos del módulo cuando aplique: simulacros focalizados por competencia, afirmación o parte de Inglés, banco de contenido con IA, revisión de consignas abiertas de Comunicación Escrita, etc.

Tu única salida debe ser un objeto JSON válido, sin texto adicional, usando EXACTAMENTE estos nombres de clave en español:
{{"resumen": "...", "acciones": [{{"titulo": "...", "descripcion": "...", "prioridad": "alta"}}, ...]}}"""

    return _generar_analisis(mensaje)


def generar_analisis_acciones_institucional(payload: dict) -> dict:
    """
    Genera con IA el análisis de acciones a partir de la analítica institucional.

    Se usa para coordinadores y vicerrectores (HU-24.7): recibe el payload de
    `construir_analitica_institucional` (solo agregados, sin datos personales) y
    devuelve un plan de acción de alcance institucional. Si no hay intentos
    elegibles la vista debe responder 400 antes de llamar aquí.
    """
    contexto = json.dumps(
        _contexto_para_ia_institucional(payload), ensure_ascii=False, indent=2
    )

    mensaje = f"""Eres asistente de coordinación académica de una institución que prepara estudiantes para el examen Saber Pro de Colombia.
Recibes los indicadores agregados de la institución (sin datos personales) y debes proponer un plan de acción institucional.

DATOS INSTITUCIONALES (JSON):
{contexto}

Reglas:
1. "resumen": diagnóstico breve del desempeño institucional (3 a 5 oraciones), en español, basado ÚNICAMENTE en los datos entregados; no inventes resultados.
2. "acciones": entre 3 y 6 acciones concretas y accionables para coordinación y vicerrectoría, ordenadas de mayor a menor prioridad. Cada acción:
   - "titulo": máximo 12 palabras, sin puntuación final.
   - "descripcion": qué hacer, sobre qué área, criterio, curso o carrera y con qué propósito, en 1 a 3 oraciones.
   - "prioridad": exactamente "alta", "media" o "baja".
3. Apóyate en los focos de refuerzo, desgloses y comparativas por curso, carrera y periodo; no menciones estudiantes por nombre ni datos que no estén en el JSON.
4. Sugiere usos concretos del módulo cuando aplique: refuerzo focalizado por competencia, afirmación o parte de Inglés, acompañamiento a los cursos con menor desempeño y seguimiento por periodo.

Tu única salida debe ser un objeto JSON válido, sin texto adicional, usando EXACTAMENTE estos nombres de clave en español:
{{"resumen": "...", "acciones": [{{"titulo": "...", "descripcion": "...", "prioridad": "alta"}}, ...]}}"""

    return _generar_analisis(mensaje)
