"""
Rutas de la app `examenes` accedidas por el rol Docente.

Registra los endpoints de gestión de cursos, exámenes y estudiantes inscritos.
Cada `path` apunta a una vista que ya impone `permission_classes = [EsDocente]`,
de modo que este archivo solo se ocupa de definir el mapeo URL→vista y no
duplica controles de autorización.

La estructura colección/detalle sigue la convención REST: `cursos/` para
operaciones de colección y `cursos/<id>/` para operaciones sobre un curso
específico, en una sola entrada que despacha por verbo HTTP.
"""

from django.urls import path
from apps.examenes.views import (
    VistaCrearCurso,
    VistaDetalleCurso,
    VistaCrearExamen,
    VistaDetalleExamen,
    VistaEstudiantesCurso,
)

urlpatterns = [
    # Colección de cursos del docente: creación (POST) y listado (GET).
    path('cursos/', VistaCrearCurso.as_view(), name='cursos'),

    # Detalle de un curso del docente: retrieve (GET), update (PUT/PATCH) y delete (DELETE).
    path('cursos/<int:curso_id>/', VistaDetalleCurso.as_view(), name='detalle_curso'),

    # Creación de exámenes asociados a un curso del docente.
    path('examenes/', VistaCrearExamen.as_view(), name='examenes'),

    # Detalle de un examen del docente: retrieve (GET), update (PUT/PATCH) y delete (DELETE).
    # Update/delete se bloquean si hay sesiones de estudiantes en progreso sobre el examen.
    path('examenes/<int:examen_id>/', VistaDetalleExamen.as_view(), name='detalle_examen'),

    # Listado de estudiantes inscritos en un curso del docente.
    path('cursos/<int:curso_id>/estudiantes/', VistaEstudiantesCurso.as_view(), name='estudiantes_curso'),

    # Eliminación de la inscripción de un estudiante específico en un curso del docente.
    path('cursos/<int:curso_id>/estudiantes/<int:estudiante_id>/', VistaEstudiantesCurso.as_view(), name='eliminar_estudiante'),
]
