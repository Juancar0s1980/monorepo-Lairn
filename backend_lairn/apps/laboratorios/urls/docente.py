"""
Rutas de la app `laboratorios` accedidas por el rol Docente.
"""

from django.urls import path
from apps.laboratorios.views import (
    VistaLaboratoriosCurso,
    VistaDetalleLaboratorio,
    VistaPreguntasLaboratorio,
    VistaDetallePreguntaCodigo,
    VistaSugerirPreguntasCodigo,
    VistaSugerirLaboratorioLibre,
    VistaAnaliticaLaboratorio,
)

urlpatterns = [
    # Colección de laboratorios de un curso: listado (GET) y creación (POST).
    path('cursos/<int:curso_id>/laboratorios/', VistaLaboratoriosCurso.as_view(), name='laboratorios_curso'),

    # Generar un laboratorio COMPLETO con IA a partir de un enunciado libre del docente
    # (no guarda; el docente curata y crea con los POST normales).
    path('cursos/<int:curso_id>/laboratorios/sugerir-libre/', VistaSugerirLaboratorioLibre.as_view(), name='sugerir_laboratorio_libre'),

    # Detalle de un laboratorio: retrieve con preguntas completas (GET), edición (PATCH), eliminación (DELETE).
    path('laboratorios/<int:laboratorio_id>/', VistaDetalleLaboratorio.as_view(), name='detalle_laboratorio'),

    # Preguntas de código de un laboratorio: listado (GET) y creación con casos de test anidados (POST).
    path('laboratorios/<int:laboratorio_id>/preguntas/', VistaPreguntasLaboratorio.as_view(), name='preguntas_laboratorio'),

    # Sugerir preguntas de código con IA, una por objetivo del curso (no guarda; el docente curata).
    path('laboratorios/<int:laboratorio_id>/preguntas/sugerir-ia/', VistaSugerirPreguntasCodigo.as_view(), name='sugerir_preguntas_codigo'),

    # Detalle de una pregunta de código: edición (PATCH) y eliminación (DELETE).
    path('preguntas/<int:pregunta_id>/', VistaDetallePreguntaCodigo.as_view(), name='detalle_pregunta_codigo'),

    # Analítica del laboratorio: por pregunta y por estudiante.
    path('laboratorios/<int:laboratorio_id>/analitica/', VistaAnaliticaLaboratorio.as_view(), name='analitica_laboratorio'),
]
