"""
Servicio de desbloqueo remoto de simulacros Saber Pro.

Centraliza el bloqueo del intento cuando el estudiante cambia de pestaña, sale
de pantalla completa o pierde el foco, y la decisión posterior del docente dueño
del curso: aprobar (reanudar el intento) o rechazar (enviarlo automáticamente).

El bloqueo no finaliza el intento: conserva el avance y el cronómetro para que
el estudiante continúe exactamente donde iba cuando el docente lo desbloquee.
Un rechazo sí finaliza el intento, pero nunca afecta a los demás intentos del
estudiante sobre el mismo simulacro.
"""

from django.utils import timezone

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.solicitud_desbloqueo_simulacro import (
    SolicitudDesbloqueoSimulacro,
)
from apps.saber_pro.services.presentaciones import (
    MOTIVO_ANULADO,
    MOTIVO_RECHAZADO,
    finalizar_presentacion,
    finalizar_si_vencida,
)


class DesbloqueoInvalidoError(Exception):
    """La solicitud ya fue atendida o el intento ya no puede desbloquearse."""

    def __init__(self, mensaje):
        self.mensaje = mensaje
        super().__init__(mensaje)


def solicitar_desbloqueo(
    presentacion: PresentacionSimulacro,
    motivo: str,
) -> SolicitudDesbloqueoSimulacro:
    """Bloquea el intento y reutiliza la solicitud pendiente si ya existe."""
    if not presentacion.esta_en_progreso():
        raise DesbloqueoInvalidoError('La presentación ya fue finalizada.')

    solicitud = (
        SolicitudDesbloqueoSimulacro.objects.filter(
            presentacion=presentacion,
            estado='pendiente',
        )
        .order_by('creada_en', 'id')
        .first()
    )
    if solicitud is None:
        solicitud = SolicitudDesbloqueoSimulacro.objects.create(
            presentacion=presentacion,
            motivo=motivo,
        )

    if not presentacion.bloqueada:
        presentacion.bloqueada = True
        presentacion.save(update_fields=['bloqueada', 'actualizado_en'])

    return solicitud


def aprobar_solicitud(
    solicitud: SolicitudDesbloqueoSimulacro,
    docente,
) -> SolicitudDesbloqueoSimulacro:
    """Desbloquea el intento y marca la solicitud como aprobada."""
    if solicitud.estado != 'pendiente':
        raise DesbloqueoInvalidoError('La solicitud ya fue atendida.')

    presentacion = (
        PresentacionSimulacro.objects.select_for_update()
        .select_related('simulacro')
        .get(pk=solicitud.presentacion_id)
    )

    if not presentacion.esta_en_progreso():
        solicitud.estado = 'cancelada'
        solicitud.atendida_en = timezone.now()
        solicitud.atendida_por = docente
        solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])
        raise DesbloqueoInvalidoError(
            'El intento ya finalizó y no requiere desbloqueo.'
        )

    if finalizar_si_vencida(presentacion):
        raise DesbloqueoInvalidoError(
            'El tiempo del intento se agotó y fue finalizado automáticamente.'
        )

    presentacion.bloqueada = False
    presentacion.save(update_fields=['bloqueada', 'actualizado_en'])

    solicitud.estado = 'aprobada'
    solicitud.atendida_en = timezone.now()
    solicitud.atendida_por = docente
    solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])
    return solicitud


def rechazar_solicitud(
    solicitud: SolicitudDesbloqueoSimulacro,
    docente,
) -> SolicitudDesbloqueoSimulacro:
    """Rechaza el desbloqueo y finaliza ese intento para enviarlo automáticamente.

    Solo afecta a la presentación de la solicitud: los demás intentos del
    estudiante sobre el mismo simulacro no se modifican.
    """
    if solicitud.estado != 'pendiente':
        raise DesbloqueoInvalidoError('La solicitud ya fue atendida.')

    presentacion = (
        PresentacionSimulacro.objects.select_for_update()
        .select_related('simulacro')
        .get(pk=solicitud.presentacion_id)
    )

    if not presentacion.esta_en_progreso():
        solicitud.estado = 'cancelada'
        solicitud.atendida_en = timezone.now()
        solicitud.atendida_por = docente
        solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])
        raise DesbloqueoInvalidoError(
            'El intento ya finalizó y no requiere desbloqueo.'
        )

    if finalizar_si_vencida(presentacion):
        raise DesbloqueoInvalidoError(
            'El tiempo del intento se agotó y fue finalizado automáticamente.'
        )

    # Marcar el rechazo antes de finalizar evita que la finalización cancele la
    # propia solicitud como si siguiera pendiente.
    solicitud.estado = 'rechazada'
    solicitud.atendida_en = timezone.now()
    solicitud.atendida_por = docente
    solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])

    finalizar_presentacion(presentacion, MOTIVO_RECHAZADO)
    return solicitud


def rechazar_y_anular_solicitud(
    solicitud: SolicitudDesbloqueoSimulacro,
    docente,
) -> SolicitudDesbloqueoSimulacro:
    """Rechaza el desbloqueo, anula el intento y bloquea nuevos intentos.

    A diferencia del rechazo normal, el intento queda marcado como anulado: su
    calificación es 0 sin importar el avance ni las respuestas, no pasa a
    revisión docente y el estudiante no puede iniciar otro intento de ese
    simulacro aunque le quedaran intentos disponibles.
    """
    if solicitud.estado != 'pendiente':
        raise DesbloqueoInvalidoError('La solicitud ya fue atendida.')

    presentacion = (
        PresentacionSimulacro.objects.select_for_update()
        .select_related('simulacro')
        .get(pk=solicitud.presentacion_id)
    )

    if not presentacion.esta_en_progreso():
        solicitud.estado = 'cancelada'
        solicitud.atendida_en = timezone.now()
        solicitud.atendida_por = docente
        solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])
        raise DesbloqueoInvalidoError(
            'El intento ya finalizó y no requiere desbloqueo.'
        )

    if finalizar_si_vencida(presentacion):
        raise DesbloqueoInvalidoError(
            'El tiempo del intento se agotó y fue finalizado automáticamente.'
        )

    # La anulación se marca antes de finalizar para que `_calcular_puntaje`
    # fuerce 0 y para que la finalización no deje la revisión abierta.
    presentacion.anulada = True
    presentacion.calificacion_docente = 0
    presentacion.requiere_revision = False
    presentacion.save(
        update_fields=[
            'anulada',
            'calificacion_docente',
            'requiere_revision',
            'actualizado_en',
        ]
    )

    solicitud.estado = 'rechazada'
    solicitud.atendida_en = timezone.now()
    solicitud.atendida_por = docente
    solicitud.save(update_fields=['estado', 'atendida_en', 'atendida_por'])

    finalizar_presentacion(presentacion, MOTIVO_ANULADO)
    return solicitud
