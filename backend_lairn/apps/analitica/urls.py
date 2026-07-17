from django.urls import path
from apps.analitica.views import (
    VistaMisResultados,
    VistaResultadosCurso,
    VistaAvanceEstudiante,
    VistaModeloConocimientoEstudiante,
    VistaPatronesCurso,
    VistaResumenCurso,
    VistaMisResultadosExamen,
    VistaMiAvanceCurso,
    VistaMiConocimiento,
    VistaResumenGlobal,
    VistaCursosAdmin,
    VistaRedesModelos,
    VistaRedesResultados,
    VistaCumplimientoObjetivos,
    VistaEvolucionCurso,
    VistaMejoraIntentos,
)

urlpatterns = [
    # Estudiante — generales
    path('mis-resultados/', VistaMisResultados.as_view(), name='mis_resultados'),
    path('mis-resultados/examen/<int:examen_id>/', VistaMisResultadosExamen.as_view(), name='mis_resultados_examen'),
    path('mi-avance/curso/<int:curso_id>/', VistaMiAvanceCurso.as_view(), name='mi_avance_curso'),
    path('mi-conocimiento/curso/<int:curso_id>/', VistaMiConocimiento.as_view(), name='mi_conocimiento'),

    # Docente — resumen y patrones del curso
    path('curso/<int:curso_id>/resumen/', VistaResumenCurso.as_view(), name='resumen_curso'),
    path('curso/<int:curso_id>/patrones/', VistaPatronesCurso.as_view(), name='patrones_curso'),
    path('curso/<int:curso_id>/resultados/', VistaResultadosCurso.as_view(), name='resultados_curso'),
    path('curso/<int:curso_id>/objetivos/', VistaCumplimientoObjetivos.as_view(), name='cumplimiento_objetivos'),
    path('curso/<int:curso_id>/evolucion/', VistaEvolucionCurso.as_view(), name='evolucion_curso'),
    path('curso/<int:curso_id>/mejora-intentos/', VistaMejoraIntentos.as_view(), name='mejora_intentos'),

    # Docente — por estudiante
    path('curso/<int:curso_id>/estudiante/<int:estudiante_id>/', VistaAvanceEstudiante.as_view(), name='avance_estudiante'),
    path('curso/<int:curso_id>/estudiante/<int:estudiante_id>/conocimiento/', VistaModeloConocimientoEstudiante.as_view(), name='modelo_conocimiento'),

    # Administrador — métricas globales del sistema
    path('administracion/resumen/', VistaResumenGlobal.as_view(), name='admin_resumen_global'),
    path('administracion/cursos/', VistaCursosAdmin.as_view(), name='admin_cursos'),

    # Administrador — panel de Redes Neuronales
    path('administracion/redes/modelos/', VistaRedesModelos.as_view(), name='admin_redes_modelos'),
    path('administracion/redes/resultados/', VistaRedesResultados.as_view(), name='admin_redes_resultados'),
]
