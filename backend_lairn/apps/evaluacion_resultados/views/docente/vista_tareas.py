"""
Tareas prácticas del docente (HU-08B.1 a 08B.5).

Mismo alcance que el banco: solo asignaturas cuyo curso vinculado es del
docente; lo ajeno responde 404.

- `GET/POST docente/tareas/?asignatura=`        listar / crear borrador manual
- `POST docente/tareas/generar/`                borrador con IA desde un RA
- `GET/PATCH/DELETE docente/tareas/<id>/`       editar o borrar solo en borrador
- `POST/DELETE docente/tareas/<id>/archivos/[<aid>/]`  archivos guía (borrador)
- `POST docente/tareas/<id>/publicar/`          exige rúbrica válida, formatos y plazo futuro
- `GET docente/tareas/<id>/entregas/`           panel: inscritos con su estado
- `GET docente/entregas/<id>/archivo/`          descarga del archivo entregado
- `POST docente/entregas/<id>/calificar/`       niveles por criterio -> nota ponderada
"""

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    ArchivoGuiaTarea,
    EntregaTarea,
    OpcionesEstadoTarea,
    ResultadoAprendizaje,
    TareaPractica,
)
from apps.evaluacion_resultados.serializers.serializador_tarea import (
    SerializadorCalificar,
    SerializadorTarea,
    fila_entrega_docente,
)
from apps.evaluacion_resultados.services.agente_preguntas_banco import ErrorGeneracion
from apps.evaluacion_resultados.services.agente_tareas import generar_tarea
from apps.evaluacion_resultados.services.servicio_tareas import (
    EXTENSIONES_GUIA,
    TAMANO_MAX_GUIA,
    ErrorRubrica,
    calcular_nota,
    estudiantes_de_tarea,
    extension,
    rubrica_desde_resultado,
    validar_formatos,
    validar_rubrica,
)
from core.permissions.permisos_rol import EsDocente
from core.throttling import ThrottleIA

from .vista_banco_preguntas import asignaturas_del_docente

MENSAJE_PUBLICADA = 'La tarea ya fue publicada y no se puede modificar.'


def tareas_del_docente(usuario):
    return TareaPractica.objects.filter(
        asignatura__in=asignaturas_del_docente(usuario),
    ).select_related('asignatura__curso_vinculado', 'resultado').prefetch_related('archivos_guia')


def _resultado_de(asignatura, resultado_id):
    return ResultadoAprendizaje.objects.filter(pk=resultado_id, asignatura=asignatura, activo=True).first()


class VistaListaCrearTareas(generics.ListCreateAPIView):
    permission_classes = [EsDocente]
    serializer_class = SerializadorTarea

    def get_queryset(self):
        qs = tareas_del_docente(self.request.user)
        asignatura = self.request.query_params.get('asignatura')
        return qs.filter(asignatura_id=asignatura) if asignatura and asignatura.isdigit() else qs

    def create(self, request, *args, **kwargs):
        asignatura = get_object_or_404(asignaturas_del_docente(request.user), pk=request.data.get('asignatura'))
        resultado = _resultado_de(asignatura, request.data.get('resultado'))
        if resultado is None:
            return Response({'resultado': ['Elige un resultado de aprendizaje de la asignatura.']}, status=400)
        datos = dict(request.data)
        # Sin rúbrica propia, se parte de la del RA (HU-08B.2: crear o asociar).
        if not datos.get('rubrica'):
            datos['rubrica'] = rubrica_desde_resultado(resultado)
        serial = self.get_serializer(data=datos)
        serial.is_valid(raise_exception=True)
        tarea = serial.save(asignatura=asignatura, resultado=resultado, creado_por=request.user, origen='manual')
        return Response(self.get_serializer(tarea).data, status=201)


class VistaGenerarTarea(APIView):
    permission_classes = [EsDocente]
    throttle_classes = [ThrottleIA]
    throttle_scope = 'ia'

    def post(self, request):
        asignatura = get_object_or_404(asignaturas_del_docente(request.user), pk=request.data.get('asignatura'))
        resultado = _resultado_de(asignatura, request.data.get('resultado'))
        if resultado is None:
            return Response({'resultado': ['Elige un resultado de aprendizaje de la asignatura.']}, status=400)
        fecha_limite = request.data.get('fecha_limite')
        if not fecha_limite:
            return Response({'fecha_limite': ['Indica la fecha límite de entrega.']}, status=400)
        try:
            formatos = validar_formatos(request.data.get('formatos_permitidos') or ['pdf'])
        except ValueError as exc:
            return Response({'formatos_permitidos': [str(exc)]}, status=400)
        try:
            # La IA conoce los formatos para no pedir un entregable que no se puede subir.
            borrador = generar_tarea(asignatura, resultado, formatos)
        except ErrorGeneracion as exc:
            return Response({'detalle': str(exc)}, status=502)
        serial = SerializadorTarea(data={
            'resultado': resultado.id, 'titulo': borrador['titulo'], 'descripcion': borrador['descripcion'],
            'rubrica': borrador['rubrica'], 'fecha_limite': fecha_limite,
            'formatos_permitidos': formatos,
            'permite_tardias': bool(request.data.get('permite_tardias', False)),
        })
        serial.is_valid(raise_exception=True)
        tarea = serial.save(asignatura=asignatura, resultado=resultado, creado_por=request.user, origen='ia')
        return Response(SerializadorTarea(tarea).data, status=201)


class VistaDetalleTarea(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [EsDocente]
    serializer_class = SerializadorTarea
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return tareas_del_docente(self.request.user)

    def update(self, request, *args, **kwargs):
        tarea = self.get_object()
        if tarea.estado != OpcionesEstadoTarea.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        if 'resultado' in request.data and _resultado_de(tarea.asignatura, request.data['resultado']) is None:
            return Response({'resultado': ['Elige un resultado de aprendizaje de la asignatura.']}, status=400)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        tarea = self.get_object()
        if tarea.estado != OpcionesEstadoTarea.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        for archivo in tarea.archivos_guia.all():
            archivo.archivo.delete(save=False)
        return super().destroy(request, *args, **kwargs)


class VistaArchivosGuia(APIView):
    permission_classes = [EsDocente]
    parser_classes = [MultiPartParser]

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_del_docente(request.user), pk=pk)
        if tarea.estado != OpcionesEstadoTarea.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        archivo = request.FILES.get('archivo')
        if archivo is None:
            return Response({'archivo': ['Selecciona un archivo.']}, status=400)
        if extension(archivo.name) not in EXTENSIONES_GUIA:
            return Response({'archivo': [f'Formato no permitido. Usa: {", ".join(sorted(EXTENSIONES_GUIA))}.']}, status=400)
        if archivo.size > TAMANO_MAX_GUIA:
            return Response({'archivo': ['El archivo supera los 10 MB.']}, status=400)
        guia = ArchivoGuiaTarea.objects.create(
            tarea=tarea, archivo=archivo, nombre_original=archivo.name[:255], tamano=archivo.size,
        )
        return Response({'id': guia.id, 'nombre': guia.nombre_original, 'tamano': guia.tamano}, status=201)


class VistaDetalleArchivoGuia(APIView):
    permission_classes = [EsDocente]

    def get(self, request, pk, archivo_id):
        guia = get_object_or_404(ArchivoGuiaTarea, pk=archivo_id, tarea__in=tareas_del_docente(request.user), tarea_id=pk)
        return FileResponse(guia.archivo.open('rb'), as_attachment=True, filename=guia.nombre_original)

    def delete(self, request, pk, archivo_id):
        guia = get_object_or_404(ArchivoGuiaTarea, pk=archivo_id, tarea__in=tareas_del_docente(request.user), tarea_id=pk)
        if guia.tarea.estado != OpcionesEstadoTarea.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        guia.archivo.delete(save=False)
        guia.delete()
        return Response(status=204)


class VistaPublicarTarea(APIView):
    permission_classes = [EsDocente]

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_del_docente(request.user), pk=pk)
        if tarea.estado != OpcionesEstadoTarea.BORRADOR:
            return Response({'detalle': MENSAJE_PUBLICADA}, status=409)
        try:
            validar_formatos(tarea.formatos_permitidos)
            validar_rubrica(tarea.rubrica)
        except (ValueError, ErrorRubrica) as exc:
            return Response({'detalle': str(exc)}, status=400)
        if tarea.fecha_limite <= timezone.now():
            return Response({'detalle': 'La fecha límite ya pasó: ajústala antes de publicar.'}, status=400)
        tarea.estado = OpcionesEstadoTarea.PUBLICADA
        tarea.publicada_en = timezone.now()
        tarea.save(update_fields=['estado', 'publicada_en', 'actualizado_en'])
        return Response(SerializadorTarea(tarea).data)


class VistaEntregasTarea(APIView):
    permission_classes = [EsDocente]

    def get(self, request, pk):
        tarea = get_object_or_404(tareas_del_docente(request.user), pk=pk)
        entregas = {e.estudiante_id: e for e in tarea.entregas.all()}
        return Response([fila_entrega_docente(est, entregas.get(est.id)) for est in estudiantes_de_tarea(tarea)])


def _entrega_del_docente(usuario, entrega_id):
    return get_object_or_404(
        EntregaTarea.objects.select_related('tarea'), pk=entrega_id, tarea__in=tareas_del_docente(usuario),
    )


class VistaArchivoEntregaDocente(APIView):
    permission_classes = [EsDocente]

    def get(self, request, entrega_id):
        entrega = _entrega_del_docente(request.user, entrega_id)
        return FileResponse(entrega.archivo.open('rb'), as_attachment=True, filename=entrega.nombre_original)


class VistaCalificarEntrega(APIView):
    permission_classes = [EsDocente]

    def post(self, request, entrega_id):
        entrega = _entrega_del_docente(request.user, entrega_id)
        serial = SerializadorCalificar(data=request.data)
        serial.is_valid(raise_exception=True)
        try:
            nota = calcular_nota(entrega.tarea.rubrica, serial.validated_data['niveles_elegidos'])
        except ValueError as exc:
            return Response({'niveles_elegidos': [str(exc)]}, status=400)
        entrega.niveles_elegidos = serial.validated_data['niveles_elegidos']
        entrega.nota = nota
        entrega.observaciones = serial.validated_data['observaciones']
        entrega.calificada_por = request.user
        entrega.calificada_en = timezone.now()
        entrega.save()
        estudiante = entrega.estudiante
        return Response(fila_entrega_docente(estudiante, entrega))
