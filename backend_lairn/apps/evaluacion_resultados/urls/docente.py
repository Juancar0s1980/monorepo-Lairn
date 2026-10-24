"""
Rutas del docente de `evaluacion_resultados` (banco de preguntas, HU-04/05).

Montadas en `api/evaluacion/docente/`.
"""

from django.urls import path

from apps.evaluacion_resultados.views.docente import (
    VistaAprobarPregunta,
    VistaDescartarPregunta,
    VistaDetallePregunta,
    VistaGenerarPreguntas,
    VistaListaPreguntas,
    VistaMisAsignaturas,
)

urlpatterns = [
    path('asignaturas/', VistaMisAsignaturas.as_view(), name='ev_docente_asignaturas'),
    path('banco/', VistaListaPreguntas.as_view(), name='ev_banco'),
    path('banco/generar/', VistaGenerarPreguntas.as_view(), name='ev_banco_generar'),
    path('banco/<int:pk>/', VistaDetallePregunta.as_view(), name='ev_banco_detalle'),
    path('banco/<int:pk>/aprobar/', VistaAprobarPregunta.as_view(), name='ev_banco_aprobar'),
    path('banco/<int:pk>/descartar/', VistaDescartarPregunta.as_view(), name='ev_banco_descartar'),
]
