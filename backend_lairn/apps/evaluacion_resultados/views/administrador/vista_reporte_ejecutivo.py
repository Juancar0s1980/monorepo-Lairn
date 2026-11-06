"""
Reporte ejecutivo institucional (HU-11) con analítica de RA (ADR-011) y capa
interpretativa (ADR-015). Solo lectura para Vicerrector, Administrador y Coordinador.

- `GET reporte-ejecutivo/`                    indicadores + desglose (institución/programa) + `analitica`
- `GET reporte-ejecutivo/?programa=<id>&…`    filtros: programa, semestre, momento, desde, hasta,
                                              asignatura, docente, competencia, resultado, evaluacion
- `GET reporte-ejecutivo/opciones/`           valores de los filtros (?programa=&semestre=)
- `GET reporte-ejecutivo/exportar/?formato=pdf|xlsx&…` mismos filtros, mismas cifras (HU-11.3)
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.evaluacion_resultados.services.servicio_analitica_ra import (
    analitica,
    cerrar_vencidos,
    leer_filtros,
    notas,
    observaciones,
    opciones,
)
from apps.evaluacion_resultados.services.servicio_exportar_reporte import a_excel, a_pdf
from apps.evaluacion_resultados.services.servicio_reporte_ejecutivo import reporte
from core.permissions.permisos_rol import EsLectorAnalitica

TIPOS = {
    'pdf': ('application/pdf', a_pdf),
    'xlsx': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', a_excel),
}


def _datos(request):
    """Lanza ValueError si un filtro es inválido."""
    filtros = leer_filtros(request.query_params)
    programa = get_object_or_404(ProgramaAcademico, pk=filtros.programa) if filtros.programa else None
    cerrar_vencidos()
    # Una sola pasada de observaciones alimenta notas, indicadores y analítica.
    obs = observaciones(filtros)
    datos = reporte(programa, filtros, notas(filtros, obs))
    datos['analitica'] = analitica(filtros, obs)
    return datos


class VistaReporteEjecutivo(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        try:
            return Response(_datos(request))
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)


class VistaOpcionesReporte(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        programa = request.query_params.get('programa', '')
        semestre = request.query_params.get('semestre', '')
        return Response(opciones(
            int(programa) if programa.isdigit() else None, int(semestre) if semestre.isdigit() else None,
        ))


class VistaExportarReporte(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        formato = request.query_params.get('formato', 'pdf')
        if formato not in TIPOS:
            return Response({'formato': ['Usa pdf o xlsx.']}, status=400)
        try:
            datos = _datos(request)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        tipo_contenido, generar = TIPOS[formato]
        sufijo = datos['programa']['codigo'] if datos['nivel'] == 'programa' else 'institucional'
        respuesta = HttpResponse(generar(datos), content_type=tipo_contenido)
        respuesta['Content-Disposition'] = (
            f'attachment; filename="reporte_{sufijo}_{timezone.localdate():%Y%m%d}.{formato}"'
        )
        return respuesta


class VistaCatalogoIndicadores(APIView):
    """Fichas técnicas de los indicadores y los indicadores oficiales no disponibles (ADR-015)."""

    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        from apps.evaluacion_resultados.services.servicio_indicadores import NO_DISPONIBLES, catalogo
        return Response({'indicadores': catalogo(), 'no_disponibles': NO_DISPONIBLES})
