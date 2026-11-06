"""
Integridad académica en la presentación de la evaluación formal (ADR-010).

- `IncidenteIntento`: cada evento sospechoso que el navegador reporta durante
  un intento en curso (copiar, cortar, pegar, menú contextual, cambio de
  pestaña o ventana, salida de pantalla completa). El servidor decide su
  `consecuencia`: advertencia (1.º), suspensión (2.º, o el primero tras una
  reactivación), agrupado (duplicado en < 2 s, no cuenta) o sin efecto
  (informativo o con el intento ya suspendido).
- `ResolucionIntegridad`: decisión del docente supervisor (o del gestor si no
  hay supervisor) sobre un intento suspendido: reactivar o anular por fraude,
  con motivo obligatorio.

Ninguno de los dos se borra: son la trazabilidad del proceso.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class OpcionesTipoIncidente(models.TextChoices):
    COPIAR = 'copiar', 'Copiar'
    CORTAR = 'cortar', 'Cortar'
    PEGAR = 'pegar', 'Pegar'
    MENU_CONTEXTUAL = 'menu_contextual', 'Menú contextual'
    CAMBIO_PESTANA = 'cambio_pestana', 'Cambio de pestaña o ventana'
    SALIR_PANTALLA_COMPLETA = 'salir_pantalla_completa', 'Salida de pantalla completa'
    # Informativo: el navegador no permitió pantalla completa. No cuenta como fraude.
    PANTALLA_COMPLETA_NO_DISPONIBLE = 'pantalla_completa_no_disponible', 'Pantalla completa no disponible'


class OpcionesConsecuencia(models.TextChoices):
    ADVERTENCIA = 'advertencia', 'Advertencia'
    SUSPENSION = 'suspension', 'Suspensión'
    AGRUPADO = 'agrupado', 'Agrupado (duplicado)'
    SIN_EFECTO = 'sin_efecto', 'Sin efecto'


class OpcionesAccionIntegridad(models.TextChoices):
    REACTIVAR = 'reactivar', 'Reactivar'
    ANULAR = 'anular', 'Anular por fraude'


TIPOS_INFORMATIVOS = {OpcionesTipoIncidente.PANTALLA_COMPLETA_NO_DISPONIBLE}


class IncidenteIntento(models.Model):
    intento = models.ForeignKey('IntentoEvaluacion', on_delete=models.PROTECT, related_name='incidentes')
    tipo = models.CharField(max_length=40, choices=OpcionesTipoIncidente.choices)
    consecuencia = models.CharField(max_length=20, choices=OpcionesConsecuencia.choices)
    ocurrido_en = models.DateTimeField(default=timezone.now, db_index=True)
    detalle = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'ev_incidentes_intento'
        ordering = ['ocurrido_en', 'id']


class ResolucionIntegridad(models.Model):
    intento = models.ForeignKey('IntentoEvaluacion', on_delete=models.PROTECT, related_name='resoluciones')
    accion = models.CharField(max_length=20, choices=OpcionesAccionIntegridad.choices)
    motivo = models.CharField(max_length=500)
    resuelto_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    resuelto_en = models.DateTimeField(auto_now_add=True)
    segundos_restantes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'ev_resoluciones_integridad'
        ordering = ['resuelto_en', 'id']
