"""
Vista de detalle de un examen para el rol Docente.

Expone el endpoint `/examenes/<examen_id>/` con cuatro operaciones sobre un
examen específico:
- GET: retrieve.
- PUT: update completo.
- PATCH: update parcial.
- DELETE: eliminación.

Todas las operaciones aplican el filtro `curso__docente=request.user` al
recuperar el examen, lo que combina existencia y propiedad en una sola query:
si el examen no existe o pertenece al curso de otro docente, la respuesta es
404 en lugar de 403 (evita revelar la existencia de exámenes ajenos).

Las mutaciones (PUT/PATCH) delegan el chequeo de "examen en curso" al
validador de `SerializadorCrearExamen`, que devuelve 400 si existe alguna
`SesionExamen` con `estado='en_progreso'`. El DELETE no atraviesa serializer,
así que replica el mismo chequeo explícitamente y responde 409 Conflict
cuando hay sesiones activas, para mantener una semántica HTTP coherente
con "no es un error de payload sino un conflicto de estado".
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Examen
from apps.examenes.serializers import SerializadorCrearExamen
from apps.motor_adaptativo.models import SesionExamen


@extend_schema_view(
    get=extend_schema(
        tags=['Exámenes'],
        summary='Obtener detalle de examen',
        description='Retorna la información detallada de un examen específico perteneciente a un curso del docente autenticado.',
        parameters=[
            OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del examen'),
        ],
        responses={
            200: SerializadorCrearExamen,
            403: OpenApiResponse(description='El examen no pertenece a un curso del docente'),
            404: OpenApiResponse(description='Examen no encontrado'),
        },
    ),
    put=extend_schema(
        tags=['Exámenes'],
        summary='Actualizar examen',
        description=(
            'Actualiza la totalidad de los campos del examen. '
            'La operación se rechaza si existen estudiantes presentando el examen en este momento.'
        ),
        request=SerializadorCrearExamen,
        parameters=[
            OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del examen'),
        ],
        responses={
            200: SerializadorCrearExamen,
            400: OpenApiResponse(description='Datos inválidos o examen en curso por al menos un estudiante'),
            403: OpenApiResponse(description='El examen no pertenece a un curso del docente'),
            404: OpenApiResponse(description='Examen no encontrado'),
        },
    ),
    patch=extend_schema(
        tags=['Exámenes'],
        summary='Actualizar examen parcialmente',
        description=(
            'Actualiza uno o varios campos del examen. '
            'La operación se rechaza si existen estudiantes presentando el examen en este momento.'
        ),
        request=SerializadorCrearExamen,
        parameters=[
            OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del examen'),
        ],
        responses={
            200: SerializadorCrearExamen,
            400: OpenApiResponse(description='Datos inválidos o examen en curso por al menos un estudiante'),
            403: OpenApiResponse(description='El examen no pertenece a un curso del docente'),
            404: OpenApiResponse(description='Examen no encontrado'),
        },
    ),
    delete=extend_schema(
        tags=['Exámenes'],
        summary='Eliminar examen',
        description=(
            'Elimina un examen del docente autenticado. '
            'La operación se rechaza con 409 si existen estudiantes presentando el examen en este momento.'
        ),
        parameters=[
            OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del examen'),
        ],
        responses={
            204: OpenApiResponse(description='Examen eliminado correctamente'),
            403: OpenApiResponse(description='El examen no pertenece a un curso del docente'),
            404: OpenApiResponse(description='Examen no encontrado'),
            409: OpenApiResponse(description='Examen en curso por al menos un estudiante'),
        },
    ),
)
class VistaDetalleExamen(APIView):
    permission_classes = [EsDocente]

    # Recupera el examen solicitado validando que pertenezca a un curso del docente autenticado.
    def get(self, request, examen_id):
        try:
            examen = Examen.objects.get(id=examen_id, curso__docente=request.user)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearExamen(examen)
        return Response(serializador.data)

    # Actualiza la totalidad de los campos del examen; el serializer bloquea la operación si hay sesiones en curso.
    def put(self, request, examen_id):
        try:
            examen = Examen.objects.get(id=examen_id, curso__docente=request.user)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearExamen(examen, data=request.data)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Actualiza parcialmente los campos del examen; el serializer bloquea la operación si hay sesiones en curso.
    def patch(self, request, examen_id):
        try:
            examen = Examen.objects.get(id=examen_id, curso__docente=request.user)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializador = SerializadorCrearExamen(examen, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    # Elimina el examen siempre que no haya ninguna sesión de estudiante en progreso sobre él.
    def delete(self, request, examen_id):
        try:
            examen = Examen.objects.get(id=examen_id, curso__docente=request.user)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if SesionExamen.objects.filter(examen=examen, estado='en_progreso').exists():
            return Response(
                {'detalle': 'No se puede eliminar el examen porque hay estudiantes presentándolo en este momento.'},
                status=status.HTTP_409_CONFLICT,
            )

        examen.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
