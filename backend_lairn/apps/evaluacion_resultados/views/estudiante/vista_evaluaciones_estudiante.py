"""
Presentación de evaluaciones formales por el estudiante (HU-07).

- `GET  estudiante/evaluaciones/`                 activas a las que está convocado + las ya presentadas
- `GET  estudiante/evaluaciones/<id>/`            resumen; si hay intento en curso, sus preguntas y respuestas
- `POST estudiante/evaluaciones/<id>/iniciar/`    crea (o retoma) el único intento
- `PUT  estudiante/evaluaciones/<id>/respuestas/` guarda una respuesta al marcarla (HU-07.2)
- `POST estudiante/evaluaciones/<id>/enviar/`     envío manual; vencido = envío automático (HU-07.3)
- `POST estudiante/evaluaciones/<id>/incidentes/` reporta un incidente de integridad (ADR-010)

Supervisión en sala (ADR-009): si la evaluación tiene supervisor, el resumen
trae `requiere_asistencia=True` y `asistencia` (estado o `pendiente`), e
iniciar exige estar marcado presente o tarde (403 si no). Llegar tarde no
reduce la duración: el vencimiento ya queda limitado por `fecha_fin`.

Integridad (ADR-010): el servidor decide advertencia o suspensión. Con el
intento suspendido no se envían las preguntas, guardar y enviar responden 409
y el tiempo queda congelado hasta la decisión del docente.

Nunca se envían al estudiante la respuesta correcta ni la justificación.
Toda consulta cierra primero los intentos vencidos (cierre perezoso).
"""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import IntentoEvaluacion, OpcionesTipoEvaluacion
from apps.evaluacion_resultados.services.servicio_integridad import (
    AVISO_ADVERTENCIA,
    AVISO_SUSPENSION,
    ErrorIntegridad,
    registrar_incidente,
)
from apps.evaluacion_resultados.services.servicio_presentacion import (
    GRACIA_SEGUNDOS,
    asistencia_de,
    calcular_vencimiento,
    cerrar,
    cerrar_si_vencido,
    esta_activa,
    evaluaciones_convocadas,
    preguntas_de,
    puede_iniciar_por_asistencia,
)

MENSAJE_ESPERA_ASISTENCIA = 'Espera a que el docente supervisor registre tu asistencia en sala.'
from core.permissions.permisos_rol import EsEstudiante


def _intento_de(evaluacion, estudiante):
    intento = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, estudiante=estudiante).first()
    return cerrar_si_vencido(intento) if intento else None


def _asistencia(evaluacion, estudiante):
    if not evaluacion.supervisor_id:
        return None
    registro = asistencia_de(evaluacion, estudiante)
    return registro.estado if registro else 'pendiente'


def _resumen(evaluacion, intento, ahora, estudiante):
    return {
        'id': evaluacion.id, 'nombre': evaluacion.nombre, 'instrucciones': evaluacion.instrucciones,
        'tipo': evaluacion.tipo, 'momento': evaluacion.momento.nombre,
        'fecha_inicio': evaluacion.fecha_inicio, 'fecha_fin': evaluacion.fecha_fin,
        'duracion_minutos': evaluacion.duracion_minutos, 'activa': esta_activa(evaluacion, ahora),
        'tarea': {'id': evaluacion.tarea_id, 'titulo': evaluacion.tarea.titulo} if evaluacion.tarea_id else None,
        'total_preguntas': evaluacion.items.count(),
        'requiere_asistencia': bool(evaluacion.supervisor_id),
        'asistencia': _asistencia(evaluacion, estudiante),
        'intento': None if intento is None else {
            'estado': 'enviado' if intento.enviado else 'en_curso',
            'iniciado_en': intento.iniciado_en, 'vence_en': intento.vence_en,
            'enviado_en': intento.enviado_en, 'envio_automatico': intento.envio_automatico,
            'respondidas': len(intento.respuestas),
            'integridad': intento.integridad,
            # Tiempo congelado mientras está suspendido (el temporizador no corre).
            'segundos_restantes': intento.segundos_restantes_al_suspender if intento.suspendido else None,
        },
    }


def _detalle(evaluacion, intento, ahora, estudiante):
    datos = _resumen(evaluacion, intento, ahora, estudiante)
    datos['ahora_servidor'] = ahora  # el reloj del navegador puede estar desfasado
    if intento is not None and not intento.enviado and not intento.suspendido:
        datos['preguntas'] = [
            {'id': p.id, 'contexto': p.contexto, 'enunciado': p.enunciado, 'opciones': p.opciones}
            for p in preguntas_de(evaluacion)
        ]
        datos['respuestas'] = intento.respuestas
    return datos


def _convocada(request, pk):
    return get_object_or_404(evaluaciones_convocadas(request.user), pk=pk)


class VistaMisEvaluaciones(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        ahora = timezone.now()
        lista = []
        for evaluacion in evaluaciones_convocadas(request.user).order_by('fecha_inicio'):
            intento = _intento_de(evaluacion, request.user)
            # HU-07.1: solo las activas; las ya presentadas quedan como constancia.
            if esta_activa(evaluacion, ahora) or intento is not None:
                lista.append(_resumen(evaluacion, intento, ahora, request.user))
        return Response(lista)


class VistaDetalleMiEvaluacion(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, pk):
        evaluacion = _convocada(request, pk)
        return Response(_detalle(evaluacion, _intento_de(evaluacion, request.user), timezone.now(), request.user))


class VistaIniciarEvaluacion(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, pk):
        evaluacion = _convocada(request, pk)
        ahora = timezone.now()
        if evaluacion.tipo != OpcionesTipoEvaluacion.CUESTIONARIO:
            return Response({'detalle': 'Esta evaluación se presenta entregando la tarea asignada.'}, status=400)
        intento = _intento_de(evaluacion, request.user)
        if intento is None:
            if not esta_activa(evaluacion, ahora):
                return Response({'detalle': 'La evaluación no está disponible en este momento.'}, status=400)
            if not puede_iniciar_por_asistencia(evaluacion, request.user):
                return Response({'detalle': MENSAJE_ESPERA_ASISTENCIA}, status=403)
            try:
                with transaction.atomic():
                    intento = IntentoEvaluacion.objects.create(
                        evaluacion=evaluacion, estudiante=request.user,
                        vence_en=calcular_vencimiento(evaluacion, ahora),
                    )
            except IntegrityError:
                # Doble clic: el intento ya se creó en la otra petición.
                intento = _intento_de(evaluacion, request.user)
        return Response(_detalle(evaluacion, intento, ahora, request.user), status=201)


class VistaGuardarRespuesta(APIView):
    permission_classes = [EsEstudiante]

    def put(self, request, pk):
        evaluacion = _convocada(request, pk)
        pregunta_id = request.data.get('pregunta')
        opcion = request.data.get('opcion')
        preguntas = {p.id: p for p in preguntas_de(evaluacion)}
        if not isinstance(pregunta_id, int) or pregunta_id not in preguntas:
            return Response({'pregunta': ['La pregunta no pertenece a esta evaluación.']}, status=400)
        if isinstance(opcion, bool) or not isinstance(opcion, int) or not 0 <= opcion < len(preguntas[pregunta_id].opciones):
            return Response({'opcion': ['Opción no válida.']}, status=400)
        with transaction.atomic():
            # Bloqueo de fila: dos respuestas guardadas casi a la vez no se pisan.
            intento = IntentoEvaluacion.objects.select_for_update().filter(
                evaluacion=evaluacion, estudiante=request.user,
            ).first()
            if intento is None:
                return Response({'detalle': 'Primero inicia la evaluación.'}, status=400)
            if intento.enviado:
                return Response({'detalle': 'La evaluación ya fue enviada.'}, status=409)
            if intento.suspendido:
                return Response({'detalle': AVISO_SUSPENSION}, status=409)
            if (timezone.now() - intento.vence_en).total_seconds() > GRACIA_SEGUNDOS:
                transaction.on_commit(lambda: cerrar_si_vencido(intento))
                return Response({'detalle': 'El tiempo terminó: tus respuestas registradas se enviaron.'}, status=409)
            intento.respuestas[str(pregunta_id)] = opcion
            intento.save(update_fields=['respuestas'])
        return Response({'guardada': True, 'respondidas': len(intento.respuestas)})


class VistaEnviarEvaluacion(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, pk):
        evaluacion = _convocada(request, pk)
        intento = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, estudiante=request.user).first()
        if intento is None:
            return Response({'detalle': 'No has iniciado esta evaluación.'}, status=400)
        ahora = timezone.now()
        if intento.suspendido:
            return Response({'detalle': AVISO_SUSPENSION}, status=409)
        if not intento.enviado:
            # Pasada la hora de vencimiento, el envío es el automático del temporizador
            # (HU-07.3) aunque llegue dentro del margen de red; se registra a la hora de vencimiento.
            vencido = ahora >= intento.vence_en
            intento = cerrar(intento, automatico=vencido, momento=intento.vence_en if vencido else None)
        return Response(_resumen(evaluacion, intento, ahora, request.user))


class VistaReportarIncidente(APIView):
    """El navegador reporta; el servidor decide advertencia o suspensión."""

    permission_classes = [EsEstudiante]

    def post(self, request, pk):
        evaluacion = _convocada(request, pk)
        intento = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, estudiante=request.user).first()
        if intento is None:
            return Response({'detalle': 'No has iniciado esta evaluación.'}, status=400)
        try:
            intento, incidente = registrar_incidente(
                intento, request.data.get('tipo'), request.data.get('detalle', ''),
            )
        except ErrorIntegridad as error:
            return Response({'detalle': error.mensaje}, status=error.status)
        aviso = {
            'advertencia': AVISO_ADVERTENCIA, 'suspension': AVISO_SUSPENSION,
        }.get(incidente.consecuencia)
        if aviso is None and intento.suspendido:
            aviso = AVISO_SUSPENSION
        return Response({
            'consecuencia': incidente.consecuencia, 'integridad': intento.integridad, 'aviso': aviso,
        }, status=201)
