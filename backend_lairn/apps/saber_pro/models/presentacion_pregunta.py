"""
Modelo `PresentacionPregunta` (HU-21).

Congela el contenido de cada bloque del simulacro en el momento de iniciar el
intento. El campo `datos` es una copia del contenido aprobado (enunciado,
opciones, relaciones, preguntas y respuesta correcta). Así una aprobación,
edición o regeneración del banco nunca modifica un examen en curso ni los
resultados históricos.

`orden` define la secuencia obligatoria de presentación; el estudiante no puede
retroceder ni saltar bloques.
"""

from django.db import models


class PresentacionPregunta(models.Model):
    presentacion = models.ForeignKey(
        'PresentacionSimulacro',
        on_delete=models.CASCADE,
        related_name='preguntas',
    )
    contenido = models.ForeignKey(
        'ContenidoBancoSaberPro',
        on_delete=models.PROTECT,
        related_name='presentaciones_pregunta',
    )
    orden = models.PositiveIntegerField()
    datos = models.JSONField(
        default=dict,
        help_text='Copia congelada del contenido y su respuesta correcta al iniciar el intento.',
    )

    class Meta:
        db_table = 'presentacion_preguntas_saber_pro'
        ordering = ['orden', 'id']
        verbose_name = 'Pregunta de presentación Saber Pro'
        verbose_name_plural = 'Preguntas de presentación Saber Pro'
        unique_together = [('presentacion', 'orden')]
        constraints = [
            models.UniqueConstraint(
                fields=['presentacion', 'contenido'],
                name='presentacion_pregunta_contenido_unico',
            ),
        ]

    def __str__(self):
        return f'{self.presentacion} - bloque {self.orden}'
