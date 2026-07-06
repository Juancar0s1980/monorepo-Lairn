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

    # Docente — por estudiante
    path('curso/<int:curso_id>/estudiante/<int:estudiante_id>/', VistaAvanceEstudiante.as_view(), name='avance_estudiante'),
    path('curso/<int:curso_id>/estudiante/<int:estudiante_id>/conocimiento/', VistaModeloConocimientoEstudiante.as_view(), name='modelo_conocimiento'),
]
