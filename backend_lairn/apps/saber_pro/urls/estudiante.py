"""
Rutas de la app `saber_pro` accedidas por el rol Estudiante (HU-18).

Registra los endpoints de la inscripción por código: unirse a un curso con el
código de acceso (HU-18.1, con la validación de HU-18.2 y el rechazo de
duplicado de HU-18.4) y consultar los cursos a los que el estudiante pertenece
(HU-18.3). Cada vista impone `permission_classes = [EsEstudiante]`; este archivo
solo define el mapeo URL→vista, como el resto del paquete `urls`.
"""

from django.urls import path
from apps.saber_pro.views import (
    VistaBloquearPresentacionSaberPro,
    VistaCursosEstudianteSaberPro,
    VistaDesbloquearPresentacionSaberPro,
    VistaEstadoPresentacionSaberPro,
    VistaFinalizarPresentacionSaberPro,
    VistaIniciarPresentacionSaberPro,
    VistaResponderPresentacionSaberPro,
    VistaSimulacrosEstudianteSaberPro,
    VistaUnirseCursoSaberPro,
)

urlpatterns = [
    # Inscripción del estudiante con el código de acceso (HU-18.1/18.2/18.4).
    path('estudiante/unirse/', VistaUnirseCursoSaberPro.as_view(), name='unirse_curso_saber_pro'),

    # Listado de cursos a los que el estudiante se ha unido (HU-18.3).
    path('estudiante/cursos/', VistaCursosEstudianteSaberPro.as_view(), name='cursos_estudiante_saber_pro'),

    # Simulacros activos de los cursos inscritos del estudiante (HU-19.5).
    path('estudiante/simulacros/', VistaSimulacrosEstudianteSaberPro.as_view(), name='simulacros_estudiante_saber_pro'),

    # Presentación cronometrada del simulacro (HU-21).
    path(
        'estudiante/simulacros/<int:simulacro_id>/presentaciones/',
        VistaIniciarPresentacionSaberPro.as_view(),
        name='iniciar_presentacion_saber_pro',
    ),
    path(
        'estudiante/presentaciones/<int:presentacion_id>/',
        VistaEstadoPresentacionSaberPro.as_view(),
        name='estado_presentacion_saber_pro',
    ),
    path(
        'estudiante/presentaciones/<int:presentacion_id>/responder/',
        VistaResponderPresentacionSaberPro.as_view(),
        name='responder_presentacion_saber_pro',
    ),
    path(
        'estudiante/presentaciones/<int:presentacion_id>/bloquear/',
        VistaBloquearPresentacionSaberPro.as_view(),
        name='bloquear_presentacion_saber_pro',
    ),
    path(
        'estudiante/presentaciones/<int:presentacion_id>/desbloquear/',
        VistaDesbloquearPresentacionSaberPro.as_view(),
        name='desbloquear_presentacion_saber_pro',
    ),
    path(
        'estudiante/presentaciones/<int:presentacion_id>/finalizar/',
        VistaFinalizarPresentacionSaberPro.as_view(),
        name='finalizar_presentacion_saber_pro',
    ),
]