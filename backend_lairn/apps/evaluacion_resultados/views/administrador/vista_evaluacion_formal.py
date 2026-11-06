"""
Ensamblado de evaluaciones formales por momento (HU-06), para
Administrador y Coordinador.

- `GET/POST momentos/<id>/evaluaciones/`        listar / crear (borrador)
- `GET momentos/<id>/banco-elegible/`           RA del momento + preguntas aprobadas elegibles
- `GET/PATCH/DELETE evaluaciones/<id>/`          editar o borrar solo en borrador
- `PUT evaluaciones/<id>/preguntas/`             fijar la selección (orden = orden enviado)
- `POST evaluaciones/<id>/publicar/`             congelar para presentación (HU-07)
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    EvaluacionFormal,
    EvaluacionPregunta,
    MomentoEvaluacion,
    OpcionesEstadoEvaluacion,
    OpcionesTipoEvaluacion,
)
from apps.evaluacion_resultados.serializers.serializador_banco import SerializadorPreguntaBanco
from apps.evaluacion_resultados.serializers.serializador_evaluacion_formal import (
    SerializadorEvaluacionFormal,
    SerializadorSeleccionPreguntas,
)
from apps.evaluacion_resultados.services.servicio_evaluacion_formal import (
    preguntas_elegibles,
    tareas_elegibles,
    vinculos_activos,
)
from core.permissions.permisos_rol import EsGestorAcademico

MENSAJE_PUBLICADA = 'La evaluación ya fue publicada y no se puede modificar.'


def _momento_activo(momento_id):
    return get_object_or_404(MomentoEvaluacion, pk=momento_id, activo=True)


class VistaListaCrearEvaluaciones(generics.ListCreateAPIView):
    permission_classes = [EsGestorAcademico]
    serializer_class = SerializadorEvaluacionFormal

    def get_queryset(self):
        return EvaluacionFormal.objects.filter(momento=_momento_activo(self.kwargs['momento_id']))

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if 'momento_id' in self.kwargs:
            contexto['momento'] = _momento_activo(self.kwargs['momento_id'])
        return contexto

    def perform_create(self, serializer):
        serializer.save(momento=_momento_activo(self.kwargs['momento_id']), creado_por=self.request.user)


class VistaBancoElegible(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request, momento_id):
        momento = _momento_activo(momento_id)
        elegibles, excluidas = preguntas_elegibles(momento)
        por_ra = {}
        for p in elegibles:
            por_ra.setdefault(p.resultado_id, []).append(p)
        return Response({
            'momento': {'id': momento.id, 'nombre': momento.nombre, 'semestre': momento.semestre_referencia},
            'excluidas_por_laboratorio': excluidas,
            'tareas': [
                {'id': t.id, 'titulo': t.titulo, 'fecha_limite': t.fecha_limite,
                 'asignatura': t.asignatura.codigo, 'resultado_id': t.resultado_id}
                for t in tareas_elegibles(momento)
            ],
            'resultados': [
                {
                    'resultado': {
                        'id': v.resultado_id, 'descripcion': v.resultado.descripcion,
                        'competencia': v.resultado.competencia.nombre,
                    },
                    'obligatorio': v.obligatorio,
                    'preguntas': SerializadorPreguntaBanco(por_ra.get(v.resultado_id, []), many=True).data,
                }
                for v in vinculos_activos(momento)
            ],
        })


class VistaDetalleEvaluacion(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [EsGestorAcademico]
    serializer_class = SerializadorEvaluacionFormal
    queryset = EvaluacionFormal.objects.select_related('momento')
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def update(self, request, *args, **kwargs):
        if self.get_object().estado != OpcionesEstadoEvaluacion.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if self.get_object().estado != OpcionesEstadoEvaluacion.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        return super().destroy(request, *args, **kwargs)


class VistaSeleccionPreguntas(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request, pk):
        evaluacion = get_object_or_404(EvaluacionFormal, pk=pk)
        preguntas = [i.pregunta for i in evaluacion.items.select_related(
            'pregunta__asignatura', 'pregunta__resultado__competencia', 'pregunta__competencia_transversal',
        )]
        return Response(SerializadorPreguntaBanco(preguntas, many=True).data)

    def put(self, request, pk):
        evaluacion = get_object_or_404(EvaluacionFormal.objects.select_related('momento'), pk=pk)
        if evaluacion.estado != OpcionesEstadoEvaluacion.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        if evaluacion.tipo == OpcionesTipoEvaluacion.TAREA and request.data.get('preguntas'):
            return Response({'preguntas': ['Una evaluación por tarea no lleva preguntas del banco.']}, status=400)
        serial = SerializadorSeleccionPreguntas(data=request.data)
        serial.is_valid(raise_exception=True)
        ids = serial.validated_data['preguntas']
        elegibles = {p.id for p in preguntas_elegibles(evaluacion.momento)[0]}
        invalidas = [i for i in ids if i not in elegibles]
        if invalidas:
            return Response(
                {'preguntas': ['Solo se pueden usar preguntas aprobadas de los RA del momento '
                               'que no estén en el laboratorio de práctica.']},
                status=400,
            )
        with transaction.atomic():
            evaluacion.items.all().delete()
            EvaluacionPregunta.objects.bulk_create([
                EvaluacionPregunta(evaluacion=evaluacion, pregunta_id=pid, orden=i) for i, pid in enumerate(ids)
            ])
        return Response(SerializadorEvaluacionFormal(evaluacion).data)


class VistaPublicarEvaluacion(APIView):
    permission_classes = [EsGestorAcademico]

    def post(self, request, pk):
        evaluacion = get_object_or_404(EvaluacionFormal, pk=pk)
        if evaluacion.estado != OpcionesEstadoEvaluacion.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        if evaluacion.tipo == OpcionesTipoEvaluacion.TAREA:
            if evaluacion.tarea is None:
                return Response({'detalle': 'Elige la tarea que se evaluará antes de publicar.'}, status=400)
        elif not evaluacion.items.exists():
            return Response({'detalle': 'Selecciona al menos una pregunta antes de publicar.'}, status=400)
        if evaluacion.fecha_fin <= timezone.now():
            return Response({'detalle': 'La fecha de cierre ya pasó: ajústala antes de publicar.'}, status=400)
        evaluacion.estado = OpcionesEstadoEvaluacion.PUBLICADA
        evaluacion.publicada_en = timezone.now()
        evaluacion.save(update_fields=['estado', 'publicada_en', 'actualizado_en'])
        return Response(SerializadorEvaluacionFormal(evaluacion).data)
