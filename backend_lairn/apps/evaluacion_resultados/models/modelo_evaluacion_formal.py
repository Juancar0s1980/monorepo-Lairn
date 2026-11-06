"""
Modelos `EvaluacionFormal` y `EvaluacionPregunta` (HU-06).

Una evaluación formal mide los RA vinculados a un momento de evaluación
(programa + semestre de referencia, HU-02). La arma el Administrador o el
Coordinador:
  - HU-06.1: parte del momento y sus RA vinculados.
  - HU-06.2: toma preguntas APROBADAS del banco oficial de esos RA.
  - HU-06.3: ventana de disponibilidad (inicio/fin) y duración del intento.
  - HU-06.4: tipo `cuestionario` (preguntas del banco) o `tarea` (apunta a
    una tarea práctica publicada, HU-08B).

Estados: `borrador` (editable) -> `publicada` (congelada). La presentación
por parte del estudiante (HU-07) solo leerá evaluaciones publicadas.

Supervisión en sala (ADR-009): si la evaluación tiene `supervisor` (docente
con cursos asignado por el Coordinador), el estudiante solo puede iniciarla
cuando ese docente lo marca presente o tarde en el llamado a lista. Sin
supervisor la presentación funciona igual que antes.
"""

from django.conf import settings
from django.db import models


class OpcionesTipoEvaluacion(models.TextChoices):
    CUESTIONARIO = 'cuestionario', 'Selección múltiple con única respuesta'
    TAREA = 'tarea', 'Tarea con asignación por entregar'


class OpcionesEstadoEvaluacion(models.TextChoices):
    BORRADOR = 'borrador', 'Borrador'
    PUBLICADA = 'publicada', 'Publicada'


class EvaluacionFormal(models.Model):
    momento = models.ForeignKey(
        'MomentoEvaluacion', on_delete=models.PROTECT, related_name='evaluaciones',
    )
    nombre = models.CharField(max_length=200)
    instrucciones = models.TextField(blank=True, default='')
    tipo = models.CharField(
        max_length=20, choices=OpcionesTipoEvaluacion.choices,
        default=OpcionesTipoEvaluacion.CUESTIONARIO,
    )
    fecha_inicio = models.DateTimeField(help_text='Desde cuándo pueden presentarla.')
    fecha_fin = models.DateTimeField(help_text='Hasta cuándo pueden iniciarla.')
    duracion_minutos = models.PositiveIntegerField(
        help_text='Tiempo de cada intento una vez iniciado (HU-07.3).',
    )
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoEvaluacion.choices,
        default=OpcionesEstadoEvaluacion.BORRADOR, db_index=True,
    )
    tarea = models.ForeignKey(
        'TareaPractica', on_delete=models.PROTECT, null=True, blank=True, related_name='evaluaciones_formales',
        help_text='Solo para tipo "tarea": tarea publicada cuyo RA está vinculado al momento.',
    )
    preguntas = models.ManyToManyField(
        'PreguntaBanco', through='EvaluacionPregunta', related_name='evaluaciones_formales',
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+',
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evaluaciones_supervisadas',
        help_text='Docente que hace el llamado a lista en sala (activa el control de asistencia).',
    )
    publicada_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_evaluaciones_formales'
        ordering = ['-fecha_inicio']

    def __str__(self) -> str:
        return f'{self.nombre} ({self.estado})'


class EvaluacionPregunta(models.Model):
    evaluacion = models.ForeignKey('EvaluacionFormal', on_delete=models.CASCADE, related_name='items')
    # PROTECT: una pregunta usada en una evaluación no puede desaparecer del banco.
    pregunta = models.ForeignKey('PreguntaBanco', on_delete=models.PROTECT, related_name='+')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'ev_evaluaciones_preguntas'
        ordering = ['orden', 'id']
        constraints = [
            models.UniqueConstraint(fields=['evaluacion', 'pregunta'], name='uq_ev_evaluacion_pregunta'),
        ]
