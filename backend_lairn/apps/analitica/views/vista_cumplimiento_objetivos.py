"""
Vista de cumplimiento de objetivos de aprendizaje, para el rol Docente.

Expone `GET /analitica/curso/<curso_id>/objetivos/`: para cada examen del
curso que tenga objetivos anclados, reporta el desempeño por objetivo y un
resumen agregado del examen y del curso.

La agregación es posible porque el generador de preguntas copia el texto del
objetivo como `concepto` (tanto en `RespuestaEstudiante.concepto` como en las
claves de `ModeloConocimiento.conceptos`), así que el cruce es por igualdad
exacta de texto. Si el docente edita un objetivo después de que hubo
respuestas, las respuestas viejas quedan asociadas al texto anterior — se
reporta lo registrado, no se reescribe historia.

Criterio de estado por objetivo (sobre el nivel BKT/heurístico 1-3 de los
estudiantes que lo han enfrentado):
- `cumplido`: nivel promedio >= 2.5
- `en_proceso`: nivel promedio >= 1.5
- `no_cumplido`: nivel promedio < 1.5
- `sin_datos`: ningún estudiante lo ha enfrentado aún
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.analitica.models import RespuestaEstudiante
from apps.motor_adaptativo.models import ModeloConocimiento

UMBRAL_CUMPLIDO = 2.5
UMBRAL_EN_PROCESO = 1.5


def _estado_por_nivel(nivel_promedio):
    if nivel_promedio is None:
        return 'sin_datos'
    if nivel_promedio >= UMBRAL_CUMPLIDO:
        return 'cumplido'
    if nivel_promedio >= UMBRAL_EN_PROCESO:
        return 'en_proceso'
    return 'no_cumplido'


@extend_schema(
    tags=['Analítica'],
    summary='Cumplimiento de objetivos por examen',
    description=(
        'Para cada examen del curso con objetivos anclados, reporta por objetivo: preguntas '
        'respondidas, % de acierto, estudiantes evaluados, cuántos lo dominan (nivel 3), nivel '
        'promedio y estado (cumplido / en_proceso / no_cumplido / sin_datos). Incluye resumen '
        'por examen y global del curso.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: OpenApiResponse(description='Cumplimiento por objetivo, por examen y global'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaCumplimientoObjetivos(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        examenes = (
            curso.examenes
            .prefetch_related('objetivos')
            .order_by('creado_en')
        )

        datos_examenes = []
        conteo_global = {'cumplido': 0, 'en_proceso': 0, 'no_cumplido': 0, 'sin_datos': 0}

        for examen in examenes:
            objetivos = list(examen.objetivos.all())
            if not objetivos:
                continue

            # Modelos de conocimiento de todos los estudiantes que han rendido este examen.
            modelos = list(
                ModeloConocimiento.objects.filter(examen=examen).values_list('conceptos', flat=True)
            )

            datos_objetivos = []
            conteo_examen = {'cumplido': 0, 'en_proceso': 0, 'no_cumplido': 0, 'sin_datos': 0}

            for objetivo in objetivos:
                texto = objetivo.descripcion

                respuestas = RespuestaEstudiante.objects.filter(
                    resultado__examen=examen, concepto=texto
                )
                total_preguntas = respuestas.count()
                correctas = respuestas.filter(respuesta_incorrecta='').count()

                niveles = [
                    conceptos[texto]['nivel']
                    for conceptos in modelos
                    if texto in conceptos
                ]
                estudiantes_evaluados = len(niveles)
                nivel_promedio = round(sum(niveles) / estudiantes_evaluados, 2) if niveles else None
                estado = _estado_por_nivel(nivel_promedio)
                conteo_examen[estado] += 1
                conteo_global[estado] += 1

                datos_objetivos.append({
                    'objetivo_id': objetivo.id,
                    'objetivo': texto,
                    'preguntas_respondidas': total_preguntas,
                    'correctas': correctas,
                    'porcentaje_acierto': round(correctas / total_preguntas * 100, 1) if total_preguntas else None,
                    'estudiantes_evaluados': estudiantes_evaluados,
                    'estudiantes_dominan': sum(1 for n in niveles if n >= 3),
                    'nivel_promedio': nivel_promedio,
                    'estado': estado,
                })

            total_objetivos = len(objetivos)
            datos_examenes.append({
                'examen_id': examen.id,
                'titulo': examen.titulo,
                'objetivos': datos_objetivos,
                'resumen': {
                    'total_objetivos': total_objetivos,
                    **conteo_examen,
                    'porcentaje_cumplimiento': round(conteo_examen['cumplido'] / total_objetivos * 100, 1),
                },
            })

        total_global = sum(conteo_global.values())
        return Response({
            'curso': curso.nombre,
            'examenes': datos_examenes,
            'resumen_global': {
                'total_objetivos_evaluados': total_global,
                **conteo_global,
                'porcentaje_cumplimiento': round(conteo_global['cumplido'] / total_global * 100, 1) if total_global else 0.0,
            },
        })
