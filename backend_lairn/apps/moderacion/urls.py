from django.urls import path
from apps.moderacion.views import VistaCrearReporte, VistaListaReportes, VistaDetalleReporte

urlpatterns = [
    # Colección de reportes: creación (POST, cualquier autenticado) y listado (GET, Administrador).
    path('reportes/', VistaListaReportes.as_view(), name='lista_reportes'),
    path('reportes/crear/', VistaCrearReporte.as_view(), name='crear_reporte'),

    # Actualización de estado de un reporte (PATCH, Administrador).
    path('reportes/<int:reporte_id>/', VistaDetalleReporte.as_view(), name='detalle_reporte'),
]
