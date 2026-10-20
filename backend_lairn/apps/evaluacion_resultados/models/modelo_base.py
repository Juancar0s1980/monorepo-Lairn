"""
Modelos base trazables de la app `evaluacion_resultados`.

Todo registro académico soporta triple vía de carga:
  manual | documento_ia | api_nova | seed

Y trazabilidad total hacia futuras integraciones:
  - `origen`: de dónde vino el dato.
  - `external_id`: id estable en NOVA/Campus (para `upsert` idempotente,
    nunca duplica aunque se sincronice 10 veces).
  - `datos_origen`: JSON crudo recibido (auditoría / re-mapeo futuro).
  - `version` + `activo` + `reemplazado_por`: HU-01.8, nunca se borra
    físicamente lo que ya se usó en una evaluación finalizada.
"""

from django.db import models


class OpcionesOrigen(models.TextChoices):
    MANUAL = 'manual', 'Carga manual'
    DOCUMENTO_IA = 'documento_ia', 'Documento + IA'
    API_NOVA = 'api_nova', 'API institucional NOVA'
    SEMILLA = 'semilla', 'Datos de prueba'


class OpcionesEstadoRevision(models.TextChoices):
    BORRADOR_IA = 'borrador_ia', 'Borrador de IA'
    PENDIENTE = 'pendiente', 'Pendiente de validación'
    APROBADO = 'aprobado', 'Aprobado'
    DESCARTADO = 'descartado', 'Descartado'
    INACTIVO = 'inactivo', 'Inactivo (histórico)'


class ModeloTrazable(models.Model):
    """Clase abstracta: auditoría mínima común a todo el módulo."""

    origen = models.CharField(
        max_length=20, choices=OpcionesOrigen.choices, default=OpcionesOrigen.MANUAL,
        help_text='Vía por la que ingresó el dato.',
    )
    external_id = models.CharField(
        max_length=100, null=True, blank=True, db_index=True,
        help_text='Id estable en el sistema institucional (NOVA/Campus). Null = aún no sincronizado.',
    )
    datos_origen = models.JSONField(
        default=dict, blank=True,
        help_text='JSON crudo recibido (API o propuesta IA) para auditoría y re-mapeo futuro.',
    )
    estado_revision = models.CharField(
        max_length=20, choices=OpcionesEstadoRevision.choices,
        default=OpcionesEstadoRevision.APROBADO,
        help_text='Borradores IA quedan en borrador_ia/pendiente hasta aprobación humana.',
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text='Se incrementa en cada edición que genera histórico (HU-01.8).',
    )
    activo = models.BooleanField(
        default=True, db_index=True,
        help_text='False = desactivado lógicamente, se conserva por histórico.',
    )
    creado_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
