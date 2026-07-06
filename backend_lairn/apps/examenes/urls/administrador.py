"""
Rutas de la app `examenes` accedidas por el rol Administrador.

Registra el endpoint de solo lectura que permite auditar todos los exámenes
del sistema, sin restringirse al docente propietario como hacen las rutas
bajo `apps.examenes.urls.docente`.
"""

from django.urls import path
from apps.examenes.views import VistaAdminExamenes

urlpatterns = [
    # Listado global de exámenes de todos los cursos y docentes, con filtro opcional por curso.
    path('administracion/examenes/', VistaAdminExamenes.as_view(), name='admin_examenes'),
]
