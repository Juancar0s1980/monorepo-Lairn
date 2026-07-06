"""
Modelo de dominio `Curso`.

Representa un curso creado por un docente, que actúa como contenedor de
exámenes y como punto de entrada para la inscripción de estudiantes.

Cada curso lleva un `codigo` único y opaco de 8 caracteres alfanuméricos
que el docente comparte con sus estudiantes para que se auto-inscriban
sin necesidad de exponer el id interno ni listar cursos públicamente.
La eliminación del docente arrastra sus cursos por `on_delete=CASCADE`.
"""

import random
import string
from django.conf import settings
from django.db import models


# Genera un código alfanumérico de 8 caracteres en mayúsculas para identificar al curso.
def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Modelo que representa un curso de un docente y sirve de contenedor para exámenes e inscripciones.
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cursos'
    )
    codigo = models.CharField(max_length=8, unique=True, default=generar_codigo)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cursos'
