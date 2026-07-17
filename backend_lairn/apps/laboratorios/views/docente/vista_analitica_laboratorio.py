"""
Vista de analítica de un laboratorio, para el rol Docente.

Expone `/laboratorios/laboratorios/<laboratorio_id>/analitica/`: por cada
pregunta, cuántos estudiantes la intentaron, cuántos la resolvieron al 100%,
el % de acierto promedio (sobre la MEJOR entrega de cada estudiante, no
todas — un estudiante que reintenta y mejora no debe "ensuciar" el promedio
con sus intentos fallidos previos) y los intentos promedio gastados. También
un resumen por estudiante con su progreso en el laboratorio completo.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import Laboratorio, EntregaCodigo


@extend_schema(
    tags=['Laboratorios'],
    summary='Analítica del laboratorio',
    description=(
        'Por pregunta: estudiantes que la intentaron/resolvieron, % de acierto promedio e '
        'intentos promedio (sobre la mejor entrega de cada estudiante). Por estudiante: '
        'preguntas resueltas y puntaje promedio en el laboratorio.'
    ),
    parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: OpenApiResponse(description='Analítica del laboratorio'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Laboratorio no encontrado'),
    },
)
class VistaAnaliticaLaboratorio(APIView):
    permission_classes = [EsDocente]

    def get(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.get(id=laboratorio_id, curso__docente=request.user)
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        preguntas = list(laboratorio.preguntas.all())
        datos_preguntas = []
        # estudiante_id -> {nombre, email, preguntas_resueltas, suma_puntajes, preguntas_intentadas}
        resumen_estudiantes = {}

        for pregunta in preguntas:
            entregas = EntregaCodigo.objects.filter(pregunta=pregunta).select_related('estudiante')

            mejor_por_estudiante = {}
            intentos_por_estudiante = {}
            for entrega in entregas:
                eid = entrega.estudiante_id
                intentos_por_estudiante[eid] = intentos_por_estudiante.get(eid, 0) + 1
                if eid not in mejor_por_estudiante or entrega.puntaje > mejor_por_estudiante[eid].puntaje:
                    mejor_por_estudiante[eid] = entrega

            estudiantes_intentaron = len(mejor_por_estudiante)
            estudiantes_resueltas = sum(1 for e in mejor_por_estudiante.values() if e.puntaje == 100)
            porcentaje_acierto_promedio = (
                round(sum(e.puntaje for e in mejor_por_estudiante.values()) / estudiantes_intentaron, 1)
                if estudiantes_intentaron else None
            )
            intentos_promedio = (
                round(sum(intentos_por_estudiante.values()) / estudiantes_intentaron, 1)
                if estudiantes_intentaron else None
            )

            datos_preguntas.append({
                'pregunta_id': pregunta.id,
                'enunciado': pregunta.enunciado,
                'lenguaje': pregunta.lenguaje,
                'estudiantes_intentaron': estudiantes_intentaron,
                'estudiantes_resueltas': estudiantes_resueltas,
                'porcentaje_acierto_promedio': porcentaje_acierto_promedio,
                'intentos_promedio': intentos_promedio,
            })

            for eid, mejor in mejor_por_estudiante.items():
                registro = resumen_estudiantes.setdefault(eid, {
                    'estudiante_id': eid,
                    'nombre': f'{mejor.estudiante.first_name} {mejor.estudiante.first_last_name}',
                    'email': mejor.estudiante.email,
                    'preguntas_resueltas': 0,
                    'suma_puntajes': 0.0,
                    'preguntas_intentadas': 0,
                })
                registro['preguntas_intentadas'] += 1
                registro['suma_puntajes'] += mejor.puntaje
                if mejor.puntaje == 100:
                    registro['preguntas_resueltas'] += 1

        total_preguntas = len(preguntas)
        estudiantes = [
            {
                'estudiante_id': r['estudiante_id'],
                'nombre': r['nombre'],
                'email': r['email'],
                'preguntas_resueltas': r['preguntas_resueltas'],
                'total_preguntas': total_preguntas,
                'puntaje_promedio': round(r['suma_puntajes'] / r['preguntas_intentadas'], 1) if r['preguntas_intentadas'] else 0.0,
            }
            for r in resumen_estudiantes.values()
        ]
        estudiantes.sort(key=lambda e: -e['puntaje_promedio'])

        return Response({
            'laboratorio': laboratorio.titulo,
            'total_preguntas': total_preguntas,
            'total_estudiantes_intentaron': len(resumen_estudiantes),
            'preguntas': datos_preguntas,
            'estudiantes': estudiantes,
        })
