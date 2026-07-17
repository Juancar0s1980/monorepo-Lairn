"""
Paquete de vistas para el recurso ObjetivoCurso (rol Docente).

- `vista_objetivos_curso`: colección — listar (GET) y crear (POST) objetivos
  de un curso propio.
- `vista_detalle_objetivo`: detalle — editar (PATCH) y eliminar (DELETE) un
  objetivo específico.
- `vista_sugerir_objetivos`: genera borradores de objetivos con la IA a partir
  del nombre y descripción del curso; NO guarda nada, el docente curata.
"""

from .vista_objetivos_curso import VistaObjetivosCurso
from .vista_detalle_objetivo import VistaDetalleObjetivo
from .vista_sugerir_objetivos import VistaSugerirObjetivos
