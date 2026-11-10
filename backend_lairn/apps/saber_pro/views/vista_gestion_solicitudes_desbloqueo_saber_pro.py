"""
Vistas de gestión de solicitudes de desbloqueo para el docente Saber Pro.

- `GET /api/saber-pro/docente/solicitudes-desbloqueo/` lista las solicitudes
  pendientes de los cursos del docente autenticado.
- `POST /api/saber-pro/docente/solicitudes-desbloqueo/<solicitud_id>/aprobar/`
  desbloquea el intento del estudiante.
- `POST /api/saber-pro/docente/solicitudes-desbloqueo/<solicitud_id>/rechazar/`
  finaliza y envía automáticamente ese intento, sin afectar a los demás.
- `POST /api/saber-pro/docente/solicitudes-desbloqueo/<solicitud_id>/rechazar-anular/`
  rechaza el desbloqueo, anula el intento con nota 0 y bloquea nuevos intentos
  del estudiante sobre el mismo simulacro.

Las solicitudes se muestran como notificaciones en la sesión del docente. Antes
de listar, se finalizan de forma perezosa los intentos cuyo tiempo ya venció para
que no queden solicitudes imposibles de atender.
"""

from django.db import transaction
from django.utils import timezone
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.solicitud_desbloqueo_simulacro import (
    SolicitudDesbloqueoSimulacro,
)
from apps.saber_pro.serializers import (
    SerializadorListaSolicitudesDesbloqueo,
    SerializadorSolicitudDesbloqueoDocente,
)
from apps.saber_pro.services.desbloqueos import (
    DesbloqueoInvalidoError,
    aprobar_solicitud,
    rechazar_solicitud,
    rechazar_y_anular_solicitud,
)
from apps.saber_pro.services.presentaciones import finalizar_si_vencida
from core.permissions.permisos_rol import EsDocente


def _finalizar_intentos_vencidos(docente) -> None:
    """Cierra intentos vencidos que aún tengan una solicitud pendiente."""
    vencidas = (
        PresentacionSimulacro.objects.filter(
            estado='en_progreso',
            expira_en__lte=timezone.now(),
            simulacro__curso__docente=docente,
            solicitudes_desbloqueo__estado='pendiente',
        )
        .select_related('simulacro')
        .distinct()
    )
    for presentacion in vencidas:
        finalizar_si_vencida(presentacion)


def _solicitudes_pendientes(docente):
    return (
        SolicitudDesbloqueoSimulacro.objects.filter(
            estado='pendiente',
            presentacion__estado='en_progreso',
            presentacion__simulacro__curso__docente=docente,
        )
        .select_related(
            'presentacion__estudiante',
            'presentacion__simulacro__curso__area',
        )
        .order_by('creada_en', 'id')
    )


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Listar solicitudes de desbloqueo pendientes',
    description=(
        'Retorna las solicitudes de desbloqueo pendientes de los cursos del docente '
        'autenticado, ordenadas de la más antigua a la más reciente. El frontend las '
        'consulta periódicamente para mostrarlas como notificaciones.'
    ),
    responses={
        200: SerializadorListaSolicitudesDesbloqueo,
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
    },
)
class VistaSolicitudesDesbloqueoSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        _finalizar_intentos_vencidos(request.user)
        solicitudes = list(_solicitudes_pendientes(request.user))
        payload = {'total': len(solicitudes), 'solicitudes': solicitudes}
        return Response(SerializadorListaSolicitudesDesbloqueo(payload).data)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Aprobar una solicitud de desbloqueo',
    description=(
        'Desbloquea el intento del estudiante para que continúe donde iba. Solo el '
        'docente dueño del curso puede aprobar la solicitud.'
    ),
    parameters=[
        OpenApiParameter(
            'solicitud_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la solicitud de desbloqueo.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorSolicitudDesbloqueoDocente,
        400: OpenApiResponse(description='La solicitud ya fue atendida o el intento finalizó'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Solicitud no encontrada'),
    },
)
class VistaAprobarSolicitudDesbloqueoSaberPro(APIView):
    permission_classes = [EsDocente]

    def post(self, request, solicitud_id):
        with transaction.atomic():
            solicitud = (
                SolicitudDesbloqueoSimulacro.objects.select_for_update()
                .filter(
                    id=solicitud_id,
                    presentacion__simulacro__curso__docente=request.user,
                )
                .first()
            )
            if solicitud is None:
                return Response(
                    {'detalle': 'Solicitud de desbloqueo no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                aprobar_solicitud(solicitud, request.user)
            except DesbloqueoInvalidoError as error:
                return Response(
                    {'detalle': error.mensaje},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        solicitud = (
            SolicitudDesbloqueoSimulacro.objects.select_related(
                'presentacion__estudiante',
                'presentacion__simulacro__curso__area',
            )
            .get(pk=solicitud.pk)
        )
        return Response(SerializadorSolicitudDesbloqueoDocente(solicitud).data)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Rechazar y anular una solicitud de desbloqueo',
    description=(
        'Rechaza el desbloqueo, anula el intento del estudiante con calificación 0 sin '
        'importar su avance ni sus respuestas, y bloquea nuevos intentos de ese '
        'simulacro para el estudiante. Solo el docente dueño del curso puede anular '
        'la solicitud.'
    ),
    parameters=[
        OpenApiParameter(
            'solicitud_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la solicitud de desbloqueo.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorSolicitudDesbloqueoDocente,
        400: OpenApiResponse(description='La solicitud ya fue atendida o el intento finalizó'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Solicitud no encontrada'),
    },
)
class VistaRechazarYAnularSolicitudDesbloqueoSaberPro(APIView):
    permission_classes = [EsDocente]

    def post(self, request, solicitud_id):
        with transaction.atomic():
            solicitud = (
                SolicitudDesbloqueoSimulacro.objects.select_for_update()
                .filter(
                    id=solicitud_id,
                    presentacion__simulacro__curso__docente=request.user,
                )
                .first()
            )
            if solicitud is None:
                return Response(
                    {'detalle': 'Solicitud de desbloqueo no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                rechazar_y_anular_solicitud(solicitud, request.user)
            except DesbloqueoInvalidoError as error:
                return Response(
                    {'detalle': error.mensaje},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        solicitud = (
            SolicitudDesbloqueoSimulacro.objects.select_related(
                'presentacion__estudiante',
                'presentacion__simulacro__curso__area',
            )
            .get(pk=solicitud.pk)
        )
        return Response(SerializadorSolicitudDesbloqueoDocente(solicitud).data)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Rechazar una solicitud de desbloqueo',
    description=(
        'Rechaza el desbloqueo y finaliza el intento del estudiante para enviar sus '
        'respuestas automáticamente. Solo se cierra esa presentación: los demás '
        'intentos del estudiante sobre el mismo simulacro no se modifican. Solo el '
        'docente dueño del curso puede rechazar la solicitud.'
    ),
    parameters=[
        OpenApiParameter(
            'solicitud_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID de la solicitud de desbloqueo.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorSolicitudDesbloqueoDocente,
        400: OpenApiResponse(description='La solicitud ya fue atendida o el intento finalizó'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Solicitud no encontrada'),
    },
)
class VistaRechazarSolicitudDesbloqueoSaberPro(APIView):
    permission_classes = [EsDocente]

    def post(self, request, solicitud_id):
        with transaction.atomic():
            solicitud = (
                SolicitudDesbloqueoSimulacro.objects.select_for_update()
                .filter(
                    id=solicitud_id,
                    presentacion__simulacro__curso__docente=request.user,
                )
                .first()
            )
            if solicitud is None:
                return Response(
                    {'detalle': 'Solicitud de desbloqueo no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                rechazar_solicitud(solicitud, request.user)
            except DesbloqueoInvalidoError as error:
                return Response(
                    {'detalle': error.mensaje},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        solicitud = (
            SolicitudDesbloqueoSimulacro.objects.select_related(
                'presentacion__estudiante',
                'presentacion__simulacro__curso__area',
            )
            .get(pk=solicitud.pk)
        )
        return Response(SerializadorSolicitudDesbloqueoDocente(solicitud).data)
