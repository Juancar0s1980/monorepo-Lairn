"""
Rutas de la app `examenes` accedidas por el rol Estudiante.

Registra los endpoints de auto-inscripción y de consulta sobre cursos y
exámenes en los que el estudiante está inscrito. Las vistas asociadas ya
imponen `permission_classes = [EsEstudiante]`, por lo que este archivo
únicamente declara el mapeo URL→vista.

El prefijo `mis-cursos/` se usa para los listados centrados en el estudiante
(sus inscripciones y los exámenes derivados), diferenciándolos de las rutas
de gestión global del docente bajo `cursos/`.
"""

from django.urls import path
from apps.examenes.views import (
    VistaInscribirse,
    VistaMisCursos,
    VistaExamenesCurso,
)

urlpatterns = [
    # Inscripción de un estudiante a un curso mediante el código compartido por el docente.
    path('inscribirse/', VistaInscribirse.as_view(), name='inscribirse'),

    # Listado de cursos en los que el estudiante autenticado está inscrito.
    path('mis-cursos/', VistaMisCursos.as_view(), name='mis_cursos'),

    # Listado de exámenes disponibles para el estudiante en un curso donde está inscrito.
    path('mis-cursos/<int:curso_id>/examenes/', VistaExamenesCurso.as_view(), name='examenes_curso'),
]
