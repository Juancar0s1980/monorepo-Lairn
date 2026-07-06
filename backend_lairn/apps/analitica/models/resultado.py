from django.conf import settings
from django.db import models


class Resultado(models.Model):
    sesion = models.OneToOneField(
        'motor_adaptativo.SesionExamen',
        on_delete=models.CASCADE,
        related_name='resultado'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resultados'
    )
    examen = models.ForeignKey(
        'examenes.Examen',
        on_delete=models.CASCADE,
        related_name='resultados'
    )
    puntaje = models.FloatField(default=0)
    nota = models.FloatField(default=1.0, help_text='Calificación en escala 1.0 a 5.0')
    total_preguntas = models.IntegerField()
    correctas = models.IntegerField(default=0)
    completado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resultados'


class RespuestaEstudiante(models.Model):
    resultado = models.ForeignKey(
        Resultado,
        on_delete=models.CASCADE,
        related_name='respuestas'
    )
    concepto = models.CharField(max_length=200, blank=True, default='')
    pregunta = models.TextField()
    respuesta_correcta = models.TextField()
    respuesta_incorrecta = models.TextField(blank=True, default='')
    tiempo_por_pregunta = models.IntegerField(help_text='Tiempo en segundos')
    dificultad = models.IntegerField()

    class Meta:
        db_table = 'respuestas_estudiante'
