"""
Modelo `IntentoEvaluacion`: presentación de una evaluación formal de tipo
cuestionario por parte de un estudiante (HU-07).

- Un único intento por estudiante y evaluación.
- `vence_en` = el menor entre (inicio + duración) y el cierre de la ventana.
- Cada respuesta se guarda al marcarla (HU-07.2) en `respuestas`
  ({"<pregunta_id>": índice_opción}).
- Al vencer sin envío manual, el intento se cierra con lo registrado hasta
  ese momento (`envio_automatico=True`, HU-07.3). El cierre es perezoso: se
  aplica en cuanto alguien consulta el intento, así no depende de que el
  navegador del estudiante siga abierto.
- `aciertos`/`total`/`nota` se calculan al cerrar y alimentarán la
  analítica por RA (HU-09).
- Integridad académica (ADR-010): el servidor lleva el estado
  normal → advertido → suspendido → (reactivado | anulado_fraude). Mientras
  está suspendido el tiempo se congela en `segundos_restantes_al_suspender`
  y el cierre automático no aplica. `resuelto_*` guarda la última decisión;
  el historial completo vive en `ResolucionIntegridad`.
"""

from django.conf import settings
from django.db import models


class OpcionesIntegridad(models.TextChoices):
    NORMAL = 'normal', 'Normal'
    ADVERTIDO = 'advertido', 'Advertido'
    SUSPENDIDO = 'suspendido', 'Suspendido'
    REACTIVADO = 'reactivado', 'Reactivado'
    ANULADO_FRAUDE = 'anulado_fraude', 'Anulado por fraude'


class IntentoEvaluacion(models.Model):
    evaluacion = models.ForeignKey('EvaluacionFormal', on_delete=models.PROTECT, related_name='intentos')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    iniciado_en = models.DateTimeField(auto_now_add=True)
    vence_en = models.DateTimeField()
    respuestas = models.JSONField(default=dict, blank=True)
    enviado_en = models.DateTimeField(null=True, blank=True)
    envio_automatico = models.BooleanField(default=False)
    aciertos = models.PositiveIntegerField(null=True, blank=True)
    total = models.PositiveIntegerField(null=True, blank=True)
    nota = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text='Escala 0-5.')
    integridad = models.CharField(
        max_length=20, choices=OpcionesIntegridad.choices, default=OpcionesIntegridad.NORMAL, db_index=True,
    )
    suspendido_en = models.DateTimeField(null=True, blank=True)
    segundos_restantes_al_suspender = models.PositiveIntegerField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    resuelto_en = models.DateTimeField(null=True, blank=True)
    motivo_resolucion = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        db_table = 'ev_intentos_evaluacion'
        ordering = ['-iniciado_en']
        constraints = [
            models.UniqueConstraint(fields=['evaluacion', 'estudiante'], name='uq_ev_intento_evaluacion_estudiante'),
        ]

    @property
    def enviado(self) -> bool:
        return self.enviado_en is not None

    @property
    def suspendido(self) -> bool:
        return self.integridad == OpcionesIntegridad.SUSPENDIDO

    @property
    def anulado(self) -> bool:
        return self.integridad == OpcionesIntegridad.ANULADO_FRAUDE
