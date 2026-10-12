"""
Vista de inscripción de un estudiante a un curso Saber Pro por código (HU-18).

Expone `POST /api/saber-pro/estudiante/unirse/`. Recibe el `codigo` de acceso
de 8 caracteres y crea la `InscripcionCursoSaberPro` del estudiante
autenticado.

Se usa código en lugar de `curso_id` porque el flujo está diseñado para que el
docente comparta un identificador corto y opaco con sus estudiantes (HU-17.2),
sin exponer ids internos ni listar cursos públicos. La vista traduce los errores
de dominio del servicio `services/inscripciones.py` a respuestas HTTP con
mensajes claros según el criterio de aceptación de HU-18:

- código inválido, regenerado o inexistente (HU-18.2);
- curso desactivado, por la desactivación de HU-17.6 (HU-18.2);
- estudiante ya inscrito (HU-18.4).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsEstudiante
from apps.saber_pro.serializers import (
    SerializadorInscripcionCursoSaberPro,
    SerializadorUnirseCursoSaberPro,
)
from apps.saber_pro.services.inscripciones import (
    ErrorInscripcionSaberPro,
    inscribir_estudiante,
)


@extend_schema(
    tags=['Saber Pro - Estudiante'],
    summary='Unirse a un curso Saber Pro con código de acceso',
    description=(
        'El estudiante ingresa el código de acceso del curso (8 caracteres) para '
        'inscribirse. Si el código no existe, fue regenerado, el curso está '
        'desactivado o el estudiante ya pertenece al curso, retorna un error claro.'
    ),
    request=SerializadorUnirseCursoSaberPro,
    examples=[
        OpenApiExample(
            name='Unirse a un curso',
            value={'codigo': 'AB3X9KLM'},
            request_only=True,
        ),
    ],
    responses={
        201: SerializadorInscripcionCursoSaberPro,
        400: OpenApiResponse(description='Código inválido, curso desactivado o estudiante ya inscrito'),
        403: OpenApiResponse(description='Solo los estudiantes pueden inscribirse'),
    },
)
class VistaUnirseCursoSaberPro(APIView):
    permission_classes = [EsEstudiante]

    # Inscribe al estudiante autenticado en el curso identificado por el código (HU-18).
    def post(self, request):
        serializador = SerializadorUnirseCursoSaberPro(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            inscripcion = inscribir_estudiante(
                request.user,
                serializador.validated_data['codigo'],
            )
        except ErrorInscripcionSaberPro as error:
            return Response({'detalle': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            SerializadorInscripcionCursoSaberPro(inscripcion).data,
            status=status.HTTP_201_CREATED,
        )