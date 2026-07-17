"""
Vista de mejora entre intentos, para el rol Docente.

Expone `GET /analitica/curso/<curso_id>/mejora-intentos/`: para cada examen
del curso donde algún estudiante haya presentado más de un intento
(`SesionExamen.intento`), reporta la nota promedio y % de aprobados por
número de intento, y cuántos estudiantes mejoraron su nota del primer al
último intento. Responde la pregunta que ningún otro endpoint contesta:
¿repetir el examen realmente ayuda a aprender, o los estudiantes se estancan?

Exámenes sin reintentos reales (todos con un solo intento) se omiten: no hay
nada que comparar.
"""

from collections import defaultdict
from django.db.models import Count, Avg, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.analitica.models import Resultado
from apps.examenes.models import Curso


@extend_schema(
    tags=['Analítica'],
    summary='Mejora entre intentos por examen',
    description=(
        'Para exámenes con más de un intento presentado por al menos un estudiante, compara '
        'nota promedio y % de aprobados por número de intento, y cuántos estudiantes mejoraron '
        'entre su primer y su último intento. Exámenes sin reintentos reales se omiten.'
    ),
    parameters=[
        OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID del curso'),
    ],
    responses={
        200: OpenApiResponse(description='Comparación de desempeño por intento, por examen'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
    },
)
class VistaMejoraIntentos(APIView):
    permission_classes = [EsDocente]

    def get(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        examenes_data = []

        for examen in curso.examenes.order_by('creado_en'):
            resultados_qs = Resultado.objects.filter(examen=examen).select_related('sesion')

            por_intento_raw = resultados_qs.values('sesion__intento').annotate(
                total=Count('id'),
                nota_promedio=Avg('nota'),
                aprobados=Count('id', filter=Q(nota__gte=3.0)),
            ).order_by('sesion__intento')

            # Sin un segundo intento presentado por nadie, no hay nada que comparar.
            if not any(p['sesion__intento'] > 1 for p in por_intento_raw):
                continue

            intentos_data = [
                {
                    'intento': p['sesion__intento'],
                    'total_resultados': p['total'],
                    'nota_promedio': round(p['nota_promedio'], 2),
                    'porcentaje_aprobados': round(p['aprobados'] / p['total'] * 100, 1) if p['total'] else 0.0,
                }
                for p in por_intento_raw
            ]

            # Nota del primer y último intento presentado por cada estudiante, para medir mejora individual.
            notas_por_estudiante = defaultdict(dict)
            for r in resultados_qs.values('estudiante_id', 'sesion__intento', 'nota'):
                notas_por_estudiante[r['estudiante_id']][r['sesion__intento']] = r['nota']

            deltas = []
            for notas in notas_por_estudiante.values():
                if len(notas) < 2:
                    continue
                intentos_ordenados = sorted(notas.keys())
                primero = notas[intentos_ordenados[0]]
                ultimo = notas[intentos_ordenados[-1]]
                deltas.append(ultimo - primero)

            examenes_data.append({
                'examen_id': examen.id,
                'titulo': examen.titulo,
                'max_intentos': examen.max_intentos,
                'intentos': intentos_data,
                'estudiantes_con_reintento': len(deltas),
                'estudiantes_mejoraron': sum(1 for d in deltas if d > 0),
                'estudiantes_empeoraron': sum(1 for d in deltas if d < 0),
                'mejora_promedio': round(sum(deltas) / len(deltas), 2) if deltas else None,
            })

        return Response({
            'curso': curso.nombre,
            'examenes': examenes_data,
        })
