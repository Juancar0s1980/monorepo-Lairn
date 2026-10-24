"""
Banco de preguntas del docente (HU-04.1 a 04.5, HU-05.1 a 05.4).

Alcance por docente: solo las asignaturas cuyo `curso_vinculado` es un
curso suyo ("mi materia"). La coordinación hace ese vínculo en la malla.
Todo lo de otras asignaturas responde 404 (no se revela su existencia).

- `GET  docente/asignaturas/`             asignaturas + RA + competencias transversales
- `POST docente/banco/generar/`           IA crea borradores en estado pendiente
- `GET  docente/banco/?estado=&asignatura=&resultado=&competencia_transversal=`
- `GET/PATCH docente/banco/<id>/`         editar solo si está pendiente
- `POST docente/banco/<id>/aprobar/`      pendiente -> aprobada (banco oficial)
- `POST docente/banco/<id>/descartar/`    pendiente -> descartada
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    OpcionesEstadoPregunta,
    OpcionesOrigenPregunta,
    OpcionesTipoCompetencia,
    PreguntaBanco,
    ResultadoAprendizaje,
)
from apps.evaluacion_resultados.serializers.serializador_banco import (
    SerializadorDescartar,
    SerializadorEdicionPregunta,
    SerializadorGenerarPreguntas,
    SerializadorPreguntaBanco,
)
from apps.evaluacion_resultados.services.agente_preguntas_banco import (
    ErrorGeneracion,
    generar_preguntas,
)
from core.permissions.permisos_rol import EsDocente


def asignaturas_del_docente(usuario):
    return AsignaturaMalla.objects.filter(
        curso_vinculado__docente=usuario, activo=True,
    ).select_related('programa', 'curso_vinculado')


def preguntas_del_docente(usuario):
    return PreguntaBanco.objects.filter(
        asignatura__in=asignaturas_del_docente(usuario),
    ).select_related('asignatura', 'resultado__competencia', 'competencia_transversal')


class LimiteGeneracionIA(UserRateThrottle):
    """Cada generación consume el proveedor de IA (costo y cuota)."""

    scope = 'banco_generar'
    rate = '10/min'


class VistaMisAsignaturas(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        datos = []
        for a in asignaturas_del_docente(request.user):
            resultados = ResultadoAprendizaje.objects.filter(asignatura=a, activo=True).select_related('competencia')
            transversales = Competencia.objects.filter(
                programa=a.programa, tipo=OpcionesTipoCompetencia.TRANSVERSAL, activo=True,
            )
            datos.append({
                'id': a.id, 'codigo': a.codigo, 'nombre': a.nombre,
                'programa': {'id': a.programa_id, 'codigo': a.programa.codigo, 'nombre': a.programa.nombre},
                'curso': {'id': a.curso_vinculado_id, 'nombre': a.curso_vinculado.nombre},
                'resultados': [
                    {'id': r.id, 'descripcion': r.descripcion,
                     'competencia': {'id': r.competencia_id, 'nombre': r.competencia.nombre}}
                    for r in resultados
                ],
                'competencias_transversales': [{'id': c.id, 'nombre': c.nombre} for c in transversales],
            })
        return Response(datos)


class VistaGenerarPreguntas(APIView):
    permission_classes = [EsDocente]
    throttle_classes = [LimiteGeneracionIA]

    def post(self, request):
        serial = SerializadorGenerarPreguntas(data=request.data)
        serial.is_valid(raise_exception=True)
        d = serial.validated_data
        asignatura = get_object_or_404(asignaturas_del_docente(request.user), pk=d['asignatura'])
        resultado = ResultadoAprendizaje.objects.filter(
            pk=d['resultado'], asignatura=asignatura, activo=True,
        ).select_related('competencia').first()
        if resultado is None:
            return Response({'resultado': ['Ese resultado de aprendizaje no pertenece a la asignatura.']}, status=400)
        competencia = None
        if d.get('competencia_transversal'):
            competencia = Competencia.objects.filter(
                pk=d['competencia_transversal'], programa=asignatura.programa,
                tipo=OpcionesTipoCompetencia.TRANSVERSAL, activo=True,
            ).first()
            if competencia is None:
                return Response(
                    {'competencia_transversal': ['Elige una competencia transversal del programa.']}, status=400,
                )
        try:
            preguntas, meta = generar_preguntas(asignatura, resultado, competencia, d['cantidad'])
        except ErrorGeneracion as exc:
            return Response({'detalle': str(exc)}, status=502)
        with transaction.atomic():
            creadas = [
                PreguntaBanco.objects.create(
                    asignatura=asignatura, resultado=resultado, competencia_transversal=competencia,
                    origen=OpcionesOrigenPregunta.IA, estado=OpcionesEstadoPregunta.PENDIENTE,
                    datos_generacion=meta, creado_por=request.user, **p,
                )
                for p in preguntas
            ]
        return Response(SerializadorPreguntaBanco(creadas, many=True).data, status=201)


class VistaListaPreguntas(generics.ListAPIView):
    permission_classes = [EsDocente]
    serializer_class = SerializadorPreguntaBanco

    def get_queryset(self):
        qs = preguntas_del_docente(self.request.user)
        filtros = {
            'estado': 'estado', 'asignatura': 'asignatura_id', 'resultado': 'resultado_id',
            'competencia_transversal': 'competencia_transversal_id',
        }
        for parametro, campo in filtros.items():
            valor = self.request.query_params.get(parametro)
            if valor and (parametro == 'estado' or valor.isdigit()):
                qs = qs.filter(**{campo: valor})
        return qs


class VistaDetallePregunta(generics.RetrieveUpdateAPIView):
    permission_classes = [EsDocente]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return preguntas_del_docente(self.request.user)

    def get_serializer_class(self):
        return SerializadorEdicionPregunta if self.request.method == 'PATCH' else SerializadorPreguntaBanco

    def update(self, request, *args, **kwargs):
        pregunta = self.get_object()
        if pregunta.estado != OpcionesEstadoPregunta.PENDIENTE:
            return Response(
                {'detalle': 'Solo se pueden editar preguntas pendientes de validación.'}, status=409,
            )
        serial = SerializadorEdicionPregunta(pregunta, data=request.data, partial=True)
        serial.is_valid(raise_exception=True)
        serial.save()
        return Response(SerializadorPreguntaBanco(pregunta).data)


class _VistaCambioEstado(APIView):
    permission_classes = [EsDocente]

    def _pendiente(self, request, pk):
        pregunta = get_object_or_404(preguntas_del_docente(request.user), pk=pk)
        if pregunta.estado != OpcionesEstadoPregunta.PENDIENTE:
            return pregunta, Response({'detalle': 'La pregunta ya fue revisada.'}, status=409)
        return pregunta, None


class VistaAprobarPregunta(_VistaCambioEstado):
    def post(self, request, pk):
        pregunta, error = self._pendiente(request, pk)
        if error:
            return error
        # Revalida el contenido: una pregunta incompleta no entra al banco oficial.
        revision = SerializadorEdicionPregunta(pregunta, data={
            'enunciado': pregunta.enunciado, 'opciones': pregunta.opciones,
            'respuesta_correcta': pregunta.respuesta_correcta,
        }, partial=True)
        revision.is_valid(raise_exception=True)
        pregunta.estado = OpcionesEstadoPregunta.APROBADA
        pregunta.revisado_por = request.user
        pregunta.revisado_en = timezone.now()
        pregunta.save(update_fields=['estado', 'revisado_por', 'revisado_en', 'actualizado_en'])
        return Response(SerializadorPreguntaBanco(pregunta).data)


class VistaDescartarPregunta(_VistaCambioEstado):
    def post(self, request, pk):
        pregunta, error = self._pendiente(request, pk)
        if error:
            return error
        serial = SerializadorDescartar(data=request.data)
        serial.is_valid(raise_exception=True)
        pregunta.estado = OpcionesEstadoPregunta.DESCARTADA
        pregunta.motivo_descarte = serial.validated_data['motivo']
        pregunta.revisado_por = request.user
        pregunta.revisado_en = timezone.now()
        pregunta.save(update_fields=['estado', 'motivo_descarte', 'revisado_por', 'revisado_en', 'actualizado_en'])
        return Response(SerializadorPreguntaBanco(pregunta).data)
