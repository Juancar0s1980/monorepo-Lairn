from django.db.models import Avg, Count, Q
from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.analitica.models import Resultado
from apps.examenes.models import Curso, Inscripcion
from apps.motor_adaptativo.models import ModeloConocimiento


@extend_schema(
    tags=['Analítica'],
    summary='Resumen ejecutivo del curso',
    description=(
        'Retorna un resumen del desempeño del curso: nota promedio general y la lista de todos los '
        'estudiantes inscritos ordenados de mayor a menor nota. Para cada estudiante muestra cuántos '
        'exámenes presentó, su nota promedio y los conceptos donde tiene dificultades.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaResumenCurso',
            fields={
                'curso': drf_serializers.CharField(),
                'codigo': drf_serializers.CharField(),
                'total_inscritos': drf_serializers.IntegerField(),
                'nota_promedio_curso': drf_serializers.FloatField(help_text='1.0–5.0'),
                'estudiantes': inline_serializer(
                    name='EstudianteResumen',
                    fields={
                        'estudiante_id': drf_serializers.IntegerField(),
                        'nombre': drf_serializers.CharField(),
                        'email': drf_serializers.EmailField(),
                        'examenes_presentados': drf_serializers.IntegerField(),
                        'nota_promedio': drf_serializers.FloatField(),
                        'aprobados': drf_serializers.IntegerField(),
                        'conceptos_debiles': drf_serializers.ListField(child=drf_serializers.CharField()),
                    },
                    many=True,
                ),
            },
        ),
        403: OpenApiResponse(description='Solo los docentes pueden acceder o el curso no le pertenece'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaResumenCurso(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        inscritos = Inscripcion.objects.filter(curso=curso).select_related('estudiante')
        total_inscritos = inscritos.count()

        estudiantes_data = []
        for inscripcion in inscritos:
            estudiante = inscripcion.estudiante
            resultados = Resultado.objects.filter(
                estudiante=estudiante, examen__curso=curso
            ).aggregate(
                nota_promedio=Avg('nota'),
                examenes_presentados=Count('id'),
                aprobados=Count('id', filter=Q(nota__gte=3.0))
            )

            modelos = ModeloConocimiento.objects.filter(
                estudiante=estudiante, examen__curso=curso
            )

            conceptos_globales = {}
            for modelo in modelos:
                for nombre, datos in modelo.conceptos.items():
                    if nombre not in conceptos_globales:
                        conceptos_globales[nombre] = {'intentos': 0, 'correctas': 0}
                    conceptos_globales[nombre]['intentos'] += datos['intentos']
                    conceptos_globales[nombre]['correctas'] += datos['correctas']

            debiles = [
                n for n, d in conceptos_globales.items()
                if d['intentos'] and (d['correctas'] / d['intentos']) < 0.5
            ]

            estudiantes_data.append({
                'estudiante_id': estudiante.id,
                'nombre': f"{estudiante.first_name} {estudiante.first_last_name}",
                'email': estudiante.email,
                'examenes_presentados': resultados['examenes_presentados'] or 0,
                'nota_promedio': round(resultados['nota_promedio'] or 1.0, 1),
                'aprobados': resultados['aprobados'] or 0,
                'conceptos_debiles': debiles,
            })

        estudiantes_data.sort(key=lambda x: x['nota_promedio'], reverse=True)

        nota_general = (
            sum(e['nota_promedio'] for e in estudiantes_data if e['examenes_presentados'] > 0) /
            max(sum(1 for e in estudiantes_data if e['examenes_presentados'] > 0), 1)
        )

        return Response({
            'curso': curso.nombre,
            'codigo': curso.codigo,
            'total_inscritos': total_inscritos,
            'nota_promedio_curso': round(nota_general, 1),
            'estudiantes': estudiantes_data,
        })
