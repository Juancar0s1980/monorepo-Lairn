"""Vistas del estudiante en `evaluacion_resultados` (tareas HU-08A y evaluación formal HU-07)."""

from .vista_evaluaciones_estudiante import (
    VistaDetalleMiEvaluacion,
    VistaEnviarEvaluacion,
    VistaGuardarRespuesta,
    VistaIniciarEvaluacion,
    VistaMisEvaluaciones,
    VistaReportarIncidente,
)
from .vista_tareas_estudiante import (
    VistaArchivoGuiaEstudiante,
    VistaArchivoMiEntrega,
    VistaDetalleMiTarea,
    VistaEntregarTarea,
    VistaMisTareas,
)

__all__ = [
    'VistaArchivoGuiaEstudiante',
    'VistaArchivoMiEntrega',
    'VistaDetalleMiTarea',
    'VistaEntregarTarea',
    'VistaMisTareas',
    'VistaDetalleMiEvaluacion',
    'VistaEnviarEvaluacion',
    'VistaGuardarRespuesta',
    'VistaIniciarEvaluacion',
    'VistaMisEvaluaciones',
    'VistaReportarIncidente',
]
