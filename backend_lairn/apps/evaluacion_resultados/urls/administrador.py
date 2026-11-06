"""
Rutas de administración de `evaluacion_resultados`.

Permisos: programas = lectura Coordinador / escritura Administrador;
malla, competencias, RA, momentos, tablero y evaluaciones formales = Administrador o Coordinador;
cargues documentales e integración = solo Administrador;
reporte ejecutivo = Vicerrector o Administrador (solo lectura);
supervisión en sala, seguimiento y cargue de convocados = Administrador o Coordinador (ADR-009).

Montadas en `api/evaluacion/` (ver `backend_lairn/urls.py`).
Convención: el padre va en el path (`programas/<id>/...`) y la vista
lo valida; el cliente nunca elige el padre en el body.
"""

from django.urls import path

from apps.evaluacion_resultados.views.administrador import (
    VistaAprobarCargue,
    VistaAsignarSupervisor,
    VistaCargueConvocados,
    VistaQuitarConvocado,
    VistaResolverIntegridadGestor,
    VistaSeguimientoEvaluacion,
    VistaSupervisoresDisponibles,
    VistaCargarDocumento,
    VistaCursosVinculables,
    VistaAnalizarAsignacion,
    VistaConfirmarAsignacion,
    VistaPlantillaAsignacion,
    VistaDesempenoRA,
    VistaExportarReporte,
    VistaEstudiantesGestor,
    VistaPanelCoordinador,
    VistaPanelAdmin,
    VistaValidarEstudiantes,
    VistaOpcionesReporte,
    VistaCatalogoIndicadores,
    VistaReporteEjecutivo,
    VistaAlertasPrograma,
    VistaAtenderAlerta,
    VistaExportarAlertas,
    VistaReglaAlerta,
    VistaBancoElegible,
    VistaDetalleEvaluacion,
    VistaListaCrearEvaluaciones,
    VistaPublicarEvaluacion,
    VistaSeleccionPreguntas,
    VistaDetalleAsignatura,
    VistaDetalleCargue,
    VistaDetalleCompetencia,
    VistaDetalleMomento,
    VistaDetallePrograma,
    VistaDetalleResultado,
    VistaDetalleSemestre,
    VistaDetalleVinculo,
    VistaImportarJson,
    VistaImportarUrl,
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
    # HU-09.1: % de acierto por RA (solo Administrador).
    path('programas/<int:programa_id>/desempeno-ra/', VistaDesempenoRA.as_view(), name='ev_desempeno_ra'),
    # HU-11: reporte ejecutivo (Vicerrector y Administrador, solo lectura).
    path('reporte-ejecutivo/', VistaReporteEjecutivo.as_view(), name='ev_reporte_ejecutivo'),
    path('reporte-ejecutivo/indicadores/', VistaCatalogoIndicadores.as_view(), name='ev_reporte_indicadores'),
    path('reporte-ejecutivo/opciones/', VistaOpcionesReporte.as_view(), name='ev_reporte_opciones'),
    path('reporte-ejecutivo/exportar/', VistaExportarReporte.as_view(), name='ev_reporte_exportar'),
    # HU-10: alerta temprana.
    path('alertas/regla/', VistaReglaAlerta.as_view(), name='ev_alertas_regla'),
    path('alertas/<int:pk>/atender/', VistaAtenderAlerta.as_view(), name='ev_alerta_atender'),
    path('programas/<int:programa_id>/alertas/', VistaAlertasPrograma.as_view(), name='ev_alertas'),
    path('programas/<int:programa_id>/alertas/exportar/', VistaExportarAlertas.as_view(), name='ev_alertas_exportar'),
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
    path('cursos/', VistaCursosVinculables.as_view(), name='ev_cursos_vinculables'),
    # HU-06: evaluación formal por momento.
    path('momentos/<int:momento_id>/evaluaciones/', VistaListaCrearEvaluaciones.as_view(), name='ev_evaluaciones'),
    path('momentos/<int:momento_id>/banco-elegible/', VistaBancoElegible.as_view(), name='ev_banco_elegible'),
    path('evaluaciones/<int:pk>/', VistaDetalleEvaluacion.as_view(), name='ev_evaluacion_detalle'),
    path('evaluaciones/<int:pk>/preguntas/', VistaSeleccionPreguntas.as_view(), name='ev_evaluacion_preguntas'),
    path('evaluaciones/<int:pk>/publicar/', VistaPublicarEvaluacion.as_view(), name='ev_evaluacion_publicar'),
    # ADR-009: supervisión en sala, seguimiento en vivo y convocatoria masiva.
    # ADR-017: asignación masiva de docentes a asignaturas.
    path('asignacion-docentes/plantilla/', VistaPlantillaAsignacion.as_view(), name='ev_asignacion_plantilla'),
    path('asignacion-docentes/analizar/', VistaAnalizarAsignacion.as_view(), name='ev_asignacion_analizar'),
    path('asignacion-docentes/confirmar/', VistaConfirmarAsignacion.as_view(), name='ev_asignacion_confirmar'),
    # ADR-013: inicio del Coordinador.
    path('panel-admin/', VistaPanelAdmin.as_view(), name='ev_panel_admin'),
    path('panel-coordinador/', VistaPanelCoordinador.as_view(), name='ev_panel_coordinador'),
    # ADR-012: estudiantes convocados e inscritos (gestor) y validación global (Administrador).
    path('estudiantes/', VistaEstudiantesGestor.as_view(), name='ev_estudiantes'),
    path('estudiantes/validar/', VistaValidarEstudiantes.as_view(), name='ev_estudiantes_validar'),
    path('supervisores-disponibles/', VistaSupervisoresDisponibles.as_view(), name='ev_supervisores_disponibles'),
    path('evaluaciones/<int:pk>/supervisor/', VistaAsignarSupervisor.as_view(), name='ev_evaluacion_supervisor'),
    path('evaluaciones/<int:pk>/seguimiento/', VistaSeguimientoEvaluacion.as_view(), name='ev_evaluacion_seguimiento'),
    path('evaluaciones/<int:pk>/convocados/cargue/', VistaCargueConvocados.as_view(), name='ev_convocados_cargue'),
    path('evaluaciones/<int:pk>/intentos/<int:estudiante_id>/resolver/', VistaResolverIntegridadGestor.as_view(),
         name='ev_evaluacion_resolver'),
    path('evaluaciones/<int:pk>/convocados/<int:estudiante_id>/', VistaQuitarConvocado.as_view(), name='ev_convocado_quitar'),
    path('cargues/', VistaListaCargues.as_view(), name='ev_cargues'),
    path('cargues/subir/', VistaCargarDocumento.as_view(), name='ev_cargue_subir'),
    path('cargues/<int:pk>/', VistaDetalleCargue.as_view(), name='ev_cargue_detalle'),
    path('cargues/<int:cargue_id>/aprobar/', VistaAprobarCargue.as_view(), name='ev_cargue_aprobar'),
    path('integracion/importar-json/', VistaImportarJson.as_view(), name='ev_importar_json'),
    path('integracion/importar-url/', VistaImportarUrl.as_view(), name='ev_importar_url'),
    path('integracion/registros/', VistaListaRegistros.as_view(), name='ev_registros'),
    path('integracion/sincronizar/', VistaSincronizarNova.as_view(), name='ev_sincronizar'),
]
