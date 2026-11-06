"""
Sistema de alerta temprana (HU-10).

- `ReglaAlerta` (una sola, la define el Administrador, HU-10.1): alertar
  cuando haya `actividades_minimas` o más actividades con desempeño por
  debajo de `porcentaje_minimo`.
- `AlertaDesempeno` (HU-10.2): una alerta abierta por estudiante (dentro de
  un programa) o por curso (asignatura). Se recalcula al evaluar: si la
  condición desaparece, la alerta abierta pasa a `resuelta`; el Coordinador
  la marca `atendida` con una nota de seguimiento.

Actividad = evaluación formal presentada (% de aciertos) o tarea calificada
(nota / 5 × 100).
"""

from django.conf import settings
from django.db import models


class ReglaAlerta(models.Model):
    porcentaje_minimo = models.PositiveSmallIntegerField(default=60, help_text='Por debajo de este % la actividad cuenta.')
    actividades_minimas = models.PositiveSmallIntegerField(default=3, help_text='Cuántas actividades bajas activan la alerta.')
    activa = models.BooleanField(default=True)
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_regla_alerta'

    @classmethod
    def vigente(cls):
        regla, _ = cls.objects.get_or_create(pk=1)
        return regla


class OpcionesTipoAlerta(models.TextChoices):
    ESTUDIANTE = 'estudiante', 'Estudiante'
    CURSO = 'curso', 'Curso'


class OpcionesEstadoAlerta(models.TextChoices):
    ABIERTA = 'abierta', 'Abierta'
    ATENDIDA = 'atendida', 'Atendida'
    RESUELTA = 'resuelta', 'Resuelta (ya no cumple la condición)'


class AlertaDesempeno(models.Model):
    tipo = models.CharField(max_length=20, choices=OpcionesTipoAlerta.choices)
    programa = models.ForeignKey('ProgramaAcademico', on_delete=models.CASCADE, related_name='alertas')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    asignatura = models.ForeignKey('AsignaturaMalla', on_delete=models.CASCADE, null=True, blank=True, related_name='alertas')
    actividades_bajas = models.PositiveIntegerField(default=0)
    total_actividades = models.PositiveIntegerField(default=0)
    detalle = models.JSONField(default=list, blank=True, help_text='Actividades por debajo del umbral.')
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoAlerta.choices, default=OpcionesEstadoAlerta.ABIERTA, db_index=True,
    )
    nota_seguimiento = models.TextField(blank=True, default='')
    atendida_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    atendida_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_alertas_desempeno'
        ordering = ['-actividades_bajas', '-creada_en']
        indexes = [models.Index(fields=['programa', 'estado'])]
