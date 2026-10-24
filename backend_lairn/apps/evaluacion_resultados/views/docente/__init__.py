"""Vistas del docente en `evaluacion_resultados` (banco de preguntas)."""

from .vista_banco_preguntas import (
    VistaAprobarPregunta,
    VistaDescartarPregunta,
    VistaDetallePregunta,
    VistaGenerarPreguntas,
    VistaListaPreguntas,
    VistaMisAsignaturas,
)

__all__ = [
    'VistaAprobarPregunta',
    'VistaDescartarPregunta',
    'VistaDetallePregunta',
    'VistaGenerarPreguntas',
    'VistaListaPreguntas',
    'VistaMisAsignaturas',
]
