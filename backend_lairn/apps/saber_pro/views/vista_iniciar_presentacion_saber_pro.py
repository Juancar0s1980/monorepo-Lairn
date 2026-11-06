"""
Vista para iniciar o reanudar un simulacro Saber Pro (HU-21.1).

Expone `POST /api/saber-pro/estudiante/simulacros/<simulacro_id>/presentaciones/`
sin cuerpo. Solo el estudiante inscrito en el curso puede iniciar el intento.
Si ya existe una presentación activa se reanuda; si venció, se finaliza con
motivo `tiempo_agotado` y se devuelve el resultado.

La respuesta incluye el bloque actual sin respuestas correctas y el cronómetro
calculado por el servidor.
"""

from django.db import transaction
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers import SerializadorEstadoPresentacion
from apps.saber_pro.services.presentaciones import (
    PresentacionNoDisponibleError,
    crear_presentacion,
    pregunta_actual,
)
from core.permissions.permisos_rol import EsEstudiante


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Iniciar o reanudar un simulacro',
    description=(
        'Inicia un intento nuevo del simulacro o reanuda el intento activo del '
        'estudiante autenticado (HU-21.1). El contenido se congela y el tiempo se '
        'calcula en el servidor. No expone respuestas correctas.'
    ),
    parameters=[
        OpenApiParameter(
            'simulacro_id',
            OpenApiTypes.INT,
            OpenApiParameter.PATH,
            description='ID del simulacro disponible para el estudiante.',
        ),
    ],
    request=None,
    responses={
        200: SerializadorEstadoPresentacion,
        400: OpenApiResponse(description='El simulacro no tiene preguntas asignadas'),
        403: OpenApiResponse(description='Solo los estudiantes pueden acceder'),
        404: OpenApiResponse(description='Simulacro no disponible o curso ajeno'),
    },
)
class VistaIniciarPresentacionSaberPro(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, simulacro_id):
        simulacro = (
            Simulacro.objects.filter(
                id=simulacro_id,
                curso__inscripciones__estudiante=request.user,
            )
            .select_related('curso__area')
            .distinct()
            .first()
        )
        if simulacro is None:
            return Response(
                {'detalle': 'Simulacro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tiene_presentacion_activa = simulacro.presentaciones.filter(
            estudiante=request.user,
            estado='en_progreso',
        ).exists()
        if not tiene_presentacion_activa and (
            not simulacro.activo or not simulacro.curso.activo
        ):
            return Response(
                {'detalle': 'El simulacro no está disponible para presentar.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            with transaction.atomic():
                presentacion = crear_presentacion(simulacro, request.user)
        except PresentacionNoDisponibleError as error:
            return Response(
                {'detalle': error.mensaje},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentacion = (
            PresentacionSimulacro.objects.select_related('simulacro__curso__area')
            .prefetch_related('preguntas')
            .get(pk=presentacion.pk)
        )
        return Response(
            SerializadorEstadoPresentacion(
                presentacion,
                context={'pregunta': pregunta_actual(presentacion)},
            ).data
        )
