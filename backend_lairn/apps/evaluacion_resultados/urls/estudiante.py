"""
Rutas del estudiante de `evaluacion_resultados` (tareas HU-08A y
presentación de la evaluación formal HU-07).

Montadas en `api/evaluacion/estudiante/`.
"""

from django.urls import path

from apps.evaluacion_resultados.views.administrador import VistaPanelEstudiante

from apps.evaluacion_resultados.views.estudiante import (
    VistaArchivoGuiaEstudiante,
    VistaArchivoMiEntrega,
    VistaDetalleMiTarea,
    VistaEntregarTarea,
    VistaMisTareas,
    VistaDetalleMiEvaluacion,
    VistaEnviarEvaluacion,
    VistaGuardarRespuesta,
    VistaIniciarEvaluacion,
    VistaMisEvaluaciones,
    VistaReportarIncidente,
)

urlpatterns = [
    # ADR-014: resumen de inicio del estudiante.
    path('panel/', VistaPanelEstudiante.as_view(), name='ev_est_panel'),
    path('tareas/', VistaMisTareas.as_view(), name='ev_est_tareas'),
    path('tareas/<int:pk>/', VistaDetalleMiTarea.as_view(), name='ev_est_tarea_detalle'),
    path('tareas/<int:pk>/archivos/<int:archivo_id>/', VistaArchivoGuiaEstudiante.as_view(), name='ev_est_tarea_guia'),
    path('tareas/<int:pk>/entregar/', VistaEntregarTarea.as_view(), name='ev_est_tarea_entregar'),
    path('entregas/<int:entrega_id>/archivo/', VistaArchivoMiEntrega.as_view(), name='ev_est_entrega_archivo'),
    path('evaluaciones/', VistaMisEvaluaciones.as_view(), name='ev_est_evaluaciones'),
    path('evaluaciones/<int:pk>/', VistaDetalleMiEvaluacion.as_view(), name='ev_est_evaluacion'),
    path('evaluaciones/<int:pk>/iniciar/', VistaIniciarEvaluacion.as_view(), name='ev_est_evaluacion_iniciar'),
    path('evaluaciones/<int:pk>/respuestas/', VistaGuardarRespuesta.as_view(), name='ev_est_evaluacion_respuesta'),
    path('evaluaciones/<int:pk>/enviar/', VistaEnviarEvaluacion.as_view(), name='ev_est_evaluacion_enviar'),
    # ADR-010: integridad académica (el servidor decide advertencia o suspensión).
    path('evaluaciones/<int:pk>/incidentes/', VistaReportarIncidente.as_view(), name='ev_est_evaluacion_incidente'),
]
