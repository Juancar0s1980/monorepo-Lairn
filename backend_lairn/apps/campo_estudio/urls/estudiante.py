"""
Rutas de la app `campo_estudio` accedidas por el rol Estudiante.

El proyecto raíz monta este paquete bajo `api/campo-estudio/`, por lo que
los paths de aquí NO repiten el prefijo `campo-estudio/`.
"""

from django.urls import path
from apps.campo_estudio.views import (
    VistaTemasEstudioEstudiante,
    VistaMensajesTemaEstudio,
)

urlpatterns = [
    # Temas de estudio aprobados de un curso donde el estudiante está inscrito.
    path('mis-cursos/<int:curso_id>/temas/', VistaTemasEstudioEstudiante.as_view(), name='temas_estudio_estudiante'),

    # Hilo de chat propio del estudiante sobre un tema: historial (GET) y preguntar (POST).
    path('temas/<int:tema_id>/mensajes/', VistaMensajesTemaEstudio.as_view(), name='mensajes_tema_estudio'),
]
