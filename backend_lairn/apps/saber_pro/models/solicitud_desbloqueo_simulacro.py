"""
Modelo de dominio `SolicitudDesbloqueoSimulacro`.

Cuando el estudiante cambia de pestaña, sale de pantalla completa o pierde el
foco durante un simulacro, el intento no se cierra: se bloquea y se crea una
solicitud de desbloqueo. El docente dueño del curso la recibe como notificación
y decide remotamente si reanuda el intento (aprobar) o lo envía automáticamente
(rechazar).

Reglas de negocio:

- Solo puede existir una solicitud `pendiente` por presentación. Si el
  estudiante vuelve a salir mientras espera, se reutiliza la misma solicitud.
- Aprobar la solicitud desbloquea la presentación para que el estudiante
  continúe donde iba; no altera respuestas ni el cronómetro.
- Rechazar la solicitud finaliza esa presentación y la envía automáticamente;
  los demás intentos del estudiante sobre el mismo simulacro no se modifican.
- Al finalizar el intento (por salida, tiempo, fecha límite, completado o
  desbloqueo rechazado), las solicitudes pendientes se cancelan para que dejen
  de aparecer al docente.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

ESTADO_SOLICITUD_DESBLOQUEO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
    ('cancelada', 'Cancelada'),
]

MOTIVO_SOLICITUD_DESBLOQUEO_CHOICES = [
    ('cambio_pestana', 'Cambio de pestaña'),
    ('pantalla_completa', 'Salida de pantalla completa'),
    ('perdida_foco', 'Pérdida de foco'),
]


class SolicitudDesbloqueoSimulacro(models.Model):
    presentacion = models.ForeignKey(
        'PresentacionSimulacro',
        on_delete=models.CASCADE,
        related_name='solicitudes_desbloqueo',
    )
    motivo = models.CharField(
        max_length=30,
        choices=MOTIVO_SOLICITUD_DESBLOQUEO_CHOICES,
        default='cambio_pestana',
        help_text='Evento de seguridad que bloqueó el intento.',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD_DESBLOQUEO_CHOICES,
        default='pendiente',
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    atendida_en = models.DateTimeField(null=True, blank=True)
    atendida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_desbloqueo_atendidas',
    )

    class Meta:
        db_table = 'solicitudes_desbloqueo_saber_pro'
        ordering = ['creada_en', 'id']
        verbose_name = 'Solicitud de desbloqueo Saber Pro'
        verbose_name_plural = 'Solicitudes de desbloqueo Saber Pro'
        constraints = [
            models.UniqueConstraint(
                fields=['presentacion'],
                condition=Q(estado='pendiente'),
                name='solicitud_desbloqueo_pendiente_unica',
            ),
        ]
        indexes = [
            models.Index(
                fields=['estado', 'creada_en'],
                name='solicitud_desbloq_estado_idx',
            ),
        ]

    def __str__(self):
        return f'{self.presentacion} - {self.get_estado_display()}'
