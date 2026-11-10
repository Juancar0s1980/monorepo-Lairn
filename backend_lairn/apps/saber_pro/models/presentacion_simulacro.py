"""
Modelo de dominio `PresentacionSimulacro` (HU-21).

Representa un intento concreto de un estudiante sobre un simulacro. Guarda el
cronómetro y los agregados del intento, pero el contenido se congela en
`PresentacionPregunta` para que una edición posterior del banco o del simulacro
no altere un examen ya iniciado.

Reglas de negocio:

- Solo puede existir una presentación `en_progreso` por estudiante y simulacro.
  Un intento activo nunca se reanuda: si el estudiante vuelve a iniciar, el
  intento se cierra automáticamente por salida. Si ya venció, se finaliza por
  tiempo agotado.
- Cerrar un intento por salida solo finaliza ese intento: si al estudiante le
  quedan intentos disponibles, puede iniciar el siguiente.
- `expira_en` se fija al iniciar con `Simulacro.tiempo_limite_minutos`. El
  vencimiento se evalúa de forma perezosa en cada operación, sin depender de un
  proceso externo.
- Al finalizar se conserva el motivo (`completada`, `manual`, `tiempo_agotado`,
  `fecha_limite`, `salida`, `rechazado`, `anulado`) para que la HU-24 pueda
  distinguir intentos completos de abandonos, cierres por plazo o desbloqueos
  rechazados.
- Un intento `anulada` fue rechazado con la acción "rechazar y anular": su nota
  es siempre 0 sin importar el avance ni las respuestas, y el estudiante no
  puede iniciar nuevos intentos de ese simulacro aunque le quedaran disponibles.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

ESTADO_PRESENTACION_CHOICES = [
    ('en_progreso', 'En progreso'),
    ('finalizada', 'Finalizada'),
]

MOTIVO_FINALIZACION_CHOICES = [
    ('', 'Sin finalizar'),
    ('completada', 'Completada'),
    ('manual', 'Finalizada manualmente'),
    ('tiempo_agotado', 'Tiempo agotado'),
    ('fecha_limite', 'Fecha límite vencida'),
    ('salida', 'Cerrado por salir de la prueba'),
    ('rechazado', 'Cerrado por desbloqueo rechazado'),
    ('anulado', 'Anulado por desbloqueo rechazado'),
]


class PresentacionSimulacro(models.Model):
    simulacro = models.ForeignKey(
        'Simulacro',
        on_delete=models.CASCADE,
        related_name='presentaciones',
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presentaciones_saber_pro',
    )
    intento = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Número consecutivo de intento del estudiante sobre el simulacro.',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_PRESENTACION_CHOICES,
        default='en_progreso',
    )
    anulada = models.BooleanField(
        default=False,
        help_text=(
            'El docente rechazó y anuló el intento: su nota es 0 y el estudiante '
            'no puede iniciar nuevos intentos de este simulacro.'
        ),
    )
    bloqueada = models.BooleanField(
        default=False,
        help_text='El intento se bloqueó por una salida detectada y espera aprobación docente.',
    )
    motivo_finalizacion = models.CharField(
        max_length=20,
        choices=MOTIVO_FINALIZACION_CHOICES,
        blank=True,
        default='',
    )
    iniciada_en = models.DateTimeField(default=timezone.now, editable=False)
    expira_en = models.DateTimeField(
        help_text='Momento exacto en que se agota el tiempo del intento.',
    )
    finalizada_en = models.DateTimeField(null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    contenidos_respondidos = models.PositiveIntegerField(
        default=0,
        help_text='Cantidad de bloques del simulacro respondidos hasta el momento.',
    )
    total_items = models.PositiveIntegerField(
        default=0,
        help_text='Cantidad total de ítems del simulacro (una pregunta puede aportar varios).',
    )
    total_evaluables = models.PositiveIntegerField(
        default=0,
        help_text='Ítems que se pueden calificar automáticamente.',
    )
    correctas = models.PositiveIntegerField(default=0)
    puntaje = models.FloatField(
        default=0,
        help_text='Porcentaje de acierto sobre los ítems evaluables (0 a 100).',
    )
    requiere_revision = models.BooleanField(
        default=False,
        help_text='El intento incluye respuestas abiertas que requieren revisión docente.',
    )

    calificacion_docente = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Calificación 0.0-5.0 que el docente asigna a las consignas abiertas del intento.',
    )
    retroalimentacion_docente = models.TextField(
        blank=True,
        default='',
        help_text='Comentario del docente sobre el intento, visible para el estudiante.',
    )
    revisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presentaciones_revisadas_saber_pro',
    )
    revisada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'presentaciones_simulacro_saber_pro'
        ordering = ['-iniciada_en', '-id']
        verbose_name = 'Presentación de simulacro Saber Pro'
        verbose_name_plural = 'Presentaciones de simulacro Saber Pro'
        unique_together = [('simulacro', 'estudiante', 'intento')]
        indexes = [
            models.Index(
                fields=['estudiante', 'estado'],
                name='present_estudiante_estado_idx',
            ),
            models.Index(
                fields=['simulacro', 'estado'],
                name='present_simulacro_estado_idx',
            ),
        ]

    def __str__(self):
        return f'{self.estudiante} - {self.simulacro} (intento {self.intento})'

    def esta_en_progreso(self) -> bool:
        return self.estado == 'en_progreso'

    def esta_vencida(self) -> bool:
        """Indica si el intento activo superó su tiempo límite."""
        return self.esta_en_progreso() and timezone.now() >= self.expira_en

    def esta_vencida_por_fecha_limite(self) -> bool:
        """Indica si el simulacro cerró por su fecha límite durante el intento."""
        return self.motivo_finalizacion == 'fecha_limite'

    def tiempo_restante_segundos(self) -> int:
        """Segundos restantes del intento; 0 si ya finalizó o venció."""
        if not self.esta_en_progreso():
            return 0
        restante = (self.expira_en - timezone.now()).total_seconds()
        return max(0, int(restante))

    def esta_revisada(self) -> bool:
        return self.calificacion_docente is not None
