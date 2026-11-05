"""
Vista de calificaciones de un simulacro Saber Pro para el docente.

Expone `GET /api/saber-pro/docente/cursos/<curso_id>/simulacros/<simulacro_id>/resultados/`.
Solo el docente propietario del curso puede consultar los intentos finalizados
de sus estudiantes.

- Por defecto devuelve un resultado por estudiante: el intento con mayor puntaje
  entre los ya calificados (un intento pendiente de revisión no tapa a uno ya
  calificado).
- Con `?intentos=todos` devuelve todos los intentos finalizados, que es lo que
  usa el panel de revisión para calificar cada intento por separado.
"""

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers.serializador_resultados_simulacro_saber_pro import (
    SerializadorResultadosSimulacro,
)
from apps.saber_pro.services.presentaciones import (
    presentacion_tiene_revision_pendiente,
)
from core.permissions.permisos_rol import EsDocente


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Consultar calificaciones de un simulacro',
    description=(
        'Retorna un resultado por estudiante con su calificación en escala '
        '0.0-5.0 (la del intento calificado más alto), el puntaje interno 0-100 '
        'y un resumen agregado. Con `intentos=todos` retorna todos los intentos '
        'finalizados. Solo el docente propietario del curso puede consultarlo.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
        OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del simulacro'),
        OpenApiParameter(
            'intentos',
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=False,
            description='Use `todos` para listar todos los intentos finalizados.',
        ),
    ],
    responses={
        200: SerializadorResultadosSimulacro,
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso o simulacro no encontrado'),
    },
)
class VistaResultadosSimulacroSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id, simulacro_id):
        simulacro = (
            Simulacro.objects.filter(
                id=simulacro_id,
                curso_id=curso_id,
                curso__docente=request.user,
            )
            .select_related('curso__area')
            .first()
        )
        if simulacro is None:
            return Response(
                {'detalle': 'Simulacro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        intentos = list(
            PresentacionSimulacro.objects.filter(
                simulacro=simulacro,
                estado='finalizada',
            )
            .select_related('estudiante')
            .prefetch_related('preguntas')
            .order_by(
                'estudiante__first_last_name',
                'estudiante__first_name',
                'estudiante_id',
                'intento',
            )
        )

        pendientes_por_estudiante = {}
        for presentacion in intentos:
            if presentacion_tiene_revision_pendiente(presentacion):
                pendientes_por_estudiante[presentacion.estudiante_id] = (
                    pendientes_por_estudiante.get(presentacion.estudiante_id, 0) + 1
                )
        for presentacion in intentos:
            presentacion.intentos_pendientes = pendientes_por_estudiante.get(
                presentacion.estudiante_id,
                0,
            )

        def clave(presentacion):
            # Un intento calificado siempre gana a uno pendiente; luego el
            # mayor puntaje y, en empate, el intento más reciente.
            return (
                not presentacion_tiene_revision_pendiente(presentacion),
                presentacion.puntaje,
                presentacion.intento,
            )

        mejores_por_estudiante = {}
        for presentacion in intentos:
            actual = mejores_por_estudiante.get(presentacion.estudiante_id)
            if actual is None or clave(presentacion) > clave(actual):
                mejores_por_estudiante[presentacion.estudiante_id] = presentacion

        mejores_intentos = sorted(
            mejores_por_estudiante.values(),
            key=lambda presentacion: (
                presentacion.estudiante.first_last_name or '',
                presentacion.estudiante.first_name or '',
                presentacion.estudiante_id,
            ),
        )
        calificaciones = [
            round(presentacion.puntaje / 20, 2)
            for presentacion in mejores_intentos
            if not presentacion_tiene_revision_pendiente(presentacion)
        ]

        mostrar_todos = request.query_params.get('intentos') == 'todos'

        payload = {
            'simulacro_id': simulacro.id,
            'simulacro_titulo': simulacro.titulo,
            'intentos_maximos': simulacro.intentos_maximos,
            'resumen': {
                'total_estudiantes': len(mejores_intentos),
                'total_intentos': len(intentos),
                'promedio_calificacion': (
                    round(sum(calificaciones) / len(calificaciones), 2)
                    if calificaciones
                    else 0
                ),
                'aprobados': sum(1 for calificacion in calificaciones if calificacion >= 3.0),
                'requieren_revision': sum(pendientes_por_estudiante.values()),
            },
            'resultados': intentos if mostrar_todos else mejores_intentos,
        }
        return Response(SerializadorResultadosSimulacro(payload).data)