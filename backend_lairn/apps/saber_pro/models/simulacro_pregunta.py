"""
Modelo intermedio `SimulacroPregunta` (HU-19).

Registra las preguntas concretas del banco asignadas a un simulacro, junto con
su orden de presentación. Se usa como `through` de `Simulacro.preguntas` para
poder fijar el orden y evitar duplicados.

El contenido se protege con `PROTECT`: una pieza aprobada que ya forma parte de
un simulacro no puede eliminarse, preservando la integridad del historial.
"""

from django.db import models


# Pregunta del banco asignada a un simulacro, con su orden de presentación.
class SimulacroPregunta(models.Model):
    simulacro = models.ForeignKey(
        'Simulacro',
        on_delete=models.CASCADE,
        related_name='preguntas_asignadas',
    )
    contenido = models.ForeignKey(
        'ContenidoBancoSaberPro',
        on_delete=models.PROTECT,
        related_name='asignaciones_simulacro',
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'simulacro_preguntas_saber_pro'
        ordering = ['orden', 'id']
        verbose_name = 'Pregunta de simulacro Saber Pro'
        verbose_name_plural = 'Preguntas de simulacro Saber Pro'
        constraints = [
            models.UniqueConstraint(
                fields=['simulacro', 'contenido'],
                name='simulacro_pregunta_unica',
            ),
        ]

    def __str__(self):
        return f'{self.simulacro} - pregunta {self.orden}'
