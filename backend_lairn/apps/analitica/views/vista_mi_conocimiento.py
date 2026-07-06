from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.motor_adaptativo.models import ModeloConocimiento
from apps.examenes.models import Curso, Inscripcion

NIVEL_TEXTO = {1: 'Débil', 2: 'En desarrollo', 3: 'Dominado'}


def _calcular_nivel(tasa: float) -> int:
    if tasa >= 0.8:
        return 3
    if tasa >= 0.5:
        return 2
    return 1


def _enriquecer_conceptos(conceptos: dict) -> list:
    resultado = []
    for nombre, datos in conceptos.items():
        tasa = round((datos['correctas'] / datos['intentos']) * 100, 1) if datos['intentos'] else 0
        resultado.append({
            'concepto': nombre,
            'intentos': datos['intentos'],
            'correctas': datos['correctas'],
            'porcentaje_acierto': tasa,
            'nivel': datos['nivel'],
            'nivel_texto': NIVEL_TEXTO.get(datos['nivel'], 'Desconocido'),
        })
    return sorted(resultado, key=lambda x: x['porcentaje_acierto'])


def _procesar_modelos(modelos) -> tuple:
    conceptos_globales = {}
    examenes_data = []
    for modelo in modelos:
        examenes_data.append({
            'examen_id': modelo.examen.id,
            'examen_titulo': modelo.examen.titulo,
            'conceptos': _enriquecer_conceptos(modelo.conceptos),
        })
        for nombre, datos in modelo.conceptos.items():
            if nombre not in conceptos_globales:
                conceptos_globales[nombre] = {'intentos': 0, 'correctas': 0, 'nivel': 2}
            conceptos_globales[nombre]['intentos'] += datos['intentos']
            conceptos_globales[nombre]['correctas'] += datos['correctas']
    for datos in conceptos_globales.values():
        tasa = datos['correctas'] / datos['intentos'] if datos['intentos'] else 0
        datos['nivel'] = _calcular_nivel(tasa)
    return conceptos_globales, examenes_data


_CONCEPTO_FIELDS = {
    'concepto': drf_serializers.CharField(),
    'intentos': drf_serializers.IntegerField(),
    'correctas': drf_serializers.IntegerField(),
    'porcentaje_acierto': drf_serializers.FloatField(),
    'nivel': drf_serializers.IntegerField(help_text='1=Débil 2=En desarrollo 3=Dominado'),
    'nivel_texto': drf_serializers.CharField(),
}


@extend_schema(
    tags=['Analítica'],
    summary='Mi modelo de conocimiento',
    description=(
        'Retorna el mapa de conocimiento del estudiante en todos los exámenes de un curso. '
        'Muestra en qué conceptos falla y cuáles domina, tanto por examen como en un resumen global. '
        'Los conceptos están ordenados de menor a mayor porcentaje de acierto. '
        'El estudiante debe estar inscrito en el curso.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaMiConocimiento',
            fields={
                'curso_id': drf_serializers.IntegerField(),
                'curso_nombre': drf_serializers.CharField(),
                'resumen_global': inline_serializer(
                    name='MiResumenGlobalConcepto',
                    fields={
                        'concepto_mas_debil': drf_serializers.CharField(allow_null=True),
                        'concepto_mas_fuerte': drf_serializers.CharField(allow_null=True),
                        'conceptos': inline_serializer(name='MiConceptoItem', fields=_CONCEPTO_FIELDS, many=True),
                    },
                ),
                'por_examen': inline_serializer(
                    name='MiConceptosPorExamen',
                    fields={
                        'examen_id': drf_serializers.IntegerField(),
                        'examen_titulo': drf_serializers.CharField(),
                        'conceptos': inline_serializer(name='MiConceptoItemExamen', fields=_CONCEPTO_FIELDS, many=True),
                    },
                    many=True,
                ),
            },
        ),
        403: OpenApiResponse(description='No estás inscrito en este curso'),
        404: OpenApiResponse(description='Curso no encontrado o sin datos de conocimiento'),
    },
)
class VistaMiConocimiento(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response(
                {'detalle': 'No estás inscrito en este curso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        modelos = ModeloConocimiento.objects.filter(
            estudiante=request.user, examen__curso=curso
        ).select_related('examen')

        if not modelos.exists():
            return Response(
                {'detalle': 'Aún no tienes datos de conocimiento en este curso.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        conceptos_globales, examenes_data = _procesar_modelos(modelos)
        conceptos_lista = _enriquecer_conceptos(conceptos_globales)

        return Response({
            'curso_id': curso.id,
            'curso_nombre': curso.nombre,
            'resumen_global': {
                'concepto_mas_debil': conceptos_lista[0]['concepto'] if conceptos_lista else None,
                'concepto_mas_fuerte': conceptos_lista[-1]['concepto'] if conceptos_lista else None,
                'conceptos': conceptos_lista,
            },
            'por_examen': examenes_data,
        })
