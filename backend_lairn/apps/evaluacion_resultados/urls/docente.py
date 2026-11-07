"""
Rutas del docente de `evaluacion_resultados` (banco de preguntas HU-04/05 y
tareas prácticas HU-08B, supervisión en sala ADR-009).

Montadas en `api/evaluacion/docente/`.
"""

from django.urls import path

from apps.evaluacion_resultados.views.administrador import VistaEstudiantesDocente, VistaPanelDocente
from apps.evaluacion_resultados.views.docente import (
    VistaAprobarPregunta,
    VistaAsistenciaMasiva,
    VistaLlamadoLista,
    VistaMisSupervisiones,
    VistaRegistrarAsistencia,
    VistaResolverIntegridadSupervisor,
    VistaDescartarPregunta,
    VistaDetallePregunta,
    VistaGenerarPreguntas,
    VistaListaPreguntas,
    VistaMisAsignaturas,
    VistaArchivoEntregaDocente,
    VistaArchivosGuia,
    VistaCalificarEntrega,
    VistaPreevaluarEntrega,
    VistaDetalleArchivoGuia,
    VistaDetalleTarea,
    VistaEntregasTarea,
    VistaGenerarTarea,
    VistaListaCrearTareas,
    VistaPublicarTarea,
)

urlpatterns = [
    path('asignaturas/', VistaMisAsignaturas.as_view(), name='ev_docente_asignaturas'),
    path('banco/', VistaListaPreguntas.as_view(), name='ev_banco'),
    path('banco/generar/', VistaGenerarPreguntas.as_view(), name='ev_banco_generar'),
    path('banco/<int:pk>/', VistaDetallePregunta.as_view(), name='ev_banco_detalle'),
    path('banco/<int:pk>/aprobar/', VistaAprobarPregunta.as_view(), name='ev_banco_aprobar'),
    path('banco/<int:pk>/descartar/', VistaDescartarPregunta.as_view(), name='ev_banco_descartar'),
    path('tareas/', VistaListaCrearTareas.as_view(), name='ev_tareas'),
    path('tareas/generar/', VistaGenerarTarea.as_view(), name='ev_tareas_generar'),
    path('tareas/<int:pk>/', VistaDetalleTarea.as_view(), name='ev_tarea_detalle'),
    path('tareas/<int:pk>/archivos/', VistaArchivosGuia.as_view(), name='ev_tarea_archivos'),
    path('tareas/<int:pk>/archivos/<int:archivo_id>/', VistaDetalleArchivoGuia.as_view(), name='ev_tarea_archivo'),
    path('tareas/<int:pk>/publicar/', VistaPublicarTarea.as_view(), name='ev_tarea_publicar'),
    path('tareas/<int:pk>/entregas/', VistaEntregasTarea.as_view(), name='ev_tarea_entregas'),
    path('entregas/<int:entrega_id>/archivo/', VistaArchivoEntregaDocente.as_view(), name='ev_entrega_archivo'),
    # ADR-009: llamado a lista del docente supervisor.
    # ADR-012: estudiantes de sus cursos y de las evaluaciones que supervisa.
    path('panel/', VistaPanelDocente.as_view(), name='ev_docente_panel'),
    path('estudiantes/', VistaEstudiantesDocente.as_view(), name='ev_docente_estudiantes'),
    path('supervision/', VistaMisSupervisiones.as_view(), name='ev_supervision'),
    path('supervision/<int:pk>/', VistaLlamadoLista.as_view(), name='ev_supervision_detalle'),
    path('supervision/<int:pk>/asistencia/', VistaRegistrarAsistencia.as_view(), name='ev_supervision_asistencia'),
    path('supervision/<int:pk>/intentos/<int:estudiante_id>/resolver/', VistaResolverIntegridadSupervisor.as_view(),
         name='ev_supervision_resolver'),
    path('supervision/<int:pk>/asistencia/masiva/', VistaAsistenciaMasiva.as_view(), name='ev_supervision_masiva'),
    path('entregas/<int:entrega_id>/calificar/', VistaCalificarEntrega.as_view(), name='ev_entrega_calificar'),
    path('entregas/<int:entrega_id>/preevaluar/', VistaPreevaluarEntrega.as_view(), name='ev_entrega_preevaluar'),
]
