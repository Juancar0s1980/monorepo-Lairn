"""
Reglas de ensamblado de la evaluación formal (HU-06.1 / 06.2).

- `preguntas_elegibles`: preguntas APROBADAS del banco cuyos RA están
  vinculados al momento, excluyendo las que ya se usaron de forma idéntica
  en el laboratorio de práctica (mismo enunciado, sin distinguir mayúsculas
  ni espacios). Así el estudiante no llega a la evaluación con la pregunta
  ya practicada (HU-06.2 / HU-14.2).
- `cobertura`: por cada RA del momento, cuántas preguntas se seleccionaron,
  para advertir RA obligatorios sin evaluar.
"""

import re

from apps.evaluacion_resultados.models import (
    OpcionesEstadoPregunta,
    OpcionesEstadoTarea,
    PreguntaBanco,
    TareaPractica,
)
from apps.laboratorios.models import Pregunta as PreguntaLaboratorio


def normalizar(texto: str) -> str:
    return re.sub(r'\s+', ' ', (texto or '').strip().lower())


def vinculos_activos(momento):
    return momento.vinculos.filter(resultado__activo=True).select_related('resultado__competencia')


def preguntas_elegibles(momento) -> tuple[list, int]:
    """Retorna (preguntas elegibles, cuántas se excluyeron por estar en laboratorio)."""
    ids_ra = [v.resultado_id for v in vinculos_activos(momento)]
    candidatas = list(
        PreguntaBanco.objects.filter(
            resultado_id__in=ids_ra, estado=OpcionesEstadoPregunta.APROBADA,
        ).select_related('asignatura', 'resultado__competencia', 'competencia_transversal')
    )
    if not candidatas:
        return [], 0
    usadas_en_laboratorio = {
        normalizar(e) for e in PreguntaLaboratorio.objects.values_list('enunciado', flat=True)
    }
    elegibles = [p for p in candidatas if normalizar(p.enunciado) not in usadas_en_laboratorio]
    return elegibles, len(candidatas) - len(elegibles)


def tareas_elegibles(momento):
    """Tareas publicadas cuyo RA está vinculado al momento (HU-06.4)."""
    ids_ra = [v.resultado_id for v in vinculos_activos(momento)]
    return TareaPractica.objects.filter(
        resultado_id__in=ids_ra, estado=OpcionesEstadoTarea.PUBLICADA,
    ).select_related('asignatura', 'resultado')


def cobertura(evaluacion) -> list:
    seleccion = {}
    for resultado_id in evaluacion.items.values_list('pregunta__resultado_id', flat=True):
        seleccion[resultado_id] = seleccion.get(resultado_id, 0) + 1
    # En una evaluación por tarea, el RA de la tarea queda cubierto.
    if evaluacion.tarea_id:
        seleccion[evaluacion.tarea.resultado_id] = seleccion.get(evaluacion.tarea.resultado_id, 0) + 1
    return [
        {
            'resultado_id': v.resultado_id,
            'descripcion': v.resultado.descripcion,
            'obligatorio': v.obligatorio,
            'preguntas': seleccion.get(v.resultado_id, 0),
        }
        for v in vinculos_activos(evaluacion.momento)
    ]
