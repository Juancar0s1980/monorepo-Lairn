from django.conf import settings
from django.db import models


ESTADO_CHOICES = [
    ('en_progreso', 'En progreso'),
    ('completado', 'Completado'),
]


class SesionExamen(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sesiones'
    )
    examen = models.ForeignKey(
        'examenes.Examen',
        on_delete=models.CASCADE,
        related_name='sesiones'
    )
    intento = models.IntegerField(default=1)
    dificultad_actual = models.IntegerField(default=2)
    preguntas_respondidas = models.IntegerField(default=0)
    pregunta_actual = models.JSONField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_progreso')
    iniciado_en = models.DateTimeField(auto_now_add=True)
    completado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sesiones_examen'
        unique_together = ('estudiante', 'examen', 'intento')
