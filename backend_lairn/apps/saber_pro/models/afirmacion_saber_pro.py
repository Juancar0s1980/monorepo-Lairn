"""
Modelo de dominio `AfirmacionSaberPro` (HU-20).

Segundo nivel del catálogo académico: cada afirmación describe lo que el
estudiante debe poder hacer dentro de una competencia. El docente la selecciona
junto con la competencia al generar contenido (HU-20.1) y de ella cuelgan las
evidencias observables.

Cada afirmación pertenece a una única competencia, que a su vez está anclada a
un área: la cadena completa garantiza que el contenido generado quede asociado
al área del curso del docente (HU-20.1/20.3).
"""

from django.db import models


# Afirmación de una competencia del catálogo Saber Pro.
class AfirmacionSaberPro(models.Model):
    competencia = models.ForeignKey(
        'CompetenciaSaberPro',
        on_delete=models.CASCADE,
        related_name='afirmaciones',
    )
    nombre = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'afirmaciones_saber_pro'
        ordering = ['orden', 'id']
        verbose_name = 'Afirmación Saber Pro'
        verbose_name_plural = 'Afirmaciones Saber Pro'

    def __str__(self):
        return f'Afirmación {self.orden} ({self.competencia.nombre})'
