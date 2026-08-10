"""
Rutas de la app `examenes` accedidas por el rol Docente.

Registra los endpoints de gestión de cursos, exámenes y estudiantes inscritos.
Cada `path` apunta a una vista que ya impone `permission_classes = [EsDocente]`,
de modo que este archivo solo se ocupa de definir el mapeo URL→vista y no
duplica controles de autorización.

La estructura colección/detalle sigue la convención REST: `cursos/` para
operaciones de colección y `cursos/<id>/` para operaciones sobre un curso
específico, en una sola entrada que despacha por verbo HTTP.
"""

from django.urls import path
from apps.examenes.views import (
    VistaCrearCurso,
    VistaDetalleCurso,
    VistaCrearExamen,
    VistaDetalleExamen,
    VistaEstudiantesCurso,
    VistaObjetivosCurso,
    VistaDetalleObjetivo,
    VistaSugerirObjetivos,
    VistaCargarPlanAula,
    VistaGenerarPracticaExamen,
)

urlpatterns = [
    # Colección de cursos del docente: creación (POST) y listado (GET).
    path('cursos/', VistaCrearCurso.as_view(), name='cursos'),

    # Detalle de un curso del docente: retrieve (GET), update (PUT/PATCH) y delete (DELETE).
    path('cursos/<int:curso_id>/', VistaDetalleCurso.as_view(), name='detalle_curso'),

    # Creación de exámenes asociados a un curso del docente.
    path('examenes/', VistaCrearExamen.as_view(), name='examenes'),

    # Detalle de un examen del docente: retrieve (GET), update (PUT/PATCH) y delete (DELETE).
    # Update/delete se bloquean si hay sesiones de estudiantes en progreso sobre el examen.
    path('examenes/<int:examen_id>/', VistaDetalleExamen.as_view(), name='detalle_examen'),

    # Genera (o recupera) el laboratorio de práctica vinculado a un examen. Idempotente.
    path('examenes/<int:examen_id>/generar-practica/', VistaGenerarPracticaExamen.as_view(), name='generar_practica_examen'),

    # Listado de estudiantes inscritos en un curso del docente.
    path('cursos/<int:curso_id>/estudiantes/', VistaEstudiantesCurso.as_view(), name='estudiantes_curso'),

    # Eliminación de la inscripción de un estudiante específico en un curso del docente.
    path('cursos/<int:curso_id>/estudiantes/<int:estudiante_id>/', VistaEstudiantesCurso.as_view(), name='eliminar_estudiante'),

    # Objetivos de aprendizaje del curso: listado (GET) y creación (POST).
    path('cursos/<int:curso_id>/objetivos/', VistaObjetivosCurso.as_view(), name='objetivos_curso'),

    # Sugerencias de objetivos con IA (no guarda; el docente curata y crea con el POST normal).
    path('cursos/<int:curso_id>/objetivos/sugerir/', VistaSugerirObjetivos.as_view(), name='sugerir_objetivos'),

    # Detalle de un objetivo: edición (PATCH) y eliminación (DELETE).
    path('cursos/<int:curso_id>/objetivos/<int:objetivo_id>/', VistaDetalleObjetivo.as_view(), name='detalle_objetivo'),

    # Carga del plan de aula (PDF): genera y guarda los objetivos directamente. Un solo uso por curso.
    path('cursos/<int:curso_id>/plan-aula/', VistaCargarPlanAula.as_view(), name='cargar_plan_aula'),
]
