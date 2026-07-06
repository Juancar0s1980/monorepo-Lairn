"""
Vista de resumen global del sistema, para el rol Administrador.

Expone el endpoint `/administracion/resumen/` con las métricas agregadas que
alimentan el Dashboard y la página de Analítica del administrador: conteo de
usuarios por rol, totales de cursos/exámenes, estado de las sesiones de
examen, nota promedio y tasa de aprobados globales, y la actividad más
reciente (últimos cursos, exámenes y resultados) para dar visibilidad rápida
del estado del sistema sin tener que navegar curso por curso.
"""

from django.db.models import Avg, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.users.models.user import User
from apps.examenes.models import Curso, Examen
from apps.motor_adaptativo.models import SesionExamen
from apps.analitica.models import Resultado


@extend_schema(
    tags=['Analítica'],
    summary='Resumen global del sistema (Administrador)',
    description=(
        'Retorna métricas agregadas de todo el sistema: usuarios por rol, totales de cursos y '
        'exámenes, estado de las sesiones, nota promedio y tasa de aprobados globales, y la '
        'actividad reciente. Solo accesible para el Administrador.'
    ),
    responses={
        200: OpenApiResponse(description='Métricas agregadas del sistema'),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaResumenGlobal(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        usuarios_por_rol = dict(
            User.objects.values_list('role__name').annotate(total=Count('id')).order_by()
        )

        sesiones = SesionExamen.objects.aggregate(
            en_progreso=Count('id', filter=Q(estado='en_progreso')),
            completadas=Count('id', filter=Q(estado='completado')),
        )

        rendimiento = Resultado.objects.aggregate(
            nota_promedio=Avg('nota'),
            total=Count('id'),
            aprobados=Count('id', filter=Q(nota__gte=3.0)),
        )
        total_resultados = rendimiento['total'] or 0
        tasa_aprobados = (
            round((rendimiento['aprobados'] or 0) / total_resultados * 100, 1)
            if total_resultados else 0.0
        )

        cursos_recientes = [
            {
                'id': c.id,
                'nombre': c.nombre,
                'docente': f"{c.docente.first_name} {c.docente.first_last_name}".strip(),
                'creado_en': c.creado_en,
            }
            for c in Curso.objects.select_related('docente').order_by('-creado_en')[:5]
        ]

        examenes_recientes = [
            {
                'id': e.id,
                'titulo': e.titulo,
                'curso': e.curso.nombre,
                'creado_en': e.creado_en,
            }
            for e in Examen.objects.select_related('curso').order_by('-creado_en')[:5]
        ]

        resultados_recientes = [
            {
                'estudiante': f"{r.estudiante.first_name} {r.estudiante.first_last_name}".strip(),
                'examen': r.examen.titulo,
                'nota': r.nota,
                'completado_en': r.completado_en,
            }
            for r in Resultado.objects.select_related('estudiante', 'examen').order_by('-completado_en')[:5]
        ]

        return Response({
            'usuarios_por_rol': {
                'administrador': usuarios_por_rol.get('Administrador', 0),
                'docente': usuarios_por_rol.get('Docente', 0),
                'estudiante': usuarios_por_rol.get('Estudiante', 0),
            },
            'total_cursos': Curso.objects.count(),
            'total_examenes': Examen.objects.count(),
            'sesiones_en_progreso': sesiones['en_progreso'] or 0,
            'sesiones_completadas': sesiones['completadas'] or 0,
            'nota_promedio_global': round(rendimiento['nota_promedio'] or 1.0, 1),
            'tasa_aprobados_global': tasa_aprobados,
            'cursos_recientes': cursos_recientes,
            'examenes_recientes': examenes_recientes,
            'resultados_recientes': resultados_recientes,
        })
