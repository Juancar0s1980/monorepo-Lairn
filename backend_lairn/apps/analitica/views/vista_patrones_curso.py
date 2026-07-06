from django.db.models import Count, Avg, Q
from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.analitica.models import RespuestaEstudiante, Resultado
from apps.examenes.models import Curso, Inscripcion

DIFICULTAD_TEXTO = {1: 'Fácil', 2: 'Medio', 3: 'Difícil'}


@extend_schema(
    tags=['Analítica'],
    summary='Patrones de fallo y desempeño del curso',
    description=(
        'Analítica detallada del curso para el docente: nota promedio, desempeño por examen, '
        'análisis por nivel de dificultad y los 5 conceptos donde el grupo falla más y los 5 donde está mejor. '
        'Si no hay exámenes presentados aún, retorna un mensaje indicándolo.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaPatronesCurso',
            fields={
                'curso': drf_serializers.CharField(),
                'total_inscritos': drf_serializers.IntegerField(),
                'nota_promedio_curso': drf_serializers.FloatField(help_text='1.0–5.0'),
                'examenes': inline_serializer(
                    name='ExamenPatron',
                    fields={
                        'examen_id': drf_serializers.IntegerField(),
                        'titulo': drf_serializers.CharField(),
                        'total_presentaciones': drf_serializers.IntegerField(),
                        'nota_promedio': drf_serializers.FloatField(),
                        'aprobados': drf_serializers.IntegerField(),
                        'porcentaje_aprobados': drf_serializers.FloatField(),
                    },
                    many=True,
                ),
                'analisis_por_dificultad': inline_serializer(
                    name='DificultadPatron',
                    fields={
                        'dificultad': drf_serializers.IntegerField(),
                        'nombre': drf_serializers.CharField(help_text='Fácil | Medio | Difícil'),
                        'total_preguntas': drf_serializers.IntegerField(),
                        'correctas': drf_serializers.IntegerField(),
                        'porcentaje_acierto': drf_serializers.FloatField(),
                        'tiempo_promedio_segundos': drf_serializers.FloatField(),
                    },
                    many=True,
                ),
                'conceptos_mas_debiles': inline_serializer(
                    name='ConceptoPatron',
                    fields={
                        'concepto': drf_serializers.CharField(),
                        'total_preguntas': drf_serializers.IntegerField(),
                        'correctas': drf_serializers.IntegerField(),
                        'porcentaje_acierto': drf_serializers.FloatField(),
                    },
                    many=True,
                ),
                'conceptos_mas_fuertes': inline_serializer(
                    name='ConceptoFuerte',
                    fields={
                        'concepto': drf_serializers.CharField(),
                        'total_preguntas': drf_serializers.IntegerField(),
                        'correctas': drf_serializers.IntegerField(),
                        'porcentaje_acierto': drf_serializers.FloatField(),
                    },
                    many=True,
                ),
            },
        ),
        403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaPatronesCurso(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        total_inscritos = Inscripcion.objects.filter(curso=curso).count()
        resultados_qs = Resultado.objects.filter(examen__curso=curso)

        if not resultados_qs.exists():
            return Response({
                'curso': curso.nombre,
                'total_inscritos': total_inscritos,
                'mensaje': 'Aún no hay exámenes presentados en este curso.',
            })

        nota_promedio_curso = resultados_qs.aggregate(promedio=Avg('nota'))['promedio']

        # Análisis por examen
        por_examen = resultados_qs.values(
            'examen__id', 'examen__titulo'
        ).annotate(
            total_presentaciones=Count('id'),
            nota_promedio=Avg('nota'),
            aprobados=Count('id', filter=Q(nota__gte=3.0))
        ).order_by('examen__id')

        examenes_data = []
        for e in por_examen:
            total = e['total_presentaciones']
            examenes_data.append({
                'examen_id': e['examen__id'],
                'titulo': e['examen__titulo'],
                'total_presentaciones': total,
                'nota_promedio': round(e['nota_promedio'], 1),
                'aprobados': e['aprobados'],
                'porcentaje_aprobados': round((e['aprobados'] / total) * 100, 1) if total else 0,
            })

        # Análisis por dificultad
        respuestas_qs = RespuestaEstudiante.objects.filter(resultado__examen__curso=curso)

        por_dificultad_raw = respuestas_qs.values('dificultad').annotate(
            total=Count('id'),
            correctas=Count('id', filter=Q(respuesta_incorrecta='')),
            tiempo_promedio=Avg('tiempo_por_pregunta')
        ).order_by('dificultad')

        por_dificultad = []
        for d in por_dificultad_raw:
            total = d['total']
            correctas = d['correctas']
            por_dificultad.append({
                'dificultad': d['dificultad'],
                'nombre': DIFICULTAD_TEXTO.get(d['dificultad'], str(d['dificultad'])),
                'total_preguntas': total,
                'correctas': correctas,
                'porcentaje_acierto': round((correctas / total) * 100, 1) if total else 0,
                'tiempo_promedio_segundos': round(d['tiempo_promedio'] or 0, 1),
            })

        # Análisis por concepto (dónde falla y dónde está mejor el grupo)
        por_concepto_raw = respuestas_qs.exclude(
            concepto=''
        ).values('concepto').annotate(
            total=Count('id'),
            correctas=Count('id', filter=Q(respuesta_incorrecta='')),
        ).order_by('concepto')

        conceptos = []
        for c in por_concepto_raw:
            total = c['total']
            correctas = c['correctas']
            conceptos.append({
                'concepto': c['concepto'],
                'total_preguntas': total,
                'correctas': correctas,
                'porcentaje_acierto': round((correctas / total) * 100, 1) if total else 0,
            })

        conceptos_ordenados = sorted(conceptos, key=lambda x: x['porcentaje_acierto'])

        return Response({
            'curso': curso.nombre,
            'total_inscritos': total_inscritos,
            'nota_promedio_curso': round(nota_promedio_curso, 1),
            'examenes': examenes_data,
            'analisis_por_dificultad': por_dificultad,
            'conceptos_mas_debiles': conceptos_ordenados[:5],
            'conceptos_mas_fuertes': conceptos_ordenados[-5:][::-1],
        })
