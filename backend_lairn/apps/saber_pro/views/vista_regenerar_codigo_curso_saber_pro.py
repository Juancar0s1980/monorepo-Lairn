"""
Vista de regeneración del código de acceso de un curso Saber Pro (HU-17.3).

Expone `POST /docente/cursos/<curso_id>/regenerar-codigo/`: invalida el código
vigente y asigna uno nuevo generado automáticamente por el sistema, sin que el
docente lo escriba. Los estudiantes con el código anterior dejan de poder unirse
porque la inscripción resuelve el código al momento de unirse (HU-18).

El código nuevo se genera con reintento único desde `services/codigos.py`, por lo
que no existe la posibilidad de un "código duplicado" provocado por el docente.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorCodigoRegenerado
from apps.saber_pro.services.codigos import generar_codigo_unico


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Regenerar código de acceso de un curso Saber Pro',
    description=(
        'Invalida el código vigente del curso y asigna uno nuevo generado automáticamente '
        'por el sistema. El docente no digita el código nuevo; los estudiantes que usan el '
        'código anterior dejan de poder unirse (HU-17.3).'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso Saber Pro'),
    ],
    responses={
        200: SerializadorCodigoRegenerado,
        403: OpenApiResponse(description='El curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaRegenerarCodigoCursoSaberPro(APIView):
    permission_classes = [EsDocente]

    # Reemplaza el código vigente del curso por uno nuevo y único.
    def post(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        codigo_anterior = curso.codigo
        curso.codigo = generar_codigo_unico()
        curso.save(update_fields=['codigo', 'actualizado_en'])

        serializador = SerializadorCodigoRegenerado({
            'id': curso.id,
            'codigo': curso.codigo,
            'codigo_anterior': codigo_anterior,
        })
        return Response(serializador.data)