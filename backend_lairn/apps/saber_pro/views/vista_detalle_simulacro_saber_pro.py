"""
Vista de detalle de un simulacro Saber Pro (HU-19.4).

Expone `GET/PUT/PATCH/DELETE` sobre
`/api/saber-pro/docente/cursos/<curso_id>/simulacros/<simulacro_id>/`.

- GET: consulta la configuración, las distribuciones y el total de preguntas
  asignadas. El cuestionario completo (con respuestas correctas) se consulta en
  `.../preguntas/` mediante `VistaPreguntasSimulacroSaberPro`.
- PUT/PATCH: edita metadatos y/o distribución. Si cambia la distribución o la
  cantidad de preguntas, el sistema vuelve a seleccionar contenido aprobado de
  forma aleatoria dentro de la misma transacción.
- DELETE: elimina el simulacro si no tiene presentaciones activas (HU-21).
  Tampoco se puede editar mientras exista un intento en curso, porque la
  regeneración de preguntas invalidaría el examen del estudiante.

Todas las operaciones filtran por `curso__docente=request.user` y por
`curso_id`, así que un simulacro ajeno responde 404.
"""

from django.db import transaction
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.serializers import (
    SerializadorCrearEditarSimulacro,
    SerializadorSimulacro,
)
from apps.saber_pro.services.simulacros import ContenidoInsuficienteError
from apps.saber_pro.views.vista_simulacros_curso_saber_pro import simulacros_del_curso
from core.permissions.permisos_rol import EsDocente


@extend_schema_view(
    get=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Obtener detalle de simulacro',
        description=(
            'Retorna la configuración, distribución y total de preguntas de un '
            'simulacro del docente autenticado (HU-19.4). Las preguntas concretas '
            'se consultan en `.../preguntas/`.'
        ),
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
            OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del simulacro'),
        ],
        responses={
            200: SerializadorSimulacro,
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        },
    ),
    put=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Actualizar simulacro',
        description=(
            'Actualiza la configuración del simulacro. Si se envían distribuciones '
            'distintas o cambia el número de preguntas, se reselecciona el contenido '
            'aprobado de forma aleatoria. En Inglés siempre se mantienen las 7 partes '
            'y el total fijo de 45 preguntas.'
        ),
        request=SerializadorCrearEditarSimulacro,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
            OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del simulacro'),
        ],
        responses={
            200: SerializadorSimulacro,
            400: OpenApiResponse(description='Datos inválidos o banco aprobado insuficiente'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        },
    ),
    patch=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Actualizar simulacro parcialmente',
        description=(
            'Actualiza uno o varios campos del simulacro. Para cambiar el número de '
            'preguntas de un simulacro con distribución hay que enviar también la '
            'nueva distribución.'
        ),
        request=SerializadorCrearEditarSimulacro,
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
            OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del simulacro'),
        ],
        responses={
            200: SerializadorSimulacro,
            400: OpenApiResponse(description='Datos inválidos o banco aprobado insuficiente'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Saber Pro - Docente'],
        summary='Eliminar simulacro',
        description='Elimina un simulacro del curso del docente si no tiene presentaciones activas (HU-19.4).',
        parameters=[
            OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
            OpenApiParameter('simulacro_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del simulacro'),
        ],
        responses={
            204: OpenApiResponse(description='Simulacro eliminado'),
            400: OpenApiResponse(description='El simulacro tiene presentaciones activas'),
            403: OpenApiResponse(description='El curso no le pertenece'),
            404: OpenApiResponse(description='Curso o simulacro no encontrado'),
        },
    ),
)
class VistaDetalleSimulacroSaberPro(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id, simulacro_id):
        simulacro = self._obtener_simulacro(request, curso_id, simulacro_id)
        if isinstance(simulacro, Response):
            return simulacro
        return Response(SerializadorSimulacro(simulacro).data)

    def put(self, request, curso_id, simulacro_id):
        return self._actualizar(request, curso_id, simulacro_id, parcial=False)

    def patch(self, request, curso_id, simulacro_id):
        return self._actualizar(request, curso_id, simulacro_id, parcial=True)

    def delete(self, request, curso_id, simulacro_id):
        simulacro = self._obtener_simulacro(request, curso_id, simulacro_id)
        if isinstance(simulacro, Response):
            return simulacro

        if simulacro.tiene_presentaciones_activas():
            return Response(
                {'detalle': 'El simulacro tiene presentaciones activas y no puede eliminarse.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        simulacro.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _actualizar(self, request, curso_id, simulacro_id, parcial):
        simulacro = self._obtener_simulacro(request, curso_id, simulacro_id)
        if isinstance(simulacro, Response):
            return simulacro

        if simulacro.tiene_presentaciones_activas():
            return Response(
                {
                    'detalle': (
                        'El simulacro tiene presentaciones activas y no puede editarse.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializador = SerializadorCrearEditarSimulacro(
            simulacro,
            data=request.data,
            partial=parcial,
            context={'curso': simulacro.curso},
        )
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                simulacro = serializador.save()
        except ContenidoInsuficienteError as error:
            return Response(
                {'detalle': error.mensaje, 'errores': error.detalles},
                status=status.HTTP_400_BAD_REQUEST,
            )

        simulacro = simulacros_del_curso(simulacro.curso).get(id=simulacro.id)
        return Response(SerializadorSimulacro(simulacro).data)

    def _obtener_simulacro(self, request, curso_id, simulacro_id):
        try:
            return (
                Simulacro.objects.filter(
                    id=simulacro_id,
                    curso_id=curso_id,
                    curso__docente=request.user,
                )
                .select_related('curso__area')
                .prefetch_related(
                    'distribuciones__competencia',
                    'distribuciones__afirmacion',
                    'preguntas_asignadas__contenido',
                )
                .get()
            )
        except Simulacro.DoesNotExist:
            return Response(
                {'detalle': 'Simulacro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
