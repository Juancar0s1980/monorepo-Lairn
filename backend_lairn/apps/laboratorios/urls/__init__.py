"""
Paquete de URLs de la app `laboratorios`. Montado por el proyecto raíz bajo
`api/laboratorios/`, dividido por rol igual que `apps.examenes`.
"""

from django.urls import include, path

urlpatterns = [
    path('', include('apps.laboratorios.urls.docente')),
    path('', include('apps.laboratorios.urls.estudiante')),
]
