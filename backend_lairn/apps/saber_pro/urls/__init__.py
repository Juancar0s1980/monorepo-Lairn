"""
Paquete de URLs de la app `saber_pro`. Montado por el proyecto raíz bajo
`api/saber-pro/`.

Actúa como punto de entrada único y delega la definición concreta de rutas a
submódulos divididos por rol del consumidor (Docente / Estudiante), replicando
el patrón de `examenes` y `laboratorios`. Cada submódulo solo mapea URL→vista;
la autorización la impone cada vista con su `permission_classes`.

Con la HU-17 se agregan los endpoints del docente (cursos, detalle, regeneración
de código y estudiantes inscritos) en `urls/docente.py`.
"""

from django.urls import include, path

from apps.saber_pro.views import VistaPanelSaberPro, VistaListaAreasSaberPro

urlpatterns = [
    # Panel principal del módulo (HU-16): funcionalidades disponibles según el rol.
    path('panel/', VistaPanelSaberPro.as_view(), name='panel_saber_pro'),

    # Catálogo de áreas oficiales del examen; lo consume el formulario de creación de curso (HU-17.1).
    path('areas/', VistaListaAreasSaberPro.as_view(), name='areas_saber_pro'),

    # Rutas accedidas por el rol Docente (HU-17): creación y gestión de cursos Saber Pro.
    path('', include('apps.saber_pro.urls.docente')),

    # Rutas accedidas por el rol Estudiante (HU-18): inscripción por código.
    path('', include('apps.saber_pro.urls.estudiante')),
]