"""
Vista de sugerencia de preguntas de código con IA, para el rol Docente.

Expone `POST /laboratorios/laboratorios/<laboratorio_id>/preguntas/sugerir-ia/`:
genera UNA pregunta de código por cada objetivo del curso (ver
`agente_codigo.generar_borrador_pregunta`), verifica sus casos de test
ejecutando la solución de referencia en el sandbox del ejecutor (ver
`verificador_casos.verificar_casos`) y devuelve los borradores YA
VERIFICADOS para que el docente los revise.

Importante: NO guarda nada. El docente acepta/descarta cada borrador en la
UI y los aceptados se crean con el POST normal de `/preguntas/` (el mismo
que usa la creación manual, con sus casos de test anidados).

Si el curso no tiene objetivos, 400 (no hay de dónde generar). Si algún
objetivo no produce una pregunta utilizable (la IA falla dos veces, o
ninguno de sus casos sobrevive la verificación), se omite y se reporta en
`objetivos_sin_generar` en vez de tumbar toda la operación.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.services.agente_codigo import generar_borrador_pregunta
from apps.laboratorios.services.verificador_casos import verificar_casos


@extend_schema(
    tags=['Laboratorios'],
    summary='Sugerir preguntas de código con IA (una por objetivo del curso)',
    request=None,
    parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: inline_serializer(
            name='RespuestaSugerirPreguntasCodigo',
            fields={
                'preguntas': drf_serializers.ListField(),
                'objetivos_sin_generar': drf_serializers.ListField(child=drf_serializers.CharField()),
            },
        ),
        400: OpenApiResponse(description='El curso no tiene objetivos definidos'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Laboratorio no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar ninguna pregunta verificable'),
    },
)
class VistaSugerirPreguntasCodigo(APIView):
    permission_classes = [EsDocente]

    def post(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.select_related('curso').get(
                id=laboratorio_id, curso__docente=request.user
            )
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        curso = laboratorio.curso
        objetivos = list(curso.objetivos.all())
        if not objetivos:
            return Response(
                {'detalle': 'El curso no tiene objetivos definidos. Agrégalos en la tab Objetivos antes de generar preguntas con IA.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preguntas = []
        objetivos_sin_generar = []

        for orden, objetivo in enumerate(objetivos):
            try:
                borrador = generar_borrador_pregunta(objetivo.descripcion, curso.nombre)
            except ValueError:
                objetivos_sin_generar.append(objetivo.descripcion)
                continue

            casos = verificar_casos(
                borrador['lenguaje'],
                borrador['solucion_referencia'],
                borrador.get('setup_sql', ''),
                borrador['casos'],
            )
            if not casos:
                objetivos_sin_generar.append(objetivo.descripcion)
                continue

            preguntas.append({
                'objetivo_id': objetivo.id,
                'objetivo': objetivo.descripcion,
                'enunciado': borrador['enunciado'],
                'lenguaje': borrador['lenguaje'],
                'codigo_inicial': borrador.get('codigo_inicial', ''),
                'setup_sql': borrador.get('setup_sql', ''),
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': casos,
            })

        if not preguntas:
            return Response(
                {'detalle': 'La IA no pudo generar ni verificar ninguna pregunta para los objetivos del curso.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'preguntas': preguntas, 'objetivos_sin_generar': objetivos_sin_generar})
