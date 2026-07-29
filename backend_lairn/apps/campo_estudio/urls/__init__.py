"""
Paquete de URLs de la app `campo_estudio`. Montado por el proyecto raíz bajo
`api/campo-estudio/`, dividido por rol igual que `apps.examenes`/`apps.laboratorios`.
"""

from django.urls import include, path

urlpatterns = [
    path('', include('apps.campo_estudio.urls.docente')),
    path('', include('apps.campo_estudio.urls.estudiante')),
]
