"""Vistas del docente en `evaluacion_resultados` (banco de preguntas, tareas y supervisión en sala)."""

from .vista_tareas import (
    VistaArchivoEntregaDocente,
    VistaArchivosGuia,
    VistaCalificarEntrega,
    VistaDetalleArchivoGuia,
    VistaDetalleTarea,
    VistaEntregasTarea,
    VistaGenerarTarea,
    VistaListaCrearTareas,
    VistaPublicarTarea,
)
from .vista_supervision import (
    VistaAsistenciaMasiva,
    VistaLlamadoLista,
    VistaMisSupervisiones,
    VistaRegistrarAsistencia,
    VistaResolverIntegridadSupervisor,
)
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
    'VistaArchivoEntregaDocente',
    'VistaArchivosGuia',
    'VistaCalificarEntrega',
    'VistaDetalleArchivoGuia',
    'VistaDetalleTarea',
    'VistaEntregasTarea',
    'VistaGenerarTarea',
    'VistaListaCrearTareas',
    'VistaPublicarTarea',
    'VistaAsistenciaMasiva',
    'VistaLlamadoLista',
    'VistaMisSupervisiones',
    'VistaRegistrarAsistencia',
    'VistaResolverIntegridadSupervisor',
]
