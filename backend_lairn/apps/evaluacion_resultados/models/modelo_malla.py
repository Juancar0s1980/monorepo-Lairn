"""
Modelos `SemestrePrograma` y `AsignaturaMalla` (HU-01.4 / 01.5).

La malla se puede construir por triple vía:
  - manual (semestre por semestre),
  - documento + IA (PDF del pensum descargado de la web institucional),
  - API NOVA (`external_id` para upsert idempotente).
"""

from django.db import models

from .modelo_base import ModeloTrazable


class SemestrePrograma(ModeloTrazable):
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.CASCADE, related_name='semestres',
    )
    numero = models.PositiveIntegerField(
        help_text='Número del semestre dentro del programa (1..N).',
    )
    nombre = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Nombre opcional, ej. "Cuarto semestre".',
    )

    class Meta:
        db_table = 'ev_semestres'
        ordering = ['programa_id', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['programa', 'numero'], name='uq_ev_semestre_programa_numero',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.programa.codigo} S{self.numero}'


class OpcionesTipoAsignatura(models.TextChoices):
    OBLIGATORIA = 'obligatoria', 'Obligatoria'
    ELECTIVA = 'electiva', 'Electiva'
    OPTATIVA = 'optativa', 'Optativa'
    PRACTICA = 'practica', 'Práctica / Laboratorio'


class AsignaturaMalla(ModeloTrazable):
    programa = models.ForeignKey(
        'ProgramaAcademico', on_delete=models.CASCADE, related_name='asignaturas',
    )
    semestre = models.ForeignKey(
        'SemestrePrograma', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='asignaturas',
        help_text='Semestre de la malla donde aparece. Null = aún sin ubicar.',
    )
    codigo = models.CharField(
        max_length=30, unique=True,
        help_text='Código institucional de la asignatura (único).',
    )
    nombre = models.CharField(max_length=200)
    creditos = models.PositiveIntegerField(default=3)
    intensidad_horaria = models.PositiveIntegerField(
        default=0,
        help_text='Horas semanales totales.',
    )
    tipo = models.CharField(
        max_length=20, choices=OpcionesTipoAsignatura.choices,
        default=OpcionesTipoAsignatura.OBLIGATORIA,
    )
    # Trazabilidad hacia lo que YA funciona: un Curso libre del docente
    # puede vincularse a una asignatura oficial sin romper nada.
    curso_vinculado = models.ForeignKey(
        'examenes.Curso', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='asignaturas_oficiales',
        help_text='Curso Lairn que implementa esta asignatura, si existe.',
    )

    class Meta:
        db_table = 'ev_asignaturas'
        ordering = ['programa_id', 'semestre__numero', 'nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['programa', 'activo']),
        ]

    def __str__(self) -> str:
        return f'{self.codigo} - {self.nombre}'
