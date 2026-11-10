"""
Rutas institucionales del módulo Saber Pro (HU-24.3/24.4).

Registra la analítica académica consolidada y su catálogo de filtros. Las
vistas imponen `EsLectorAnalitica` (Coordinador, Vicerrector y Administrador en
solo lectura), de modo que este archivo solo mapea URL -> vista.
"""

from django.urls import path

from apps.saber_pro.views import (
    VistaAnaliticaInstitucionalSaberPro,
    VistaCatalogoInstitucionalSaberPro,
    VistaExportarAnaliticaInstitucionalSaberPro,
)

urlpatterns = [
    # Analítica consolidada de todos los cursos de la institución.
    path(
        'institucional/analitica/',
        VistaAnaliticaInstitucionalSaberPro.as_view(),
        name='analitica_institucional_saber_pro',
    ),

    # Exportación .xlsx de la analítica consolidada (HU-24.6).
    path(
        'institucional/analitica/exportar/',
        VistaExportarAnaliticaInstitucionalSaberPro.as_view(),
        name='exportar_analitica_institucional_saber_pro',
    ),

    # Catálogo de áreas, carreras y cursos para poblar los filtros.
    path(
        'institucional/catalogo/',
        VistaCatalogoInstitucionalSaberPro.as_view(),
        name='catalogo_institucional_saber_pro',
    ),
]
