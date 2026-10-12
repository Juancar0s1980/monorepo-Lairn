"""
Vista de aprobación de contenido del banco Saber Pro, para el rol Docente (HU-20.3/20.4).

Expone `PATCH /docente/contenido/<contenido_id>/aprobar/`: marca el contenido
como `aprobado` y registra el momento de la aprobación. A partir de ahí la
HU-19 podrá incluirlo al ensamblar simulacros del área del curso (HU-20.4).
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.serializers import SerializadorContenidoBanco


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Aprobar contenido del banco',
    description=(
        'Marca como aprobado el contenido generado para que pueda usarse en los '
        'simulacros del curso (HU-20.4).'
    ),
    request=None,
    responses={
        200: SerializadorContenidoBanco,
        400: OpenApiResponse(description='El contenido ya estaba aprobado'),
        404: OpenApiResponse(description='Contenido no encontrado'),
    },
)
class VistaAprobarContenidoBancoSaberPro(APIView):
    permission_classes = [EsDocente]

    def patch(self, request, contenido_id):
        try:
            contenido = ContenidoBancoSaberPro.objects.select_related(
                'area', 'competencia', 'afirmacion', 'evidencia',
            ).get(id=contenido_id, docente=request.user)
        except ContenidoBancoSaberPro.DoesNotExist:
            return Response({'detalle': 'Contenido del banco no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if contenido.estado == 'aprobado':
            return Response({'detalle': 'El contenido ya estaba aprobado.'}, status=status.HTTP_400_BAD_REQUEST)

        contenido.estado = 'aprobado'
        contenido.aprobado_en = timezone.now()
        contenido.save(update_fields=['estado', 'aprobado_en', 'actualizado_en'])
        return Response(SerializadorContenidoBanco(contenido).data)