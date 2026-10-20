"""
Tablero académico resumido (HU-02.3 + base HU-09.1).

Solo lectura, solo Administrador. Agrega conteos por programa para
la vista `/academico` sin exponer PII (nunca lista documentos).
"""

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import ProgramaAcademico
from core.permissions.permisos_rol import EsAdministrador


class VistaTableroPrograma(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request, programa_id):
        programa = get_object_or_404(ProgramaAcademico, pk=programa_id)
        momentos = programa.momentos.filter(activo=True).prefetch_related(
            'vinculos__resultado',
        )
        detalle = []
        for momento in momentos:
            ras = [
                {
                    'id': v.resultado_id,
                    'descripcion': v.resultado.descripcion,
                    'obligatorio': v.obligatorio,
                }
                for v in momento.vinculos.all() if v.resultado.activo
            ]
            detalle.append({
                'momento_id': momento.id,
                'nombre': momento.nombre,
                'semestre': momento.semestre_referencia,
                'total_ras': len(ras),
                'ras': ras,
            })
        return Response({
            'programa': {'id': programa.id, 'codigo': programa.codigo, 'nombre': programa.nombre},
            'totales': {
                'semestres': programa.semestres.filter(activo=True).count(),
                'asignaturas': programa.asignaturas.filter(activo=True).count(),
                'competencias': programa.competencias.filter(activo=True).count(),
                'momentos': momentos.count(),
            },
            'momentos': detalle,
        })
