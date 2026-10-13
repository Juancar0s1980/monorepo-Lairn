"""
Rutas de administración de `evaluacion_resultados` (solo Administrador).

Montadas en `api/evaluacion/` (ver `backend_lairn/urls.py`).
Convención: el padre va en el path (`programas/<id>/...`) y la vista
lo valida; el cliente nunca elige el padre en el body.
"""

from django.urls import path

from apps.evaluacion_resultados.views.administrador import (
    VistaAprobarCargue,
    VistaCargarDocumento,
    VistaDetalleAsignatura,
    VistaDetalleCargue,
    VistaDetalleCompetencia,
    VistaDetalleMomento,
    VistaDetallePrograma,
    VistaDetalleResultado,
    VistaDetalleSemestre,
    VistaDetalleVinculo,
    VistaImportarJson,
    VistaListaCargues,
    VistaListaCrearAsignaturas,
    VistaListaCrearCompetencias,
    VistaListaCrearMomentos,
    VistaListaCrearProgramas,
    VistaListaCrearResultados,
    VistaListaCrearSemestres,
    VistaListaRegistros,
    VistaSincronizarNova,
    VistaTableroPrograma,
    VistaVincularResultadoMomento,
)

urlpatterns = [
    path('programas/', VistaListaCrearProgramas.as_view(), name='ev_programas'),
    path('programas/<int:pk>/', VistaDetallePrograma.as_view(), name='ev_programa_detalle'),
    path('programas/<int:programa_id>/tablero/', VistaTableroPrograma.as_view(), name='ev_tablero'),
    path('programas/<int:programa_id>/semestres/', VistaListaCrearSemestres.as_view(), name='ev_semestres'),
    path('programas/<int:programa_id>/semestres/<int:pk>/', VistaDetalleSemestre.as_view(), name='ev_semestre_detalle'),
    path('programas/<int:programa_id>/asignaturas/', VistaListaCrearAsignaturas.as_view(), name='ev_asignaturas'),
    path('programas/<int:programa_id>/asignaturas/<int:pk>/', VistaDetalleAsignatura.as_view(), name='ev_asignatura_detalle'),
    path('programas/<int:programa_id>/competencias/', VistaListaCrearCompetencias.as_view(), name='ev_competencias'),
    path('competencias/<int:pk>/', VistaDetalleCompetencia.as_view(), name='ev_competencia_detalle'),
    path('programas/<int:programa_id>/resultados/', VistaListaCrearResultados.as_view(), name='ev_resultados'),
    path('programas/<int:programa_id>/momentos/', VistaListaCrearMomentos.as_view(), name='ev_momentos'),
    path('momentos/<int:pk>/', VistaDetalleMomento.as_view(), name='ev_momento_detalle'),
    path('resultados/<int:pk>/', VistaDetalleResultado.as_view(), name='ev_resultado_detalle'),
    path('momentos/<int:momento_id>/vinculos/', VistaVincularResultadoMomento.as_view(), name='ev_vinculos'),
    path('vinculos/<int:pk>/', VistaDetalleVinculo.as_view(), name='ev_vinculo_detalle'),
    path('cargues/', VistaListaCargues.as_view(), name='ev_cargues'),
    path('cargues/subir/', VistaCargarDocumento.as_view(), name='ev_cargue_subir'),
    path('cargues/<int:pk>/', VistaDetalleCargue.as_view(), name='ev_cargue_detalle'),
    path('cargues/<int:cargue_id>/aprobar/', VistaAprobarCargue.as_view(), name='ev_cargue_aprobar'),
    path('integracion/importar-json/', VistaImportarJson.as_view(), name='ev_importar_json'),
    path('integracion/registros/', VistaListaRegistros.as_view(), name='ev_registros'),
    path('integracion/sincronizar/', VistaSincronizarNova.as_view(), name='ev_sincronizar'),
]
