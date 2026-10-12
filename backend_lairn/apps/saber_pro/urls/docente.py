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
    VistaAprobarContenidoBancoSaberPro,
    VistaContenidoBancoSaberPro,
    VistaCrearCursoSaberPro,
    VistaCriteriosAreaSaberPro,
    VistaDetalleContenidoBancoSaberPro,
    VistaDetalleCursoSaberPro,
    VistaEstudiantesCursoSaberPro,
    VistaGenerarContenidoSaberPro,
    VistaRegenerarCodigoCursoSaberPro,
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
]