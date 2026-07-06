"""
Paquete de vistas para el recurso Inscripcion.

Agrupa los endpoints que operan sobre el modelo `Inscripcion` (la relación
entre Estudiante y Curso), separados por rol y por el actor que origina
la operación:
- `vista_inscribirse`: crea una inscripción a partir del código del curso
  (acción del Estudiante).
- `vista_gestionar_estudiantes`: lista y elimina inscripciones de un curso
  propio (acciones del Docente sobre los estudiantes inscritos).

Aunque la vista del docente se nombra en términos de "estudiantes", el
recurso que efectivamente se manipula es `Inscripcion` —no se crea ni se
borra al usuario—, por eso vive en este paquete y no en uno separado de
estudiantes.
"""

from .vista_inscribirse import VistaInscribirse
from .vista_gestionar_estudiantes import VistaEstudiantesCurso
