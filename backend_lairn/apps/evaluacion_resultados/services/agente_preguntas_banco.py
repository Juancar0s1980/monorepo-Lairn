"""
Agente IA `preguntas_banco`: borradores de preguntas DCE para el banco
oficial (HU-04.2 / 04.4).

Entrada: asignatura + RA (afirmación, evidencia, tarea, rúbrica que vienen
del plan de aula) + competencia transversal opcional.
Salida validada: lista de {contexto, enunciado, opciones[4],
respuesta_correcta, retroalimentacion}. Todo lo que no cumpla el contrato
se descarta aquí: el docente nunca recibe una pregunta mal formada.
"""

import json
import logging

from backend_lairn.ia_client import obtener_cliente_ia

MAX_PREGUNTAS = 5
NUM_OPCIONES = 4
logger = logging.getLogger(__name__)


class ErrorGeneracion(Exception):
    """Mensaje apto para el docente (sin detalles del proveedor)."""


def _construir_mensaje(asignatura, resultado, competencia, cantidad: int) -> str:
    rubrica = '; '.join(
        f"{c.get('criterio', '')} ({c.get('peso', '')}%)"
        for c in (resultado.criterios_rubrica or []) if isinstance(c, dict)
    ) or 'no definida'
    transversal = (
        f'- Competencia transversal a entrenar: "{competencia.nombre}". {competencia.descripcion}\n'
        if competencia else ''
    )
    return f"""Actúas como experto en evaluación con Diseño Centrado en Evidencias (Icfes 2018).
Genera {cantidad} preguntas de selección múltiple con única respuesta para la asignatura
"{asignatura.nombre}" del programa "{asignatura.programa.nombre}".

Plan de aula (resultado de aprendizaje a evaluar):
- Afirmación: {resultado.descripcion}
- Evidencia observable: {resultado.evidencia_observable or 'no definida'}
- Tarea sugerida: {resultado.tarea_sugerida or 'no definida'}
- Competencia del RA: {resultado.competencia.nombre}
- Criterios de rúbrica: {rubrica}
{transversal}
Reglas:
- Cada pregunta parte de un caso o situación real y concreta del ámbito de la asignatura
  (campo "contexto", 2 a 5 oraciones) que exige analizar e interpretar antes de responder.
- El enunciado pregunta por la evidencia observable del RA{' y entrena la competencia transversal' if competencia else ''}.
- Exactamente {NUM_OPCIONES} opciones plausibles, una sola correcta; sin "todas/ninguna de las anteriores".
- "retroalimentacion" explica por qué la correcta lo es y por qué las demás no.
- Español neutro. No inventes datos ajenos a la asignatura.

Devuelve SOLO JSON:
{{"preguntas": [{{"contexto": "...", "enunciado": "...", "opciones": ["...", "...", "...", "..."],
"respuesta_correcta": 0, "retroalimentacion": "..."}}]}}"""


def _validar(item) -> dict | None:
    if not isinstance(item, dict):
        return None
    contexto = str(item.get('contexto') or '').strip()
    enunciado = str(item.get('enunciado') or '').strip()
    retro = str(item.get('retroalimentacion') or '').strip()
    opciones = item.get('opciones')
    correcta = item.get('respuesta_correcta')
    if not enunciado or not isinstance(opciones, list) or len(opciones) != NUM_OPCIONES:
        return None
    opciones = [str(o).strip() for o in opciones]
    if any(not o for o in opciones) or len(set(o.lower() for o in opciones)) != NUM_OPCIONES:
        return None
    if isinstance(correcta, bool) or not isinstance(correcta, int) or not 0 <= correcta < NUM_OPCIONES:
        return None
    return {
        'contexto': contexto[:3000], 'enunciado': enunciado[:2000],
        'opciones': [o[:500] for o in opciones], 'respuesta_correcta': correcta,
        'retroalimentacion': retro[:3000],
    }


def generar_preguntas(asignatura, resultado, competencia, cantidad: int) -> tuple[list, dict]:
    """Retorna (preguntas_validas, metadatos). Lanza ErrorGeneracion si no hay ninguna."""
    cantidad = max(1, min(int(cantidad), MAX_PREGUNTAS))
    try:
        client, modelo, kwarg_max_tokens = obtener_cliente_ia()
    except ValueError:
        raise ErrorGeneracion('El proveedor de IA no está configurado. Contacta a soporte.')
    mensaje = _construir_mensaje(asignatura, resultado, competencia, cantidad)
    for _ in range(2):
        try:
            respuesta = client.chat.completions.create(
                model=modelo,
                response_format={'type': 'json_object'},
                messages=[{'role': 'user', 'content': mensaje}],
                **{kwarg_max_tokens: 4000},
            )
            datos = json.loads(respuesta.choices[0].message.content or '{}')
        except json.JSONDecodeError:
            continue
        except Exception:
            # Red, cuota, credenciales: el detalle va al log, no al docente.
            logger.exception('Fallo del proveedor de IA generando preguntas del banco')
            raise ErrorGeneracion('El servicio de IA no respondió. Inténtalo de nuevo en unos minutos.')
        validas = [p for p in map(_validar, datos.get('preguntas') or []) if p][:cantidad]
        if validas:
            return validas, {'modelo': modelo, 'solicitadas': cantidad, 'validas': len(validas)}
    raise ErrorGeneracion('La IA no devolvió preguntas válidas. Inténtalo de nuevo.')
