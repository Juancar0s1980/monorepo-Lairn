"""
Paquete de vistas para el recurso Examen.

Agrupa los endpoints que operan sobre el modelo `Examen`, separados por rol:
- `vista_crear_examen`: operaciones de gestión para el Docente (crear y listar
  exámenes propios sobre todos sus cursos).
- `vista_examenes_curso`: consulta de exámenes para el Estudiante dentro de un
  curso en el que se encuentra inscrito.

La separación por archivo responde a que cada vista tiene un permiso distinto
(`EsDocente` vs `EsEstudiante`), un scope distinto (todos los cursos del docente
vs un curso específico) y un serializer distinto, lo que mantiene cada vista
con una sola responsabilidad y un único contrato de respuesta.
"""

from .vista_crear_examen import VistaCrearExamen
from .vista_detalle_examen import VistaDetalleExamen
from .vista_examenes_curso import VistaExamenesCurso
from .vista_admin_examenes import VistaAdminExamenes
from .vista_generar_practica_examen import VistaGenerarPracticaExamen
