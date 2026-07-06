from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.motor_adaptativo.models import ModeloConocimiento
from apps.examenes.models import Curso

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


def _acumular_concepto(conceptos_globales: dict, nombre: str, datos: dict) -> None:
    if nombre not in conceptos_globales:
        conceptos_globales[nombre] = {'intentos': 0, 'correctas': 0, 'nivel': 2}
    conceptos_globales[nombre]['intentos'] += datos['intentos']
    conceptos_globales[nombre]['correctas'] += datos['correctas']


def _recalcular_niveles(conceptos_globales: dict) -> None:
    for datos in conceptos_globales.values():
        tasa = datos['correctas'] / datos['intentos'] if datos['intentos'] else 0
        datos['nivel'] = _calcular_nivel(tasa)


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
            _acumular_concepto(conceptos_globales, nombre, datos)
    _recalcular_niveles(conceptos_globales)
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
    summary='Modelo de conocimiento de un estudiante',
    description=(
        'Retorna el mapa de conocimiento del estudiante en todos los exámenes del curso. '
        'Muestra en qué conceptos falla y cuáles domina, tanto por examen como en un resumen global. '
        'Los conceptos están ordenados de menor a mayor porcentaje de acierto.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
        OpenApiParameter('estudiante_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del estudiante'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaModeloConocimiento',
            fields={
                'estudiante_id': drf_serializers.IntegerField(),
                'curso_id': drf_serializers.IntegerField(),
                'resumen_global': inline_serializer(
                    name='ResumenGlobalConcepto',
                    fields={
                        'concepto_mas_debil': drf_serializers.CharField(allow_null=True),
                        'concepto_mas_fuerte': drf_serializers.CharField(allow_null=True),
                        'conceptos': inline_serializer(name='ConceptoItem', fields=_CONCEPTO_FIELDS, many=True),
                    },
                ),
                'por_examen': inline_serializer(
                    name='ConceptosPorExamen',
                    fields={
                        'examen_id': drf_serializers.IntegerField(),
                        'examen_titulo': drf_serializers.CharField(),
                        'conceptos': inline_serializer(name='ConceptoItem', fields=_CONCEPTO_FIELDS, many=True),
                    },
                    many=True,
                ),
            },
        ),
        403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado o sin datos de conocimiento para el estudiante'),
    },
)
class VistaModeloConocimientoEstudiante(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id, estudiante_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        modelos = ModeloConocimiento.objects.filter(
            estudiante_id=estudiante_id,
            examen__curso=curso
        ).select_related('examen')

        if not modelos.exists():
            return Response(
                {'detalle': 'Sin datos de conocimiento para este estudiante.'},
                status=status.HTTP_404_NOT_FOUND
            )

        conceptos_globales, examenes_data = _procesar_modelos(modelos)
        conceptos_lista = _enriquecer_conceptos(conceptos_globales)

        return Response({
            'estudiante_id': estudiante_id,
            'curso_id': curso_id,
            'resumen_global': {
                'concepto_mas_debil': conceptos_lista[0]['concepto'] if conceptos_lista else None,
                'concepto_mas_fuerte': conceptos_lista[-1]['concepto'] if conceptos_lista else None,
                'conceptos': conceptos_lista,
            },
            'por_examen': examenes_data,
        })
