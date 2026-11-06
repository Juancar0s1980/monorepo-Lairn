"""
Reglas de integridad académica en la presentación (ADR-010).

El navegador solo DETECTA y reporta; el servidor decide:
  - 1.er incidente que cuenta → `advertido` (aviso al estudiante).
  - 2.º incidente (o el primero tras una reactivación) → `suspendido`: el
    tiempo se congela (`segundos_restantes_al_suspender`), no se puede
    responder ni enviar y el cierre automático no aplica.
  - Incidentes a menos de 2 s del anterior se registran como `agrupado`
    (blur + visibilitychange del mismo cambio de pestaña cuentan una vez).
  - Con el intento suspendido, los incidentes se registran `sin_efecto`.
Decide el docente supervisor asignado; si la evaluación no tiene supervisor,
el Coordinador o el Administrador:
  - Reactivar: `vence_en = ahora + segundos restantes` → `reactivado`.
  - Anular por fraude: cierra el intento con nota 0 → `anulado_fraude`.
Los anulados se excluyen del % de acierto y de los promedios, y se cuentan
aparte (ver ADR-010).
"""

import math
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.evaluacion_resultados.models import (
    TIPOS_INFORMATIVOS,
    IncidenteIntento,
    IntentoEvaluacion,
    OpcionesAccionIntegridad,
    OpcionesConsecuencia,
    OpcionesIntegridad,
    OpcionesTipoIncidente,
    ResolucionIntegridad,
)
from apps.evaluacion_resultados.services.servicio_presentacion import cerrar_si_vencido, preguntas_de

VENTANA_AGRUPACION = timedelta(seconds=2)
MAX_MOTIVO = 500
AVISO_ADVERTENCIA = (
    'Se registró un intento de copiar o salir de la evaluación. Si vuelve a ocurrir, tu momento se '
    'suspenderá y el docente decidirá si se reactiva o se anula por fraude.'
)
AVISO_SUSPENSION = 'Evaluación suspendida: espera la decisión del docente.'


class ErrorIntegridad(Exception):
    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _suspender(intento, ahora):
    intento.integridad = OpcionesIntegridad.SUSPENDIDO
    intento.suspendido_en = ahora
    intento.segundos_restantes_al_suspender = max(0, math.ceil((intento.vence_en - ahora).total_seconds()))


def registrar_incidente(intento, tipo, detalle='', ahora=None):
    """Registra el incidente y aplica la consecuencia. Devuelve (intento, incidente)."""
    if tipo not in OpcionesTipoIncidente.values:
        raise ErrorIntegridad('Tipo de incidente no válido.')
    ahora = ahora or timezone.now()
    intento = cerrar_si_vencido(intento, ahora)
    with transaction.atomic():
        intento = IntentoEvaluacion.objects.select_for_update().get(pk=intento.pk)
        if intento.enviado:
            raise ErrorIntegridad('La evaluación ya fue enviada.', 409)
        if tipo in TIPOS_INFORMATIVOS or intento.suspendido:
            consecuencia = OpcionesConsecuencia.SIN_EFECTO
        else:
            ultimo = (intento.incidentes.exclude(tipo__in=TIPOS_INFORMATIVOS)
                      .order_by('-ocurrido_en', '-id').first())
            if ultimo is not None and ahora - ultimo.ocurrido_en < VENTANA_AGRUPACION:
                consecuencia = OpcionesConsecuencia.AGRUPADO
            elif intento.integridad == OpcionesIntegridad.NORMAL:
                consecuencia = OpcionesConsecuencia.ADVERTENCIA
                intento.integridad = OpcionesIntegridad.ADVERTIDO
            else:  # advertido o reactivado
                consecuencia = OpcionesConsecuencia.SUSPENSION
                _suspender(intento, ahora)
            intento.save()
        incidente = IncidenteIntento.objects.create(
            intento=intento, tipo=tipo, consecuencia=consecuencia,
            detalle=str(detalle or '')[:200], ocurrido_en=ahora,
        )
    return intento, incidente


def resolver(intento, accion, motivo, por, ahora=None):
    """Reactiva o anula un intento suspendido. Lanza `ErrorIntegridad`."""
    motivo = (motivo or '').strip()
    if accion not in OpcionesAccionIntegridad.values:
        raise ErrorIntegridad('Acción no válida: usa reactivar o anular.')
    if not motivo:
        raise ErrorIntegridad('El motivo de la decisión es obligatorio.')
    if len(motivo) > MAX_MOTIVO:
        raise ErrorIntegridad(f'El motivo admite máximo {MAX_MOTIVO} caracteres.')
    ahora = ahora or timezone.now()
    with transaction.atomic():
        intento = IntentoEvaluacion.objects.select_for_update().get(pk=intento.pk)
        if not intento.suspendido:
            raise ErrorIntegridad('Solo se puede decidir sobre un intento suspendido.', 409)
        segundos = intento.segundos_restantes_al_suspender or 0
        if accion == OpcionesAccionIntegridad.REACTIVAR:
            # El tiempo estaba congelado: se devuelve completo aunque pase el cierre de la ventana.
            intento.vence_en = ahora + timedelta(seconds=segundos)
            intento.integridad = OpcionesIntegridad.REACTIVADO
        else:
            intento.integridad = OpcionesIntegridad.ANULADO_FRAUDE
            intento.total = len(preguntas_de(intento.evaluacion))
            intento.aciertos = 0
            intento.nota = 0
            intento.envio_automatico = False
            intento.enviado_en = ahora
        intento.resuelto_por = por
        intento.resuelto_en = ahora
        intento.motivo_resolucion = motivo
        intento.save()
        ResolucionIntegridad.objects.create(
            intento=intento, accion=accion, motivo=motivo, resuelto_por=por, segundos_restantes=segundos,
        )
    return intento


def datos_integridad(intento) -> dict:
    """Integridad de un intento para seguimiento/supervisión (usa prefetch de incidentes y resoluciones)."""
    from apps.evaluacion_resultados.services.servicio_supervision import nombre_completo

    incidentes = list(intento.incidentes.all())
    return {
        'estado': intento.integridad,
        'suspendido_en': intento.suspendido_en,
        'segundos_restantes': intento.segundos_restantes_al_suspender if intento.suspendido else None,
        'incidentes_contados': sum(
            1 for i in incidentes if i.consecuencia in (OpcionesConsecuencia.ADVERTENCIA, OpcionesConsecuencia.SUSPENSION)
        ),
        'incidentes': [
            {'tipo': i.tipo, 'consecuencia': i.consecuencia, 'ocurrido_en': i.ocurrido_en, 'detalle': i.detalle}
            for i in incidentes
        ],
        'resoluciones': [
            {'accion': r.accion, 'motivo': r.motivo, 'resuelto_en': r.resuelto_en,
             'resuelto_por': nombre_completo(r.resuelto_por) if r.resuelto_por else None}
            for r in intento.resoluciones.all()
        ],
    }
