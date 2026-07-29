"""
Rutas de la app `campo_estudio` accedidas por el rol Docente.

El proyecto raíz monta este paquete bajo `api/campo-estudio/`, por lo que
los paths de aquí NO repiten el prefijo `campo-estudio/`.
"""

from django.urls import path
from apps.campo_estudio.views import (
    VistaActivarCampoEstudio,
    VistaTemasEstudioDocente,
    VistaGenerarTemasEstudio,
    VistaDetalleTemaEstudio,
    VistaAprobarTemaEstudio,
)

urlpatterns = [
    # Activar/desactivar el Campo de Estudio del curso.
    path('cursos/<int:curso_id>/activar/', VistaActivarCampoEstudio.as_view(), name='activar_campo_estudio'),

    # Cola de temas de estudio del curso: listado completo (GET, pendientes + aprobados).
    path('cursos/<int:curso_id>/temas/', VistaTemasEstudioDocente.as_view(), name='temas_estudio_docente'),

    # Generar temas de estudio con IA (SÍ guarda, a diferencia de "sugerir" de objetivos/laboratorios).
    path('cursos/<int:curso_id>/temas/generar/', VistaGenerarTemasEstudio.as_view(), name='generar_temas_estudio'),

    # Detalle de un tema: edición (PATCH) y eliminación (DELETE).
    path('temas/<int:tema_id>/', VistaDetalleTemaEstudio.as_view(), name='detalle_tema_estudio'),

    # Aprobar un tema pendiente: lo hace visible para los estudiantes.
    path('temas/<int:tema_id>/aprobar/', VistaAprobarTemaEstudio.as_view(), name='aprobar_tema_estudio'),
]
