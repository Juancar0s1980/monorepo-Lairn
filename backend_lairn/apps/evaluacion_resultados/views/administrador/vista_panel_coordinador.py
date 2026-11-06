"""
Panel de inicio del Coordinador (ADR-013).

- `GET panel-coordinador/?programa=<id>`  resumen con datos reales (todos los programas si no se filtra).

Permiso: Coordinador o Administrador (`EsGestorAcademico`); solo lectura.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.services.servicio_panel_coordinador import panel
from core.permissions.permisos_rol import EsGestorAcademico


class VistaPanelCoordinador(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        programa = (request.query_params.get('programa') or '').strip()
        if programa and not programa.isdigit():
            return Response({'detalle': 'El filtro "programa" debe ser un número.'}, status=400)
        return Response(panel(int(programa) if programa else None))
