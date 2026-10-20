"""Rutas de `evaluacion_resultados` (hoy solo administración)."""

from django.urls import include, path

urlpatterns = [
    path('', include('apps.evaluacion_resultados.urls.administrador')),
]
