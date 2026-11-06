"""
Agente IA `tareas`: borrador de una tarea práctica a partir del RA del plan
de aula (afirmación, evidencia, tarea sugerida y rúbrica DCE).

Devuelve título y descripción (escenario + instrucciones + entregable).
La rúbrica sale de la del RA cuando existe; si no, la IA la propone y se
valida igual que una escrita por el docente. El docente revisa y edita el
borrador antes de publicarlo.
"""

import json
import logging

from backend_lairn.ia_client import obtener_cliente_ia
from .agente_preguntas_banco import ErrorGeneracion
from .servicio_tareas import ErrorRubrica, extensiones_permitidas, rubrica_desde_resultado, validar_rubrica

logger = logging.getLogger(__name__)


def _mensaje(asignatura, resultado, con_rubrica: bool, formatos: list) -> str:
    pedir_rubrica = '' if con_rubrica else (
        ',\n"rubrica": [{"criterio": "...", "descripcion": "...", "peso": 40, '
        '"niveles": [{"nombre": "Bajo", "descripcion": "...", "valor": 1.0}, '
        '{"nombre": "Básico", "descripcion": "...", "valor": 3.0}, '
        '{"nombre": "Alto", "descripcion": "...", "valor": 5.0}]}]'
    )
    regla_rubrica = '' if con_rubrica else (
        '\n- Rúbrica de 2 a 5 criterios cuyos pesos sumen exactamente 100; niveles con valor de 0 a 5.'
    )
    return f"""Actúas como docente experto en Diseño Centrado en Evidencias.
Diseña UNA tarea práctica para entregar como archivo, de la asignatura "{asignatura.nombre}"
(programa "{asignatura.programa.nombre}"), que evidencie este resultado de aprendizaje:
- Afirmación: {resultado.descripcion}
- Evidencia observable: {resultado.evidencia_observable or 'no definida'}
- Tarea sugerida en el plan de aula: {resultado.tarea_sugerida or 'no definida'}

Reglas:
- "descripcion" incluye: un escenario real y concreto, los pasos o requisitos, y el
  entregable exacto (qué archivo y qué debe contener). Texto plano, máximo 300 palabras.
- El entregable debe ser UN solo archivo con alguna de estas extensiones: {', '.join(sorted(extensiones_permitidas(formatos)))}.
- Español neutro; no inventes datos ajenos a la asignatura.{regla_rubrica}

Devuelve SOLO JSON:
{{"titulo": "...", "descripcion": "..."{pedir_rubrica}}}"""


def generar_tarea(asignatura, resultado, formatos: list) -> dict:
    """Retorna {titulo, descripcion, rubrica, origen_rubrica}. Lanza ErrorGeneracion."""
    rubrica_ra = rubrica_desde_resultado(resultado)
    try:
        client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    except ValueError:
        raise ErrorGeneracion('El proveedor de IA no está configurado. Contacta a soporte.')
    mensaje = _mensaje(asignatura, resultado, bool(rubrica_ra), formatos)
    for _ in range(2):
        try:
            respuesta = client.chat.completions.create(
                model=modelo, response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}], **{kwarg_max_tokens: 3000},
            )
            datos = json.loads(respuesta.choices[0].message.content or '{}')
        except json.JSONDecodeError:
            continue
        except Exception:
            logger.exception('Fallo del proveedor de IA generando una tarea')
            raise ErrorGeneracion('El servicio de IA no respondió. Inténtalo de nuevo en unos minutos.')
        titulo = str(datos.get('titulo') or '').strip()
        descripcion = str(datos.get('descripcion') or '').strip()
        if not titulo or not descripcion:
            continue
        if rubrica_ra:
            rubrica, origen = rubrica_ra, 'resultado'
        else:
            try:
                rubrica, origen = validar_rubrica(datos.get('rubrica')), 'ia'
            except ErrorRubrica:
                continue
        return {'titulo': titulo[:200], 'descripcion': descripcion[:5000], 'rubrica': rubrica,
                'origen_rubrica': origen, 'modelo': modelo}
    raise ErrorGeneracion('La IA no devolvió una tarea válida. Inténtalo de nuevo.')
