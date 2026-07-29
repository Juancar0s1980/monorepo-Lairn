"""
Vista para aprobar un tema de estudio pendiente, para el rol Docente.

Expone `PATCH /campo-estudio/temas/<tema_id>/aprobar/`: el paso que hace
visible el tema para los estudiantes inscritos (junto con
`Curso.campo_estudio_habilitado=True`).
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.campo_estudio.models import TemaEstudio
from apps.campo_estudio.serializers import SerializadorTemaEstudio


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Aprobar tema de estudio',
    description='Marca el tema como aprobado y visible para los estudiantes inscritos en el curso.',
    request=None,
    parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={200: SerializadorTemaEstudio, 404: OpenApiResponse(description='Tema no encontrado')},
)
class VistaAprobarTemaEstudio(APIView):
    permission_classes = [EsDocente]

    def patch(self, request, tema_id):
        try:
            tema = TemaEstudio.objects.get(id=tema_id, curso__docente=request.user)
        except TemaEstudio.DoesNotExist:
            return Response({'detalle': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        tema.estado = 'aprobado'
        tema.aprobado_en = timezone.now()
        tema.save(update_fields=['estado', 'aprobado_en'])
        return Response(SerializadorTemaEstudio(tema).data)
