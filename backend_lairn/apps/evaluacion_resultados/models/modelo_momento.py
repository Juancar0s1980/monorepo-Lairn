"""
Modelos `MomentoEvaluacion` y `MomentoResultado` (HU-02.1 / 02.2 / 02.3).

Los momentos dependen de CADA carrera (ej. Ing. Software: 4-6-8;
otra carrera: 3-6-9). Por eso cuelgan de `ProgramaAcademico` y no son
globales. Se pueden definir:
  - manual (admin define [4,6,8]),
  - documento + IA (resolución del programa),
  - API NOVA.
"""

from django.db import models

from .modelo_base import ModeloTrazable


class MomentoEvaluacion(ModeloTrazable):
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.CASCADE, related_name='momentos',
    )
    semestre_referencia = models.PositiveIntegerField(
        help_text='Semestre en que se mide, ej. 4, 6 u 8.',
    )
    nombre = models.CharField(
        max_length=200,
        help_text='Ej. "Momento 1 - Cuarto semestre".',
    )
    periodo = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Periodo académico, ej. "2026-1".',
    )
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ev_momentos'
        ordering = ['programa_id', 'semestre_referencia']
        constraints = [
            models.UniqueConstraint(
                fields=['programa', 'semestre_referencia', 'nombre'],
                name='uq_ev_momento_prog_sem_nombre',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.programa.codigo} S{self.semestre_referencia}: {self.nombre}'


class MomentoResultado(ModeloTrazable):
    momento = models.ForeignKey(
        'MomentoEvaluacion', on_delete=models.CASCADE, related_name='vinculos',
    )
    resultado = models.ForeignKey(
        'ResultadoAprendizaje', on_delete=models.PROTECT, related_name='vinculos_momento',
    )
    obligatorio = models.BooleanField(
        default=True,
        help_text='False = complementario, no exigido en la evaluación formal.',
    )

    class Meta:
        db_table = 'ev_momentos_resultados'
        ordering = ['momento_id', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['momento', 'resultado'], name='uq_ev_momento_resultado',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.momento_id} -> RA {self.resultado_id} (oblig={self.obligatorio})'
