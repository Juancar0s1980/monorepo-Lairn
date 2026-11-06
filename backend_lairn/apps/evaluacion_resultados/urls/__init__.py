"""Rutas de `evaluacion_resultados`: administración/coordinación y docente."""

from django.urls import include, path

from apps.evaluacion_resultados.views.vista_ayuda import VistaDetalleAyuda, VistaListaAyuda, VistaVideoAyuda
from apps.evaluacion_resultados.views.vista_notas_momento import (
    VistaEsquemaInstitucional,
    VistaEsquemaMomento,
    VistaExportarNotasMomento,
    VistaMomentosConNotas,
    VistaNotasMomento,
)

urlpatterns = [
    # ADR-019: notas del momento (Administrador, Coordinador y Vicerrector).
    path('notas-momento/momentos/', VistaMomentosConNotas.as_view(), name='ev_notas_momentos'),
    path('notas-momento/esquema-institucional/', VistaEsquemaInstitucional.as_view(), name='ev_esquema_institucional'),
    path('notas-momento/<int:momento_id>/', VistaNotasMomento.as_view(), name='ev_notas_momento'),
    path('notas-momento/<int:momento_id>/exportar/', VistaExportarNotasMomento.as_view(), name='ev_notas_momento_exportar'),
    path('notas-momento/<int:momento_id>/esquema/', VistaEsquemaMomento.as_view(), name='ev_notas_momento_esquema'),
    # ADR-018: centro de ayuda (todos los roles con sesión; edición solo Administrador).
    path('ayuda/', VistaListaAyuda.as_view(), name='ev_ayuda'),
    path('ayuda/<slug:slug>/', VistaDetalleAyuda.as_view(), name='ev_ayuda_detalle'),
    path('ayuda/<slug:slug>/video/', VistaVideoAyuda.as_view(), name='ev_ayuda_video'),
    path('docente/', include('apps.evaluacion_resultados.urls.docente')),
    path('estudiante/', include('apps.evaluacion_resultados.urls.estudiante')),
    path('', include('apps.evaluacion_resultados.urls.administrador')),
]
