"""
Paquete de serializers de la app `examenes`.

Define los contratos de entrada y salida JSON de la API. Cada archivo agrupa
los serializers asociados a un mismo recurso, lo que permite tener múltiples
"vistas" del mismo modelo según el caso de uso (gestión por el docente,
consumo por el estudiante, formulario de inscripción, etc.) sin duplicar la
configuración del `Meta` ni los validadores.

Este `__init__.py` reexporta los serializers para que el resto del proyecto
pueda importarlos desde `apps.examenes.serializers` sin acoplarse a la ruta
interna de cada archivo.
"""

from .serializador_curso import SerializadorCrearCurso, SerializadorCurso, SerializadorCursoEstudiante
from .serializador_inscripcion import SerializadorInscribirse, SerializadorInscripcion
from .serializador_examen import SerializadorCrearExamen, SerializadorExamen
from .serializador_estudiante import SerializadorEstudianteCurso
