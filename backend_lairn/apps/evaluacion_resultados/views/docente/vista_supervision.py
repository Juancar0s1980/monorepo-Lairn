"""
Llamado a lista del docente supervisor en sala (ADR-009).

- `GET supervision/`                         evaluaciones publicadas que supervisa (abiertas o cerradas hace < 1 día)
- `GET supervision/<id>/`                    convocados con asistencia y progreso del intento (sin nota)
- `PUT supervision/<id>/asistencia/`         {estudiante, estado, tipo_excusa?, observacion?}
- `PUT supervision/<id>/asistencia/masiva/`  {estudiantes: [ids], estado: 'presente'}
- `POST supervision/<id>/intentos/<estudiante>/resolver/` {accion: reactivar|anular, motivo} (ADR-010)

Solo el docente asignado como supervisor ve la evaluación (otro docente: 404).
Solo `presente` y `tarde` habilitan al estudiante para iniciar el intento.
"""

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    ESTADOS_HABILITAN,
    EvaluacionFormal,
    IntentoEvaluacion,
    OpcionesEstadoEvaluacion,
)
from apps.evaluacion_resultados.services.servicio_integridad import ErrorIntegridad, resolver
from apps.evaluacion_resultados.services.servicio_presentacion import origenes_convocatoria
from apps.evaluacion_resultados.services.servicio_supervision import (
    ErrorSupervision,
    registrar_asistencia,
    resumen_evaluacion,
    seguimiento,
    validar_ventana_llamado,
)
from core.permissions.permisos_rol import EsDocente

MAX_MASIVA = 2000


def _supervisadas(usuario):
    return EvaluacionFormal.objects.filter(
        supervisor=usuario, estado=OpcionesEstadoEvaluacion.PUBLICADA,
    ).select_related('momento__programa', 'supervisor')


def _mia(request, pk):
    return get_object_or_404(_supervisadas(request.user), pk=pk)


class VistaMisSupervisiones(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        limite = timezone.now() - timedelta(days=1)
        lista = []
        for evaluacion in _supervisadas(request.user).filter(fecha_fin__gte=limite).order_by('fecha_inicio'):
            datos = resumen_evaluacion(evaluacion)
            datos['conteos'] = seguimiento(evaluacion, con_nota=False)['conteos']
            lista.append(datos)
        return Response(lista)


class VistaLlamadoLista(APIView):
    permission_classes = [EsDocente]

    def get(self, request, pk):
        return Response(seguimiento(_mia(request, pk), con_nota=False))


class VistaRegistrarAsistencia(APIView):
    permission_classes = [EsDocente]

    def put(self, request, pk):
        evaluacion = _mia(request, pk)
        try:
            registro = registrar_asistencia(
                evaluacion, request.data.get('estudiante'), request.data.get('estado'),
                tipo_excusa=request.data.get('tipo_excusa') or '',
                observacion=request.data.get('observacion') or '', por=request.user,
            )
        except ErrorSupervision as error:
            return Response({'detalle': error.mensaje}, status=error.status)
        return Response({
            'estudiante': registro.estudiante_id, 'estado': registro.estado,
            'tipo_excusa': registro.tipo_excusa or None, 'observacion': registro.observacion,
            'llegada_en': registro.llegada_en, 'actualizado_en': registro.actualizado_en,
        })


class VistaAsistenciaMasiva(APIView):
    """Marca a varios convocados con un estado que habilita (por defecto, presente)."""

    permission_classes = [EsDocente]

    def put(self, request, pk):
        evaluacion = _mia(request, pk)
        estado = request.data.get('estado', 'presente')
        ids = request.data.get('estudiantes')
        if estado not in ESTADOS_HABILITAN:
            return Response({'detalle': 'El marcado masivo solo admite presente o tarde.'}, status=400)
        if not isinstance(ids, list) or not ids or len(ids) > MAX_MASIVA:
            return Response({'detalle': 'Envía la lista de estudiantes a marcar.'}, status=400)
        ahora = timezone.now()
        try:
            validar_ventana_llamado(evaluacion, ahora)
            convocados = origenes_convocatoria(evaluacion)
            with transaction.atomic():
                for estudiante_id in dict.fromkeys(ids):
                    registrar_asistencia(evaluacion, estudiante_id, estado, por=request.user,
                                         ahora=ahora, convocados=convocados)
        except ErrorSupervision as error:
            return Response({'detalle': error.mensaje}, status=error.status)
        return Response({'marcados': len(set(ids)), 'estado': estado})


def _respuesta_resolucion(evaluacion, estudiante_id, request):
    """Resuelve (reactivar | anular) el intento suspendido de un estudiante de la evaluación."""
    intento = get_object_or_404(IntentoEvaluacion, evaluacion=evaluacion, estudiante_id=estudiante_id)
    try:
        intento = resolver(intento, request.data.get('accion'), request.data.get('motivo'), request.user)
    except ErrorIntegridad as error:
        return Response({'detalle': error.mensaje}, status=error.status)
    return Response({
        'estudiante': intento.estudiante_id, 'integridad': intento.integridad, 'vence_en': intento.vence_en,
        'resuelto_en': intento.resuelto_en, 'motivo': intento.motivo_resolucion,
    })


class VistaResolverIntegridadSupervisor(APIView):
    """El docente supervisor asignado decide sobre un intento suspendido."""

    permission_classes = [EsDocente]

    def post(self, request, pk, estudiante_id):
        return _respuesta_resolucion(_mia(request, pk), estudiante_id, request)
