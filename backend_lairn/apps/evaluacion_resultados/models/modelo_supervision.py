"""
Convocatoria extra y asistencia en sala de la evaluación formal (ADR-009).

- `ConvocadoEvaluacion`: estudiantes convocados por cargue masivo
  (Coordinador/Administrador) además de los inscritos en los cursos
  vinculados a las asignaturas de la evaluación. El cargue nunca toca a
  quien ya estaba convocado: solo agrega a quien falta.
- `AsistenciaEvaluacion`: llamado a lista del docente supervisor. Solo
  `presente` y `tarde` habilitan iniciar el intento (ver `ESTADOS_HABILITAN`).
  Llegar tarde no reduce la duración del intento; el vencimiento ya queda
  limitado por `fecha_fin` (`servicio_presentacion.calcular_vencimiento`).
"""

from django.conf import settings
from django.db import models


class OpcionesEstadoAsistencia(models.TextChoices):
    PRESENTE = 'presente', 'Presente'
    TARDE = 'tarde', 'Llegó tarde'
    AUSENTE = 'ausente', 'Ausente'
    EXCUSA = 'excusa', 'Con excusa'


class OpcionesTipoExcusa(models.TextChoices):
    PERMISO_MEDICO = 'permiso_medico', 'Permiso médico'
    CALAMIDAD = 'calamidad', 'Calamidad doméstica'
    INSTITUCIONAL = 'institucional', 'Actividad institucional'
    OTRA = 'otra', 'Otra'


ESTADOS_HABILITAN = {OpcionesEstadoAsistencia.PRESENTE, OpcionesEstadoAsistencia.TARDE}


class ConvocadoEvaluacion(models.Model):
    evaluacion = models.ForeignKey('EvaluacionFormal', on_delete=models.CASCADE, related_name='convocados_extra')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    agregado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ev_convocados_evaluacion'
        ordering = ['agregado_en']
        constraints = [
            models.UniqueConstraint(fields=['evaluacion', 'estudiante'], name='uq_ev_convocado_evaluacion'),
        ]


class AsistenciaEvaluacion(models.Model):
    evaluacion = models.ForeignKey('EvaluacionFormal', on_delete=models.CASCADE, related_name='asistencias')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    estado = models.CharField(max_length=10, choices=OpcionesEstadoAsistencia.choices)
    tipo_excusa = models.CharField(max_length=20, choices=OpcionesTipoExcusa.choices, blank=True, default='')
    observacion = models.CharField(max_length=300, blank=True, default='')
    llegada_en = models.DateTimeField(null=True, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_asistencias_evaluacion'
        constraints = [
            models.UniqueConstraint(fields=['evaluacion', 'estudiante'], name='uq_ev_asistencia_evaluacion'),
        ]

    @property
    def habilita(self) -> bool:
        return self.estado in ESTADOS_HABILITAN
