"""
Modelo de dominio `DistribucionSimulacro` (HU-19).

Define qué criterios académicos cubre un simulacro y cuántas preguntas aporta
cada uno. Se adapta a la estructura del área del curso sin mezclar criterios:

- Áreas estructuradas: una fila puede apuntar a una competencia o a una
  afirmación (la afirmación siempre pertenece a la competencia).
- Inglés: la fila apunta a una `parte` de la 1 a la 7.
- Comunicación Escrita: no usa distribución; el simulacro toma consignas
  aprobadas del banco del área.

En las áreas estructuradas y en Comunicación Escrita la suma de `cantidad`
debe coincidir con `Simulacro.num_preguntas`. En Inglés cada fila representa
una de las 7 partes obligatorias y aporta un bloque completo, por lo que
`cantidad` siempre vale 1 y el total fijo de preguntas es 45.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Criterio y cantidad de preguntas que aporta a un simulacro.
class DistribucionSimulacro(models.Model):
    simulacro = models.ForeignKey(
        'Simulacro',
        on_delete=models.CASCADE,
        related_name='distribuciones',
    )
    competencia = models.ForeignKey(
        'CompetenciaSaberPro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distribuciones_simulacro',
    )
    afirmacion = models.ForeignKey(
        'AfirmacionSaberPro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distribuciones_simulacro',
    )
    parte = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text='Parte 1 a 7 del examen de Inglés; vacío en las demás áreas.',
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Preguntas que este criterio aporta al simulacro.',
    )

    class Meta:
        db_table = 'distribuciones_simulacro_saber_pro'
        ordering = ['id']
        verbose_name = 'Distribución de simulacro Saber Pro'
        verbose_name_plural = 'Distribuciones de simulacro Saber Pro'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(parte__isnull=True) | models.Q(parte__gte=1, parte__lte=7),
                name='distribucion_simulacro_parte_rango',
            ),
        ]

    def __str__(self):
        criterio = self.afirmacion or self.competencia or f'Parte {self.parte}'
        return f'{criterio} ({self.cantidad})'

    def etiqueta(self):
        """Nombre legible del criterio para mensajes de validación."""
        if self.afirmacion_id:
            return self.afirmacion.nombre
        if self.competencia_id:
            return self.competencia.nombre
        if self.parte:
            return f'Parte {self.parte} de Inglés'
        return 'Criterio sin definir'
