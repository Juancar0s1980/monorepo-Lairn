"""
Vista comparativa de rendimiento por curso, para el rol Administrador.

Expone el endpoint `/administracion/cursos/` que lista todos los cursos del
sistema con sus métricas de rendimiento (inscritos, exámenes, nota promedio y
tasa de aprobados), a diferencia de `VistaResumenCurso` que solo entrega el
detalle de un curso a su propio docente. Sirve como tabla comparativa para
que el administrador identifique cursos con bajo desempeño sin tener que
consultar curso por curso.
"""

from django.db.models import Avg, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.examenes.models import Curso, Inscripcion, Examen
from apps.analitica.models import Resultado


@extend_schema(
    tags=['Analítica'],
    summary='Rendimiento por curso (Administrador)',
    description=(
        'Retorna todos los cursos del sistema con su docente, total de inscritos, total de '
        'exámenes, nota promedio y tasa de aprobados. Solo accesible para el Administrador.'
    ),
    responses={
        200: OpenApiResponse(description='Lista de cursos con métricas de rendimiento'),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaCursosAdmin(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        cursos = Curso.objects.select_related('docente').order_by('nombre')

        data = []
        for curso in cursos:
            resultados = Resultado.objects.filter(examen__curso=curso).aggregate(
                nota_promedio=Avg('nota'),
                total=Count('id'),
                aprobados=Count('id', filter=Q(nota__gte=3.0)),
            )
            total_resultados = resultados['total'] or 0
            tasa_aprobados = (
                round((resultados['aprobados'] or 0) / total_resultados * 100, 1)
                if total_resultados else 0.0
            )

            data.append({
                'id': curso.id,
                'nombre': curso.nombre,
                'codigo': curso.codigo,
                'docente': f"{curso.docente.first_name} {curso.docente.first_last_name}".strip(),
                'total_inscritos': Inscripcion.objects.filter(curso=curso).count(),
                'total_examenes': Examen.objects.filter(curso=curso).count(),
                'nota_promedio': round(resultados['nota_promedio'] or 1.0, 1),
                'tasa_aprobados': tasa_aprobados,
            })

        return Response(data)
