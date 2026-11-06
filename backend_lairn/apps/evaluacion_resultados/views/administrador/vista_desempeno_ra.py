"""
Tablero de porcentaje de acierto por RA de un programa (HU-09.1).

`GET programas/<id>/desempeno-ra/?momento=&evaluacion=` — solo Administrador
(la historia lo asigna a ese rol). Incluye la lista de momentos y
evaluaciones con resultados para los filtros. Métrica provisional: ver
`services/servicio_desempeno_ra.py`.
"""

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    EvaluacionFormal,
    OpcionesEstadoEvaluacion,
    OpcionesTipoEvaluacion,
    ProgramaAcademico,
)
from apps.evaluacion_resultados.services.servicio_desempeno_ra import desempeno_por_ra
from core.permissions.permisos_rol import EsAdministrador


def _id(valor):
    return int(valor) if valor and str(valor).isdigit() else None


class VistaDesempenoRA(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request, programa_id):
        programa = get_object_or_404(ProgramaAcademico, pk=programa_id)
        momento_id = _id(request.query_params.get('momento'))
        evaluacion_id = _id(request.query_params.get('evaluacion'))
        evaluaciones = EvaluacionFormal.objects.filter(
            momento__programa=programa, estado=OpcionesEstadoEvaluacion.PUBLICADA,
            tipo=OpcionesTipoEvaluacion.CUESTIONARIO,
        ).select_related('momento').order_by('momento__semestre_referencia', 'fecha_inicio')
        datos = desempeno_por_ra(programa, momento_id, evaluacion_id)
        datos['filtros'] = {
            'momentos': sorted(
                {(e.momento_id, e.momento.nombre) for e in evaluaciones}, key=lambda m: m[1],
            ),
            'evaluaciones': [
                {'id': e.id, 'nombre': e.nombre, 'momento_id': e.momento_id} for e in evaluaciones
            ],
        }
        datos['filtros']['momentos'] = [{'id': i, 'nombre': n} for i, n in datos['filtros']['momentos']]
        datos['metrica'] = (
            'Provisional: aciertos ÷ preguntas presentadas del RA en evaluaciones formales enviadas '
            '(sin responder cuenta como no acertada). Pendiente de validar con Vicerrectoría.'
        )
        return Response(datos)
