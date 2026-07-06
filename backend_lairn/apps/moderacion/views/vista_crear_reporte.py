"""
Vista de creación de reportes, para cualquier usuario autenticado.

Expone el endpoint `/reportes/` (POST) que permite a un Docente o Estudiante
señalar un curso o examen problemático. No restringe por rol ni por
pertenencia al recurso reportado: cualquier usuario autenticado que vea
contenido inapropiado puede reportarlo, y es el Administrador quien decide si
el reporte procede.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.moderacion.serializers.serializador_crear_reporte import SerializadorCrearReporte


@extend_schema(
    tags=['Moderación'],
    summary='Reportar un curso o examen',
    description='Crea un reporte sobre un curso o un examen para que el administrador lo revise.',
    request=SerializadorCrearReporte,
    responses={
        201: SerializadorCrearReporte,
        400: OpenApiResponse(description='Datos inválidos'),
    },
)
class VistaCrearReporte(APIView):
    permission_classes = [IsAuthenticated]

    # Crea un reporte asociado al usuario autenticado.
    def post(self, request):
        serializador = SerializadorCrearReporte(data=request.data)
        if serializador.is_valid():
            serializador.save(reportado_por=request.user)
            return Response(serializador.data, status=status.HTTP_201_CREATED)
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
