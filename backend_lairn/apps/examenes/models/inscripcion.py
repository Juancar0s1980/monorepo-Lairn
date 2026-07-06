"""
Modelo de dominio `Inscripcion`.

Representa la relación N:N entre un Estudiante y un Curso, materializada
como tabla intermedia explícita para poder llevar metadatos (la fecha de
inscripción) y exponer la inscripción como recurso propio en la API.

La unicidad de la pareja (estudiante, curso) está garantizada a nivel de
base de datos mediante `unique_together`, lo que evita inscripciones
duplicadas incluso ante condiciones de carrera en las vistas.
"""

from django.conf import settings
from django.db import models


# Modelo intermedio que materializa la relación estudiante-curso e impone unicidad de la pareja.
class Inscripcion(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscripciones'
    )
    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='inscripciones'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inscripciones'
        unique_together = ('estudiante', 'curso')
