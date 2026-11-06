"""
Estudiantes convocados e inscritos (ADR-012).

- `GET  estudiantes/`           Administrador o Coordinador: listado paginado.
                                ?programa=&momento=&evaluacion=&estado=&buscar=&pagina=&tamano=
                                ?formato=csv|xlsx exporta TODAS las filas con los mismos filtros.
- `POST estudiantes/validar/`   solo Administrador: valida un archivo de estudiantes contra el
                                sistema (sin evaluación). Informa; no crea ni modifica cuentas.
- `GET  docente/estudiantes/`   Docente: solo sus cursos y las evaluaciones que supervisa.

El Vicerrector no ve listados nominales (solo consolidados en el reporte, ADR-011).
"""

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.services.servicio_estudiantes import (
    ESTADOS,
    alcance_docente,
    alcance_gestor,
    exportar,
    listado,
)
from apps.evaluacion_resultados.services.servicio_supervision import ErrorSupervision, analizar_cargue
from core.permissions.permisos_rol import EsAdministrador, EsDocente, EsGestorAcademico

TIPOS = {
    'csv': 'text/csv; charset=utf-8',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


def _entero(params, clave):
    valor = (params.get(clave) or '').strip()
    if not valor:
        return None
    if not valor.isdigit():
        raise ValueError(f'El filtro "{clave}" debe ser un número.')
    return int(valor)


def responder_listado(request, alcance):
    params = request.query_params
    estado = params.get('estado') or None
    if estado and estado not in ESTADOS:
        return Response({'detalle': 'Estado no válido.'}, status=400)
    formato = params.get('formato')
    if formato and formato not in TIPOS:
        return Response({'detalle': 'Usa csv o xlsx.'}, status=400)
    try:
        pagina, tamano = _entero(params, 'pagina') or 1, _entero(params, 'tamano')
    except ValueError as error:
        return Response({'detalle': str(error)}, status=400)
    datos = listado(alcance, estado=estado, buscar=params.get('buscar', ''), pagina=pagina, tamano=tamano,
                    paginar=not formato)
    if not formato:
        return Response(datos)
    respuesta = HttpResponse(exportar(datos, formato), content_type=TIPOS[formato])
    respuesta['Content-Disposition'] = f'attachment; filename="estudiantes_{timezone.localdate():%Y%m%d}.{formato}"'
    return respuesta


class VistaEstudiantesGestor(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        try:
            alcance = alcance_gestor(_entero(request.query_params, 'programa'),
                                     _entero(request.query_params, 'momento'),
                                     _entero(request.query_params, 'evaluacion'))
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        return responder_listado(request, alcance)


class VistaEstudiantesDocente(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        try:
            alcance = alcance_docente(request.user, _entero(request.query_params, 'evaluacion'))
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        return responder_listado(request, alcance)


class VistaValidarEstudiantes(APIView):
    """Validación global (Administrador): ¿existen estas cuentas y son de estudiante? Solo informa."""

    permission_classes = [EsAdministrador]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        from apps.evaluacion_resultados.views.administrador.vista_supervision import filas_de_peticion

        try:
            filas = filas_de_peticion(request)
            if filas is None:
                return Response({'detalle': 'Sube un archivo .csv o .xlsx, o envía la lista "correos" o "filas".'},
                                status=400)
            return Response(analizar_cargue(None, filas))
        except ErrorSupervision as error:
            return Response({'detalle': error.mensaje}, status=error.status)
