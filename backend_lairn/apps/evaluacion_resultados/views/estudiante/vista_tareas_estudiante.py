"""
Tareas del estudiante (HU-08A.1 a 08A.4).

Ve solo tareas PUBLICADAS de asignaturas cuyo curso vinculado tiene
inscrito al estudiante. El envío es definitivo y único (sin borradores):
se registra con fecha y hora exactas y se marca "con retraso" si llega
después del plazo y el docente lo permite; si no lo permite, se rechaza.

- `GET estudiante/tareas/`                         mis tareas con su estado
- `GET estudiante/tareas/<id>/`                    detalle, rúbrica, guías y mi entrega
- `GET estudiante/tareas/<id>/archivos/<aid>/`     descargar archivo guía
- `POST estudiante/tareas/<id>/entregar/`          envío definitivo (multipart `archivo`)
- `GET estudiante/entregas/<id>/archivo/`          descargar mi propio archivo
"""

from django.db import IntegrityError, transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    ArchivoGuiaTarea,
    EntregaTarea,
    OpcionesEstadoTarea,
    TareaPractica,
)
from apps.evaluacion_resultados.serializers.serializador_tarea import SerializadorTareaEstudiante
from apps.evaluacion_resultados.services.servicio_tareas import (
    TAMANO_MAX_ENTREGA,
    estado_plazo,
    extension,
    extensiones_permitidas,
)
from core.permissions.permisos_rol import EsEstudiante


def tareas_del_estudiante(usuario):
    return TareaPractica.objects.filter(
        estado=OpcionesEstadoTarea.PUBLICADA,
        asignatura__curso_vinculado__inscripciones__estudiante=usuario,
    ).select_related('asignatura', 'resultado').prefetch_related('archivos_guia').distinct()


class VistaMisTareas(generics.ListAPIView):
    permission_classes = [EsEstudiante]
    serializer_class = SerializadorTareaEstudiante

    def get_queryset(self):
        return tareas_del_estudiante(self.request.user).order_by('fecha_limite')


class VistaDetalleMiTarea(generics.RetrieveAPIView):
    permission_classes = [EsEstudiante]
    serializer_class = SerializadorTareaEstudiante

    def get_queryset(self):
        return tareas_del_estudiante(self.request.user)


class VistaArchivoGuiaEstudiante(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, pk, archivo_id):
        guia = get_object_or_404(
            ArchivoGuiaTarea, pk=archivo_id, tarea_id=pk, tarea__in=tareas_del_estudiante(request.user),
        )
        return FileResponse(guia.archivo.open('rb'), as_attachment=True, filename=guia.nombre_original)


class VistaEntregarTarea(APIView):
    permission_classes = [EsEstudiante]
    parser_classes = [MultiPartParser]

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_del_estudiante(request.user), pk=pk)
        if EntregaTarea.objects.filter(tarea=tarea, estudiante=request.user).exists():
            return Response({'detalle': 'Ya enviaste esta tarea. El envío es definitivo.'}, status=409)
        plazo = estado_plazo(tarea)
        if plazo == 'cerrada':
            return Response({'detalle': 'El plazo terminó y el docente no acepta entregas tardías.'}, status=400)
        archivo = request.FILES.get('archivo')
        if archivo is None:
            return Response({'archivo': ['Adjunta el archivo de tu entrega.']}, status=400)
        permitidas = extensiones_permitidas(tarea.formatos_permitidos)
        if extension(archivo.name) not in permitidas:
            return Response({'archivo': [f'Formato no permitido. Usa: {", ".join(sorted(permitidas))}.']}, status=400)
        if archivo.size > TAMANO_MAX_ENTREGA:
            return Response({'archivo': ['El archivo supera los 20 MB.']}, status=400)
        try:
            with transaction.atomic():
                EntregaTarea.objects.create(
                    tarea=tarea, estudiante=request.user, archivo=archivo,
                    nombre_original=archivo.name[:255], tamano=archivo.size, con_retraso=(plazo == 'tardia'),
                )
        except IntegrityError:
            # Doble clic o dos pestañas: la restricción única garantiza un solo envío.
            return Response({'detalle': 'Ya enviaste esta tarea. El envío es definitivo.'}, status=409)
        return Response(SerializadorTareaEstudiante(tarea, context={'request': request}).data, status=201)


class VistaArchivoMiEntrega(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, entrega_id):
        entrega = get_object_or_404(EntregaTarea, pk=entrega_id, estudiante=request.user)
        return FileResponse(entrega.archivo.open('rb'), as_attachment=True, filename=entrega.nombre_original)
