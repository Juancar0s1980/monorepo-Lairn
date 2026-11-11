"""
Solicitud de cuenta administrativa (HU-26).

Quien entra por el acceso de personal con Google y elige Administrador, Coordinador o Vicerrector
queda con la cuenta creada pero inactiva hasta que un Administrador la apruebe. El rol pedido se
guarda aquí y solo se asigna al aprobar.
"""

from django.conf import settings
from django.db import models


class OpcionesEstadoCuenta(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    APROBADA = 'aprobada', 'Aprobada'
    RECHAZADA = 'rechazada', 'Rechazada'


class SolicitudCuenta(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solicitud_cuenta')
    rol_solicitado = models.ForeignKey('users.Role', on_delete=models.PROTECT, related_name='solicitudes_cuenta')
    estado = models.CharField(max_length=12, choices=OpcionesEstadoCuenta.choices, default=OpcionesEstadoCuenta.PENDIENTE)
    motivo = models.TextField(blank=True, default='')
    resuelta_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name='+')
    resuelta_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_solicitud_cuenta'
        ordering = ['-creada_en']

    def __str__(self) -> str:
        return f'{self.usuario.email} → {self.rol_solicitado.name} ({self.estado})'
