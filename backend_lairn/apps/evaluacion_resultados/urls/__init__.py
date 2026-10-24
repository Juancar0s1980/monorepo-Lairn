"""Rutas de `evaluacion_resultados`: administración/coordinación y docente."""

from django.urls import include, path

urlpatterns = [
    path('docente/', include('apps.evaluacion_resultados.urls.docente')),
    path('', include('apps.evaluacion_resultados.urls.administrador')),
]
