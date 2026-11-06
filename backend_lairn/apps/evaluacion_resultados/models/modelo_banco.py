"""
Modelo `PreguntaBanco`: banco oficial de preguntas por RA (HU-04 / HU-05).

Ciclo de vida (curaduría docente):
  pendiente (generada por IA o manual) --aprobar--> aprobada
                                       --descartar--> descartada
Solo las `aprobada` forman el banco oficial que usará el ensamblado de
evaluaciones formales (HU-06). Las pendientes y descartadas nunca se
exponen a estudiantes: el banco no tiene endpoints de estudiante.

Categorización completa (HU-05.3): asignatura + RA (y por él la
competencia del RA) + competencia transversal opcional usada como filtro
de generación (HU-04.1 / 04.3 / 04.5).
"""

from django.conf import settings
from django.db import models


class OpcionesEstadoPregunta(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de validación'
    APROBADA = 'aprobada', 'Aprobada'
    DESCARTADA = 'descartada', 'Descartada'


class OpcionesOrigenPregunta(models.TextChoices):
    IA = 'ia', 'Generada por IA'
    MANUAL = 'manual', 'Creada por el docente'


class PreguntaBanco(models.Model):
    asignatura = models.ForeignKey(
        'AsignaturaMalla', on_delete=models.PROTECT, related_name='preguntas_banco',
    )
    resultado = models.ForeignKey(
        'ResultadoAprendizaje', on_delete=models.PROTECT, related_name='preguntas_banco',
        help_text='RA que evalúa la pregunta (debe pertenecer a la asignatura).',
    )
    competencia_transversal = models.ForeignKey(
        'Competencia', on_delete=models.PROTECT, null=True, blank=True,
        related_name='preguntas_banco',
        help_text='Competencia transversal entrenada; queda asociada desde la generación (HU-04.3).',
    )
    contexto = models.TextField(
        blank=True, default='',
        help_text='Caso o situación real que el estudiante debe analizar (HU-04.4).',
    )
    enunciado = models.TextField()
    opciones = models.JSONField(
        default=list,
        help_text='Lista de textos de opción (selección múltiple con única respuesta).',
    )
    respuesta_correcta = models.PositiveSmallIntegerField(
        help_text='Índice (base 0) de la opción correcta dentro de `opciones`.',
    )
    retroalimentacion = models.TextField(
        blank=True, default='',
        help_text='Justificación de la respuesta correcta.',
    )
    estado = models.CharField(
        max_length=20, choices=OpcionesEstadoPregunta.choices,
        default=OpcionesEstadoPregunta.PENDIENTE, db_index=True,
    )
    origen = models.CharField(
        max_length=20, choices=OpcionesOrigenPregunta.choices, default=OpcionesOrigenPregunta.IA,
    )
    datos_generacion = models.JSONField(
        default=dict, blank=True,
        help_text='Parámetros de la generación (proveedor/modelo) para auditoría.',
    )
    motivo_descarte = models.CharField(max_length=300, blank=True, default='')
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+',
    )
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    revisado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ev_preguntas_banco'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['asignatura', 'estado']),
            models.Index(fields=['competencia_transversal', 'estado']),
        ]

    def __str__(self) -> str:
        return f'[{self.estado}] {self.enunciado[:60]}'
