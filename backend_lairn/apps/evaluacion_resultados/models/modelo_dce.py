"""
Modelos DCE: `Competencia` y `ResultadoAprendizaje` (HU-01.6 / 01.7 / 01.8).

Mapeo a la Guía Icfes Diseño Centrado en Evidencias (2018):
  Dominio     -> ProgramaAcademico / AsignaturaMalla
  Afirmación  -> Competencia + ResultadoAprendizaje.descripcion
  Evidencia   -> ResultadoAprendizaje.evidencia_observable + criterios_rubrica
  Tarea       -> Pregunta / Laboratorio / Examen (apps existentes)

HU-01.8: si un RA ya se usó en una evaluación finalizada, no se edita
in-place: se crea una versión nueva (`version + 1`) y la anterior pasa a
`activo=False, estado_revision=inactivo`, enlazada vía `reemplazado_por`.
"""

from django.db import models

from .modelo_base import ModeloTrazable


class OpcionesTipoCompetencia(models.TextChoices):
    TRANSVERSAL = 'transversal', 'Transversal'
    ESPECIFICA = 'especifica', 'Específica'


class Competencia(ModeloTrazable):
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.CASCADE, related_name='competencias',
    )
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(
        max_length=20, choices=OpcionesTipoCompetencia.choices,
        default=OpcionesTipoCompetencia.ESPECIFICA,
    )
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ev_competencias'
        ordering = ['programa_id', 'tipo', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['programa', 'nombre', 'tipo'],
                name='uq_ev_competencia_programa_nombre_tipo',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.nombre} ({self.get_tipo_display()})'


class ResultadoAprendizaje(ModeloTrazable):
    competencia = models.ForeignKey(
        'Competencia', on_delete=models.PROTECT, related_name='resultados',
        help_text='PROTECT: no se puede borrar una competencia con RAs activos; se desactiva.',
    )
    asignatura = models.ForeignKey(
        'AsignaturaMalla', on_delete=models.PROTECT, related_name='resultados',
        help_text='Asignatura de la malla a la que pertenece el RA.',
    )
    descripcion = models.CharField(
        max_length=300,
        help_text='Afirmación DCE: lo que se infiere del estudiante (1 oración, infinitivo).',
    )
    evidencia_observable = models.TextField(
        blank=True, default='',
        help_text='Evidencia DCE: qué conducta/producto observable la soporta.',
    )
    tarea_sugerida = models.TextField(
        blank=True, default='',
        help_text='Tarea DCE: escenario que pide la evidencia.',
    )
    criterios_rubrica = models.JSONField(
        default=list, blank=True,
        help_text='Lista [{criterio, niveles, peso}] para rúbrica estructurada (HU-08B.2).',
    )
    reemplazado_por = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versiones_previas',
        help_text='Nueva versión que reemplaza a esta (histórico HU-01.8).',
    )

    class Meta:
        db_table = 'ev_resultados_aprendizaje'
        ordering = ['asignatura_id', 'id']
        indexes = [
            models.Index(fields=['competencia', 'activo']),
            models.Index(fields=['asignatura', 'activo']),
        ]

    def __str__(self) -> str:
        return f'RA v{self.version}: {self.descripcion[:80]}'
