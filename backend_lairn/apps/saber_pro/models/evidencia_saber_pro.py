"""
Modelo de dominio `EvidenciaSaberPro` (HU-20).

Tercer y último nivel del catálogo académico: la evidencia es el comportamiento
observable con el que se demuestra una afirmación. El docente puede seleccionarla
al generar contenido con IA (HU-20.1).

Es opcional en la generación: el docente puede conformar el contenido solo con
la competencia y la afirmación. El catálogo que siembra `seed_saber_pro`
incluye todas las evidencias oficiales definidas una a una, incluidas las de
Multiperspectivismo y las de Conocimientos de Competencias Ciudadanas (antes
pendientes de descripción en la fuente académica).
"""

from django.db import models


# Evidencia observable de una afirmación del catálogo Saber Pro.
class EvidenciaSaberPro(models.Model):
    afirmacion = models.ForeignKey(
        'AfirmacionSaberPro',
        on_delete=models.CASCADE,
        related_name='evidencias',
    )
    nombre = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'evidencias_saber_pro'
        ordering = ['orden', 'id']
        verbose_name = 'Evidencia Saber Pro'
        verbose_name_plural = 'Evidencias Saber Pro'

    def __str__(self):
        return f'Evidencia {self.orden} ({self.afirmacion.competencia.nombre})'
