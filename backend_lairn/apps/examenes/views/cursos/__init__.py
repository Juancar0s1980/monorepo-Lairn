"""
Paquete de vistas para el recurso Curso.

Agrupa los endpoints que operan sobre el modelo `Curso`, separados por rol y
por nivel de granularidad:
- `vista_crear_curso`: endpoint colección para el Docente (crear y listar sus
  cursos).
- `vista_detalle_curso`: endpoint de detalle para el Docente (retrieve, update
  y delete sobre un curso específico).
- `vista_mis_cursos`: consulta del Estudiante (listado de los cursos en los que
  está inscrito).

Las operaciones de colección y de detalle se mantienen en archivos separados
para preservar la convención REST y para que cada vista exprese una sola
responsabilidad. La vista del estudiante vive aparte porque cambia el permiso
(`EsEstudiante`), el origen de los datos (vía `Inscripcion`) y el contrato
del serializer.
"""

from .vista_crear_curso import VistaCrearCurso
from .vista_detalle_curso import VistaDetalleCurso
from .vista_mis_cursos import VistaMisCursos
