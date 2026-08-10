from .laboratorio import Laboratorio
from .pregunta import Pregunta, TIPO_CHOICES, LENGUAJE_CHOICES
from .caso_test import CasoTest
from .entrega import Entrega
from .variante_problema_visual import VarianteProblemaVisual, AsignacionVariante

__all__ = [
    'Laboratorio', 'Pregunta', 'TIPO_CHOICES', 'LENGUAJE_CHOICES', 'CasoTest', 'Entrega',
    'VarianteProblemaVisual', 'AsignacionVariante',
]
