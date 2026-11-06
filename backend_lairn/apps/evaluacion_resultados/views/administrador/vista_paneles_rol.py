"""
Resúmenes de inicio por rol (ADR-014), solo lectura.

- `GET panel-admin/`           Administrador: estado de la plataforma.
- `GET docente/panel/`         Docente: sus asignaturas, banco, tareas, supervisiones y resultados agregados.
- `GET estudiante/panel/`      Estudiante: pendientes e historial (sin nota de la evaluación formal, HU-07).
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.services.servicio_paneles_rol import panel_admin, panel_docente, panel_estudiante
from core.permissions.permisos_rol import EsAdministrador, EsDocente, EsEstudiante


class VistaPanelAdmin(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        return Response(panel_admin())


class VistaPanelDocente(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        return Response(panel_docente(request.user))


class VistaPanelEstudiante(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request):
        return Response(panel_estudiante(request.user))
