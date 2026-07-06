from django.conf import settings
from django.db import models


class ModeloConocimiento(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='modelos_conocimiento'
    )
    examen = models.ForeignKey(
        'examenes.Examen',
        on_delete=models.CASCADE,
        related_name='modelos_conocimiento'
    )
    conceptos = models.JSONField(default=dict)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modelos_conocimiento'
        unique_together = ('estudiante', 'examen')
