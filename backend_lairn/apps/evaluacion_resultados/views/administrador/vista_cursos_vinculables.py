"""
Cursos Lairn que la coordinación puede vincular a una asignatura de la malla.

Vincular `AsignaturaMalla.curso_vinculado` es lo que da al docente dueño
del curso acceso a esa asignatura en su banco de preguntas (HU-04.5:
"el banco de preguntas de mi materia").
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.examenes.models import Curso
from core.permissions.permisos_rol import EsGestorAcademico


class VistaCursosVinculables(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        cursos = Curso.objects.select_related('docente').order_by('nombre')
        return Response([
            {
                'id': c.id, 'nombre': c.nombre, 'codigo': c.codigo,
                'docente': f'{c.docente.first_name} {c.docente.first_last_name}'.strip(),
                'docente_email': c.docente.email,
            }
            for c in cursos
        ])
