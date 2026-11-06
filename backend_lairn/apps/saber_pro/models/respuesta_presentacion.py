"""
Modelo `RespuestaPresentacion` (HU-21).

Guarda la respuesta de un bloque de la presentación y su calificación. La
relación uno a uno con `PresentacionPregunta` impide reescribir una respuesta:
la navegación es secuencial y cada bloque se responde una sola vez.

`correctas` y `total_items` se calculan al recibir la respuesta. Las consignas
abiertas se guardan con `es_evaluable=False` y quedan pendientes de revisión
docente. El docente califica cada respuesta abierta en escala 0.0-5.0 y deja una
retroalimentación que el estudiante puede consultar al finalizar el intento.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RespuestaPresentacion(models.Model):
    presentacion = models.ForeignKey(
        'PresentacionSimulacro',
        on_delete=models.CASCADE,
        related_name='respuestas',
    )
    pregunta = models.OneToOneField(
        'PresentacionPregunta',
        on_delete=models.CASCADE,
        related_name='respuesta',
    )
    respuesta = models.JSONField(
        default=dict,
        help_text='Respuesta normalizada enviada por el estudiante.',
    )
    correctas = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    es_evaluable = models.BooleanField(
        default=True,
        help_text='Falso en consignas abiertas que requieren revisión docente.',
    )
    calificacion_docente = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Calificación manual de la respuesta abierta en escala 0.0-5.0.',
    )
    retroalimentacion = models.TextField(
        blank=True,
        default='',
        help_text='Comentario del docente visible para el estudiante.',
    )
    revisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas_revisadas_saber_pro',
    )
    revisada_en = models.DateTimeField(null=True, blank=True)
    respondida_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'respuestas_presentacion_saber_pro'
        ordering = ['respondida_en', 'id']
        verbose_name = 'Respuesta de presentación Saber Pro'
        verbose_name_plural = 'Respuestas de presentación Saber Pro'

    def __str__(self):
        return f'Respuesta de {self.presentacion} al bloque {self.pregunta.orden}'

    def esta_revisada(self) -> bool:
        """Indica si una respuesta abierta ya tiene calificación docente."""
        return not self.es_evaluable and self.calificacion_docente is not None
