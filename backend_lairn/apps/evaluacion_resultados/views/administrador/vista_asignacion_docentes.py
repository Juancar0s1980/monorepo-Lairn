"""
Asignación masiva de docentes a asignaturas (ADR-017).

- `GET  asignacion-docentes/plantilla/?programa=&formato=csv|xlsx`
    plantilla con las asignaturas activas del programa y su docente actual.
- `POST asignacion-docentes/analizar/` (multipart: archivo, programa)
    vista previa: estado por fila (valida, advertencia, ya_asignada, omitida,
    error), resumen y `huella`. No escribe nada.
- `POST asignacion-docentes/confirmar/` (JSON: programa, filas, huella)
    vuelve a validar contra la base actual y aplica todo o nada.

Permiso: el mismo de la asignación individual (editar la asignatura):
`EsGestorAcademico` (Administrador o Coordinador).
"""

import logging

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.evaluacion_resultados.services.servicio_asignacion_docentes import (
    COLUMNAS,
    ErrorAsignacion,
    aplicar,
    filas_desde_archivo,
    huella,
    planificar,
    plantilla_csv,
    plantilla_xlsx,
    publico,
)
from apps.evaluacion_resultados.services.servicio_trazabilidad import registrar_sincronizacion
from core.permissions.permisos_rol import EsGestorAcademico

MAX_ERRORES_REGISTRO = 50
logger = logging.getLogger(__name__)


def _programa(valor):
    if not str(valor or '').isdigit():
        return None
    return get_object_or_404(ProgramaAcademico, pk=int(valor))


class VistaPlantillaAsignacion(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        programa = _programa(request.query_params.get('programa'))
        if programa is None:
            return Response({'programa': ['Elige un programa.']}, status=400)
        formato = request.query_params.get('formato', 'xlsx')
        if formato not in ('csv', 'xlsx'):
            return Response({'formato': ['Usa csv o xlsx.']}, status=400)
        if formato == 'csv':
            contenido, tipo = plantilla_csv(programa), 'text/csv; charset=utf-8'
        else:
            contenido = plantilla_xlsx(programa)
            tipo = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        respuesta = HttpResponse(contenido, content_type=tipo)
        respuesta['Content-Disposition'] = (
            f'attachment; filename="asignacion_docentes_{programa.codigo}_{timezone.localdate():%Y%m%d}.{formato}"'
        )
        return respuesta


class VistaAnalizarAsignacion(APIView):
    permission_classes = [EsGestorAcademico]

    def post(self, request):
        programa = _programa(request.data.get('programa'))
        if programa is None:
            return Response({'programa': ['Elige un programa.']}, status=400)
        archivo = request.FILES.get('archivo')
        if archivo is None:
            return Response({'archivo': ['Adjunta un archivo .csv, .xlsx o .json.']}, status=400)
        try:
            filas = filas_desde_archivo(archivo)
        except ErrorAsignacion as error:
            return Response({'detalle': str(error)}, status=400)
        if not filas:
            return Response({'detalle': 'El archivo no tiene filas de datos.'}, status=400)
        plan = planificar(filas, programa)
        return Response({
            'programa': {'id': programa.id, 'codigo': programa.codigo, 'nombre': programa.nombre},
            'resumen': plan['resumen'], 'filas': publico(plan),
            'entrada': filas, 'huella': huella(filas),
        })


class VistaConfirmarAsignacion(APIView):
    permission_classes = [EsGestorAcademico]

    def post(self, request):
        programa = _programa(request.data.get('programa'))
        if programa is None:
            return Response({'programa': ['Elige un programa.']}, status=400)
        entrada = request.data.get('filas')
        if not isinstance(entrada, list) or not entrada:
            return Response({'filas': ['Faltan las filas analizadas.']}, status=400)
        filas = []
        for i, f in enumerate(entrada, start=1):
            if not isinstance(f, dict):
                return Response({'filas': ['Formato de filas inválido.']}, status=400)
            fila = {'fila': f.get('fila', i), **{c: str(f.get(c) or '').strip() for c in COLUMNAS}}
            if f.get('invalida'):
                fila['invalida'] = str(f['invalida'])
            filas.append(fila)
        if request.data.get('huella') != huella(filas):
            return Response({'detalle': 'Las filas cambiaron desde la vista previa. Vuelve a analizar el archivo.'},
                            status=409)
        plan = planificar(filas, programa)
        errores = [f"Fila {f['fila']}: {f['mensaje']}" for f in plan['filas'] if f['estado'] == 'error']
        try:
            # Asignaciones y registro de trazabilidad: todo o nada.
            with transaction.atomic():
                aplicadas = aplicar(plan)
                registro = registrar_sincronizacion(
                    origen='archivo_docentes', entidad='asignacion_docentes', modo='real',
                    total_recibidos=len(filas), creados=aplicadas['cursos_creados'],
                    actualizados=aplicadas['asignadas'], omitidos=len(filas) - aplicadas['asignadas'],
                    errores=errores[:MAX_ERRORES_REGISTRO], ejecutado_por=request.user,
                )
        except Exception:
            logger.exception('Fallo al aplicar la asignación masiva de docentes (programa=%s)', programa.id)
            return Response({'detalle': 'No se guardó ningún cambio: ocurrió un error al escribir en la base de '
                                        'datos. Intenta de nuevo.'}, status=500)
        return Response({
            'registro_id': registro.id,
            'programa': {'id': programa.id, 'codigo': programa.codigo, 'nombre': programa.nombre},
            'resumen': {**plan['resumen'], **aplicadas}, 'filas': publico(plan),
        })
