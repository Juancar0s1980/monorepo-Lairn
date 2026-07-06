"""
Paquete de modelos de dominio para la app `examenes`.

Define las tres entidades centrales del sistema y sus relaciones:
- `Curso`: agrupador de exámenes, propiedad de un docente.
- `Inscripcion`: relación N:N entre estudiantes y cursos (con unicidad
  garantizada a nivel de BD).
- `Examen`: configuración de una evaluación dentro de un curso.

Cada modelo vive en su propio archivo (`curso.py`, `inscripcion.py`,
`examen.py`) para mantener bajo el peso de cada archivo y facilitar la
navegación; este `__init__.py` los re-exporta para que el resto del
proyecto pueda importarlos desde `apps.examenes.models` sin necesidad
de conocer la ruta interna.
"""

from .curso import Curso
from .inscripcion import Inscripcion
from .examen import Examen
