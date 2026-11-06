"""
Supervisión en sala, seguimiento en vivo y convocatoria masiva (ADR-009),
para Coordinador y Administrador.

- `GET    supervisores-disponibles/`                         docentes con al menos un curso
- `PATCH  evaluaciones/<id>/supervisor/`                     {supervisor: id | null}
- `GET    evaluaciones/<id>/seguimiento/`                    conteos + filas por convocado (con nota)
- `POST   evaluaciones/<id>/convocados/cargue/`              CSV/Excel o {correos}|{filas}; `confirmar` aplica
                                                           (vista previa con datos del archivo vs. cuenta, ADR-012)
- `DELETE evaluaciones/<id>/convocados/<estudiante_id>/`     quita un convocado por cargue sin intento
- `POST   evaluaciones/<id>/intentos/<estudiante>/resolver/` decide un intento suspendido (ADR-010),
                                                           solo si la evaluación NO tiene supervisor

Asignar supervisor se permite aunque la evaluación esté publicada (no pasa
por el 409 del detalle) mientras no haya pasado `fecha_fin`.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    ConvocadoEvaluacion,
    EvaluacionFormal,
    IntentoEvaluacion,
    OpcionesTipoEvaluacion,
)
from apps.evaluacion_resultados.services.servicio_integridad import ErrorIntegridad, resolver
from apps.evaluacion_resultados.serializers.serializador_evaluacion_formal import SerializadorEvaluacionFormal
from apps.evaluacion_resultados.services.servicio_supervision import (
    MAX_FILAS_CARGUE,
    ErrorSupervision,
    analizar_cargue,
    confirmar_cargue,
    filas_desde_archivo,
    docentes_con_cursos,
    es_docente_con_cursos,
    nombre_completo,
    seguimiento,
)
from core.permissions.permisos_rol import EsGestorAcademico


def _evaluacion(pk):
    return get_object_or_404(
        EvaluacionFormal.objects.select_related('momento__programa', 'supervisor'), pk=pk,
    )


def filas_de_peticion(request):
    """Filas del cargue: archivo (multipart) o JSON `filas` [{correo, ...}] / `correos` [str]. None si no hay."""
    archivo = request.FILES.get('archivo')
    if archivo is not None:
        return filas_desde_archivo(archivo)
    filas = request.data.get('filas', request.data.get('correos'))
    if not isinstance(filas, list):
        return None
    if len(filas) > MAX_FILAS_CARGUE:
        raise ErrorSupervision(f'El cargue admite máximo {MAX_FILAS_CARGUE} filas.')
    return filas


def _es_verdadero(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {'1', 'true', 'si', 'sí', 'yes'}


class VistaSupervisoresDisponibles(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        return Response([
            {'id': d.id, 'nombre': nombre_completo(d), 'email': d.email, 'total_cursos': d.total_cursos}
            for d in docentes_con_cursos()
        ])


class VistaAsignarSupervisor(APIView):
    permission_classes = [EsGestorAcademico]

    def patch(self, request, pk):
        evaluacion = _evaluacion(pk)
        if 'supervisor' not in request.data:
            return Response({'supervisor': ['Indica el docente supervisor o null para quitarlo.']}, status=400)
        supervisor_id = request.data.get('supervisor')
        if evaluacion.tipo != OpcionesTipoEvaluacion.CUESTIONARIO:
            return Response({'detalle': 'Solo las evaluaciones tipo cuestionario se presentan en sala con supervisor.'}, status=400)
        if evaluacion.fecha_fin <= timezone.now():
            return Response({'detalle': 'La evaluación ya cerró: no se puede cambiar el supervisor.'}, status=400)
        if supervisor_id in (None, ''):
            evaluacion.supervisor = None
        else:
            if isinstance(supervisor_id, bool) or not str(supervisor_id).isdigit() \
                    or not es_docente_con_cursos(int(supervisor_id)):
                return Response({'supervisor': ['El supervisor debe ser un docente con al menos un curso creado.']}, status=400)
            evaluacion.supervisor_id = int(supervisor_id)
        evaluacion.save(update_fields=['supervisor', 'actualizado_en'])
        evaluacion = _evaluacion(pk)
        return Response(SerializadorEvaluacionFormal(evaluacion).data)


class VistaSeguimientoEvaluacion(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request, pk):
        return Response(seguimiento(_evaluacion(pk), con_nota=True))


class VistaCargueConvocados(APIView):
    permission_classes = [EsGestorAcademico]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        evaluacion = _evaluacion(pk)
        if evaluacion.fecha_fin <= timezone.now():
            return Response({'detalle': 'La evaluación ya cerró: no se pueden agregar convocados.'}, status=400)
        try:
            filas = filas_de_peticion(request)
            if filas is None:
                return Response({'detalle': 'Sube un archivo .csv o .xlsx, o envía la lista "correos" o "filas".'}, status=400)
            informe = analizar_cargue(evaluacion, filas)
        except ErrorSupervision as error:
            return Response({'detalle': error.mensaje}, status=error.status)
        confirmar = _es_verdadero(request.data.get('confirmar', False))
        informe['confirmado'] = confirmar
        informe['agregados'] = confirmar_cargue(evaluacion, informe, request.user) if confirmar else 0
        return Response(informe, status=201 if confirmar else 200)


class VistaQuitarConvocado(APIView):
    permission_classes = [EsGestorAcademico]

    def delete(self, request, pk, estudiante_id):
        evaluacion = _evaluacion(pk)
        convocado = get_object_or_404(ConvocadoEvaluacion, evaluacion=evaluacion, estudiante_id=estudiante_id)
        if evaluacion.intentos.filter(estudiante_id=estudiante_id).exists():
            return Response({'detalle': 'El estudiante ya inició la evaluación: no se puede quitar.'}, status=409)
        convocado.delete()
        return Response(status=204)


def _respuesta_resolucion(evaluacion, estudiante_id, request):
    """Resuelve (reactivar | anular) el intento suspendido de un estudiante de la evaluación."""
    intento = get_object_or_404(IntentoEvaluacion, evaluacion=evaluacion, estudiante_id=estudiante_id)
    try:
        intento = resolver(intento, request.data.get('accion'), request.data.get('motivo'), request.user)
    except ErrorIntegridad as error:
        return Response({'detalle': error.mensaje}, status=error.status)
    return Response({
        'estudiante': intento.estudiante_id, 'integridad': intento.integridad, 'vence_en': intento.vence_en,
        'resuelto_en': intento.resuelto_en, 'motivo': intento.motivo_resolucion,
    })


class VistaResolverIntegridadGestor(APIView):
    """Coordinador/Administrador deciden solo si la evaluación no tiene supervisor (el docente decide)."""

    permission_classes = [EsGestorAcademico]

    def post(self, request, pk, estudiante_id):
        evaluacion = _evaluacion(pk)
        if evaluacion.supervisor_id:
            return Response(
                {'detalle': f'La decisión corresponde al docente supervisor ({nombre_completo(evaluacion.supervisor)}).'},
                status=409,
            )
        return _respuesta_resolucion(evaluacion, estudiante_id, request)
