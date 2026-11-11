"""
Identidad de Google vinculada a una cuenta (HU-26).

`sub` es el identificador único y permanente que Google asigna a cada cuenta. Se guarda en el
primer ingreso: si más adelante llega el mismo correo con otro `sub` (por ejemplo, un correo
institucional reasignado a otra persona), el ingreso se rechaza.
"""

from django.conf import settings
from django.db import models


class IdentidadGoogle(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='identidad_google')
    sub = models.CharField(max_length=64, unique=True)
    dominio = models.CharField(max_length=120, blank=True, default='')
    vinculada_en = models.DateTimeField(auto_now_add=True)
    ultimo_ingreso = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users_identidad_google'

    def __str__(self) -> str:
        return f'{self.usuario_id} · {self.sub}'
