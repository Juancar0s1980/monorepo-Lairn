"""
Vista de generación de un laboratorio completo con IA a partir de un
enunciado libre, para el rol Docente.

Expone `POST /laboratorios/cursos/<curso_id>/laboratorios/sugerir-libre/`:
el docente describe en lenguaje natural qué laboratorio quiere y elige
explícitamente el lenguaje de programación; la IA genera título,
instrucciones y varias preguntas completas en ese lenguaje
(`agente_codigo.generar_laboratorio_libre`), y cada pregunta se verifica
ejecutando su solución de referencia en el sandbox
(`verificador_casos.verificar_casos`), igual que la sugerencia por objetivo.

Importante: NO guarda nada. El docente revisa el borrador en la UI; al
aceptar, el frontend crea el `Laboratorio` (POST normal) y luego cada
pregunta aceptada dentro de él (POST normal de `/preguntas/`).

Si ninguna pregunta sobrevive la verificación, 502 (nada que ofrecer).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.laboratorios.serializers import SerializadorSugerirLaboratorioLibre
from apps.laboratorios.services.agente_codigo import generar_laboratorio_libre
from apps.laboratorios.services.verificador_casos import verificar_casos


@extend_schema(
    tags=['Laboratorios'],
    summary='Generar un laboratorio completo con IA a partir de un enunciado libre',
    request=SerializadorSugerirLaboratorioLibre,
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: inline_serializer(
            name='RespuestaSugerirLaboratorioLibre',
            fields={
                'titulo': drf_serializers.CharField(),
                'instrucciones': drf_serializers.CharField(),
                'preguntas': drf_serializers.ListField(),
            },
        ),
        400: OpenApiResponse(description='Datos inválidos'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar ninguna pregunta verificable'),
    },
)
class VistaSugerirLaboratorioLibre(APIView):
    permission_classes = [EsDocente]

    def post(self, request, curso_id):
        try:
            Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        entrada = SerializadorSugerirLaboratorioLibre(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            borrador = generar_laboratorio_libre(
                enunciado_docente=entrada.validated_data['enunciado'],
                lenguaje=entrada.validated_data['lenguaje'],
                cantidad_preguntas=entrada.validated_data['cantidad_preguntas'],
            )
        except ValueError as e:
            return Response({'detalle': f'No se pudo generar el laboratorio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        preguntas_verificadas = []
        for orden, pregunta in enumerate(borrador['preguntas']):
            casos = verificar_casos(
                pregunta['lenguaje'], pregunta['solucion_referencia'], pregunta.get('setup_sql', ''), pregunta['casos']
            )
            if not casos:
                continue
            preguntas_verificadas.append({
                'tipo': 'codigo',
                'enunciado': pregunta['enunciado'],
                'lenguaje': pregunta['lenguaje'],
                'codigo_inicial': pregunta.get('codigo_inicial', ''),
                'setup_sql': pregunta.get('setup_sql', ''),
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': casos,
            })

        if not preguntas_verificadas:
            return Response(
                {'detalle': 'La IA no pudo generar ninguna pregunta verificable para ese laboratorio.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'titulo': borrador['titulo'],
            'instrucciones': borrador['instrucciones'],
            'preguntas': preguntas_verificadas,
        })
