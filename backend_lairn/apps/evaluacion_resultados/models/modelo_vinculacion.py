"""
Solicitud de vinculación de un curso del docente a una asignatura de la malla (HU-01.10).

El docente crea su curso (examenes.Curso) y pide que lo vinculen a una asignatura oficial
(AsignaturaMalla). Solo el Administrador o el Coordinador aprueban: al aprobar, la asignatura
queda con `curso_vinculado = curso` y el docente pasa a ser su docente en la malla.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q


class OpcionesEstadoSolicitud(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    APROBADA = 'aprobada', 'Aprobada'
    RECHAZADA = 'rechazada', 'Rechazada'
    CANCELADA = 'cancelada', 'Cancelada por el docente'


class SolicitudVinculacion(models.Model):
    curso = models.ForeignKey('examenes.Curso', on_delete=models.CASCADE, related_name='solicitudes_vinculacion')
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    asignatura = models.ForeignKey('AsignaturaMalla', on_delete=models.CASCADE, related_name='solicitudes_vinculacion')
    mensaje = models.TextField(blank=True, default='', help_text='Mensaje del docente para quien aprueba.')
    estado = models.CharField(max_length=20, choices=OpcionesEstadoSolicitud.choices,
                              default=OpcionesEstadoSolicitud.PENDIENTE, db_index=True)
    respuesta = models.TextField(blank=True, default='', help_text='Motivo del rechazo o nota de aprobación.')
    reemplazo_curso = models.CharField(max_length=150, blank=True, default='',
                                       help_text='Curso que estaba vinculado y fue reemplazado al aprobar (trazabilidad).')
    resuelta_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    resuelta_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ev_solicitudes_vinculacion'
        ordering = ['-creada_en']
        constraints = [
            # Una sola solicitud pendiente por curso y asignatura (evita duplicados por doble clic).
            models.UniqueConstraint(fields=['curso', 'asignatura'], condition=Q(estado='pendiente'),
                                    name='uq_ev_solicitud_pendiente_curso_asignatura'),
        ]

    def __str__(self) -> str:
        return f'{self.curso_id} → {self.asignatura_id} ({self.estado})'
