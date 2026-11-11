"""
Rutas de la app `saber_pro` accedidas por el rol Docente (HU-17 y HU-20).

Registra los endpoints de creación y gestión de cursos Saber Pro (HU-17) y del
banco de contenido generado con IA (HU-20). Cada `path` apunta a una vista que
ya impone `permission_classes = [EsDocente]`, de modo que este archivo solo
define el mapeo URL→vista y no duplica controles de autorización.

La estructura colección/detalle sigue la convención REST de `examenes`:
`cursos/` para colección y `cursos/<id>/` para el recurso individual; las
acciones anidadas (`regenerar-codigo/`, `estudiantes/`, `contenido/`) se
registran debajo del recurso sin conflictos de nombre.
"""

from django.urls import path

from apps.saber_pro.views import (
    VistaAnaliticaCursoSaberPro,
    VistaAnalisisAccionesSaberPro,
    VistaAprobarContenidoBancoSaberPro,
    VistaAprobarSolicitudDesbloqueoSaberPro,
    VistaContenidoBancoSaberPro,
    VistaCrearCursoSaberPro,
    VistaCriteriosAreaSaberPro,
    VistaDetalleContenidoBancoSaberPro,
    VistaDetalleCursoSaberPro,
    VistaDetalleSimulacroSaberPro,
    VistaDisponibilidadSimulacroSaberPro,
    VistaEstudiantesCursoSaberPro,
    VistaExportarAnaliticaCursoSaberPro,
    VistaGenerarContenidoSaberPro,
    VistaPreguntasSimulacroSaberPro,
    VistaRankingCursoSaberPro,
    VistaRechazarSolicitudDesbloqueoSaberPro,
    VistaRechazarYAnularSolicitudDesbloqueoSaberPro,
    VistaRegenerarCodigoCursoSaberPro,
    VistaResultadosSimulacroSaberPro,
    VistaRevisionPresentacionSaberPro,
    VistaSimulacrosCursoSaberPro,
    VistaSolicitudesDesbloqueoSaberPro,
)

urlpatterns = [
    # Colección de cursos Saber Pro del docente: creación (POST) y listado (GET) (HU-17).
    path('docente/cursos/', VistaCrearCursoSaberPro.as_view(), name='cursos_saber_pro_docente'),

    # Detalle de un curso Saber Pro del docente: retrieve (GET), update (PUT/PATCH)
    # y delete (DELETE). El GET expone el código vigente para compartir (HU-17.3).
    path('docente/cursos/<int:curso_id>/', VistaDetalleCursoSaberPro.as_view(), name='detalle_curso_saber_pro'),

    # Regeneración del código de acceso: invalida el vigente y asigna uno nuevo (HU-17.3).
    path('docente/cursos/<int:curso_id>/regenerar-codigo/', VistaRegenerarCodigoCursoSaberPro.as_view(), name='regenerar_codigo_curso_saber_pro'),

    # Listado de estudiantes inscritos al curso Saber Pro del docente (HU-17.5).
    path('docente/cursos/<int:curso_id>/estudiantes/', VistaEstudiantesCursoSaberPro.as_view(), name='estudiantes_curso_saber_pro'),

    # Retiro de un estudiante del curso Saber Pro (gestión de inscripciones).
    path('docente/cursos/<int:curso_id>/estudiantes/<int:estudiante_id>/', VistaEstudiantesCursoSaberPro.as_view(), name='retirar_estudiante_curso_saber_pro'),

    # Criterios de evaluación del área para generar contenido con IA (HU-20.1).
    path('docente/areas/<int:area_id>/criterios/', VistaCriteriosAreaSaberPro.as_view(), name='criterios_area_saber_pro'),

    # Generación y consulta del banco de contenido del área del curso (HU-20.1-20.3).
    path('docente/cursos/<int:curso_id>/contenido/generar/', VistaGenerarContenidoSaberPro.as_view(), name='generar_contenido_saber_pro'),
    path('docente/cursos/<int:curso_id>/contenido/', VistaContenidoBancoSaberPro.as_view(), name='contenido_banco_saber_pro'),

    # Detalle y aprobación de una pieza del banco (HU-20.3/20.4).
    path('docente/contenido/<int:contenido_id>/', VistaDetalleContenidoBancoSaberPro.as_view(), name='detalle_contenido_banco_saber_pro'),
    path('docente/contenido/<int:contenido_id>/aprobar/', VistaAprobarContenidoBancoSaberPro.as_view(), name='aprobar_contenido_banco_saber_pro'),

    # Simulacros del curso: colección (GET/POST) y disponibilidad del banco (HU-19.1-19.3).
    path('docente/cursos/<int:curso_id>/simulacros/', VistaSimulacrosCursoSaberPro.as_view(), name='simulacros_curso_saber_pro'),
    path('docente/cursos/<int:curso_id>/simulacros/disponibilidad/', VistaDisponibilidadSimulacroSaberPro.as_view(), name='disponibilidad_simulacro_saber_pro'),

    # Detalle, edición y eliminación de un simulacro (HU-19.4).
    path('docente/cursos/<int:curso_id>/simulacros/<int:simulacro_id>/', VistaDetalleSimulacroSaberPro.as_view(), name='detalle_simulacro_saber_pro'),

    # Preguntas asignadas al simulacro, en solo lectura y con respuestas correctas.
    path('docente/cursos/<int:curso_id>/simulacros/<int:simulacro_id>/preguntas/', VistaPreguntasSimulacroSaberPro.as_view(), name='preguntas_simulacro_saber_pro'),

    # Ranking nominal del curso, filtrable por simulacro o área (HU-23).
    path('docente/cursos/<int:curso_id>/ranking/', VistaRankingCursoSaberPro.as_view(), name='ranking_curso_saber_pro'),

    # Analítica del curso: resultados individuales/agregados y desgloses (HU-24.1/24.2).
    path('docente/cursos/<int:curso_id>/analitica/', VistaAnaliticaCursoSaberPro.as_view(), name='analitica_curso_saber_pro'),

    # Exportación .xlsx de la analítica del curso con los mismos filtros (HU-24.5).
    path('docente/cursos/<int:curso_id>/analitica/exportar/', VistaExportarAnaliticaCursoSaberPro.as_view(), name='exportar_analitica_curso_saber_pro'),

    # Análisis de acciones recomendadas con IA sobre la analítica del curso (HU-24).
    path('docente/cursos/<int:curso_id>/analitica/acciones/', VistaAnalisisAccionesSaberPro.as_view(), name='analisis_acciones_curso_saber_pro'),

    # Calificaciones de los estudiantes en escala 0.0-5.0 (HU-24).
    path('docente/cursos/<int:curso_id>/simulacros/<int:simulacro_id>/resultados/', VistaResultadosSimulacroSaberPro.as_view(), name='resultados_simulacro_saber_pro'),

    # Revisión y calificación de respuestas abiertas de un intento (HU-24).
    path('docente/cursos/<int:curso_id>/simulacros/<int:simulacro_id>/resultados/<int:presentacion_id>/revision/', VistaRevisionPresentacionSaberPro.as_view(), name='revision_presentacion_saber_pro'),

    # Notificaciones de desbloqueo: solicitudes pendientes y decisión remota.
    path('docente/solicitudes-desbloqueo/', VistaSolicitudesDesbloqueoSaberPro.as_view(), name='solicitudes_desbloqueo_saber_pro'),
    path('docente/solicitudes-desbloqueo/<int:solicitud_id>/aprobar/', VistaAprobarSolicitudDesbloqueoSaberPro.as_view(), name='aprobar_solicitud_desbloqueo_saber_pro'),
    path('docente/solicitudes-desbloqueo/<int:solicitud_id>/rechazar/', VistaRechazarSolicitudDesbloqueoSaberPro.as_view(), name='rechazar_solicitud_desbloqueo_saber_pro'),
    path('docente/solicitudes-desbloqueo/<int:solicitud_id>/rechazar-anular/', VistaRechazarYAnularSolicitudDesbloqueoSaberPro.as_view(), name='rechazar_anular_solicitud_desbloqueo_saber_pro'),
]