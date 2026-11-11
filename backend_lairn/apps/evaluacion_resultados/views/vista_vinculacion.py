"""
Solicitudes de vinculación curso ↔ asignatura de la malla (HU-01.10).

Docente (solo sus cursos):
- `GET  vinculacion/opciones/`                      programas activos con sus asignaturas y el vínculo actual
- `GET  docente/cursos/<curso_id>/vinculacion/`     asignaturas vinculadas al curso y sus solicitudes
- `POST docente/cursos/<curso_id>/vinculacion/`     pedir el vínculo (asignatura, mensaje)
- `POST vinculacion/solicitudes/<id>/cancelar/`     cancelar una solicitud propia pendiente

Administrador y Coordinador:
- `GET  vinculacion/solicitudes/?estado=`           bandeja de solicitudes (por defecto pendientes)
- `POST vinculacion/solicitudes/<id>/aprobar/`      vincula la asignatura al curso
- `POST vinculacion/solicitudes/<id>/rechazar/`     rechaza con motivo obligatorio
"""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    OpcionesEstadoSolicitud,
    SolicitudVinculacion,
)
from apps.examenes.models import Curso
from core.permissions.permisos_rol import EsDocente, EsGestorAcademico


def _nombre(u):
    return f'{u.first_name} {u.first_last_name}'.strip() or u.email if u else ''


def _vinculo(asig):
    c = asig.curso_vinculado
    if c is None:
        return None
    return {'id': c.id, 'nombre': c.nombre, 'docente': _nombre(c.docente), 'docente_email': c.docente.email}


def _asignatura(a):
    return {'id': a.id, 'codigo': a.codigo, 'nombre': a.nombre,
            'semestre': a.semestre.numero if a.semestre_id else None,
            'programa': {'id': a.programa_id, 'codigo': a.programa.codigo, 'nombre': a.programa.nombre},
            'curso_vinculado': _vinculo(a)}


def fila_solicitud(s):
    return {'id': s.id, 'estado': s.estado, 'mensaje': s.mensaje, 'respuesta': s.respuesta,
            'creada_en': s.creada_en, 'resuelta_en': s.resuelta_en, 'resuelta_por': _nombre(s.resuelta_por),
            'reemplazo_curso': s.reemplazo_curso,
            'curso': {'id': s.curso_id, 'nombre': s.curso.nombre, 'codigo': s.curso.codigo},
            'docente': {'id': s.docente_id, 'nombre': _nombre(s.docente), 'email': s.docente.email},
            'asignatura': _asignatura(s.asignatura)}


def _qs():
    return SolicitudVinculacion.objects.select_related(
        'curso__docente', 'docente', 'resuelta_por', 'asignatura__programa', 'asignatura__semestre',
        'asignatura__curso_vinculado__docente')


class VistaOpcionesVinculacion(APIView):
    permission_classes = [EsDocente]

    def get(self, request):
        asignaturas = (AsignaturaMalla.objects.filter(activo=True, programa__activo=True)
                       .select_related('programa', 'semestre', 'curso_vinculado__docente')
                       .order_by('programa__codigo', 'semestre__numero', 'nombre'))
        programas = {}
        for a in asignaturas:
            p = programas.setdefault(a.programa_id, {'id': a.programa_id, 'codigo': a.programa.codigo,
                                                      'nombre': a.programa.nombre, 'asignaturas': []})
            p['asignaturas'].append(_asignatura(a))
        return Response(list(programas.values()))


class VistaVinculacionCurso(APIView):
    permission_classes = [EsDocente]

    def _curso(self, request, curso_id):
        # Lo ajeno responde 404, igual que el resto de vistas del docente.
        return get_object_or_404(Curso, pk=curso_id, docente=request.user)

    def get(self, request, curso_id):
        curso = self._curso(request, curso_id)
        vinculadas = AsignaturaMalla.objects.filter(curso_vinculado=curso).select_related(
            'programa', 'semestre', 'curso_vinculado__docente')
        return Response({'curso': {'id': curso.id, 'nombre': curso.nombre, 'codigo': curso.codigo},
                         'vinculadas': [_asignatura(a) for a in vinculadas],
                         'solicitudes': [fila_solicitud(s) for s in _qs().filter(curso=curso)]})

    def post(self, request, curso_id):
        curso = self._curso(request, curso_id)
        asignatura = AsignaturaMalla.objects.filter(pk=request.data.get('asignatura'), activo=True).select_related(
            'programa').first()
        if asignatura is None or not asignatura.programa.activo:
            return Response({'asignatura': ['Elige una asignatura activa de un programa activo.']}, status=400)
        if asignatura.curso_vinculado_id == curso.id:
            return Response({'detalle': 'Este curso ya está vinculado a esa asignatura.'}, status=409)
        mensaje = str(request.data.get('mensaje') or '').strip()[:1000]
        try:
            with transaction.atomic():
                s = SolicitudVinculacion.objects.create(curso=curso, docente=request.user, asignatura=asignatura,
                                                        mensaje=mensaje)
        except IntegrityError:
            return Response({'detalle': 'Ya hay una solicitud pendiente para esta asignatura.'}, status=409)
        return Response(fila_solicitud(_qs().get(pk=s.pk)), status=201)


class VistaCancelarSolicitud(APIView):
    permission_classes = [EsDocente]

    def post(self, request, pk):
        s = get_object_or_404(_qs(), pk=pk, docente=request.user)
        if s.estado != OpcionesEstadoSolicitud.PENDIENTE:
            return Response({'detalle': 'Solo se cancelan solicitudes pendientes.'}, status=409)
        s.estado = OpcionesEstadoSolicitud.CANCELADA
        s.resuelta_en = timezone.now()
        s.save(update_fields=['estado', 'resuelta_en'])
        return Response(fila_solicitud(s))


class VistaSolicitudesVinculacion(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request):
        estado = request.query_params.get('estado', OpcionesEstadoSolicitud.PENDIENTE)
        qs = _qs()
        if estado != 'todas':
            qs = qs.filter(estado=estado)
        pendientes = SolicitudVinculacion.objects.filter(estado=OpcionesEstadoSolicitud.PENDIENTE).count()
        return Response({'pendientes': pendientes, 'solicitudes': [fila_solicitud(s) for s in qs[:300]]})


class VistaResolverSolicitud(APIView):
    """`POST vinculacion/solicitudes/<id>/<accion>/` con accion = aprobar | rechazar."""

    permission_classes = [EsGestorAcademico]

    def post(self, request, pk, accion):
        respuesta = str(request.data.get('respuesta') or '').strip()[:1000]
        with transaction.atomic():
            s = get_object_or_404(SolicitudVinculacion.objects.select_for_update(), pk=pk)
            if s.estado != OpcionesEstadoSolicitud.PENDIENTE:
                return Response({'detalle': 'La solicitud ya fue resuelta.'}, status=409)
            if accion == 'rechazar':
                if not respuesta:
                    return Response({'respuesta': ['Escribe el motivo del rechazo para el docente.']}, status=400)
                s.estado = OpcionesEstadoSolicitud.RECHAZADA
            elif accion == 'aprobar':
                asignatura = AsignaturaMalla.objects.select_for_update().get(pk=s.asignatura_id)
                if not asignatura.activo:
                    return Response({'detalle': 'La asignatura ya no está activa.'}, status=409)
                anterior = asignatura.curso_vinculado  # se carga tras el bloqueo (sin join)
                if anterior is not None and anterior.id != s.curso_id:
                    s.reemplazo_curso = f'{anterior.nombre} ({anterior.codigo})'[:150]
                asignatura.curso_vinculado_id = s.curso_id
                asignatura.save(update_fields=['curso_vinculado'])
                s.estado = OpcionesEstadoSolicitud.APROBADA
                # Otras solicitudes pendientes por la misma asignatura quedan sin efecto.
                (SolicitudVinculacion.objects.filter(asignatura_id=s.asignatura_id, estado=OpcionesEstadoSolicitud.PENDIENTE)
                 .exclude(pk=s.pk).update(estado=OpcionesEstadoSolicitud.RECHAZADA, resuelta_en=timezone.now(),
                                          resuelta_por=request.user,
                                          respuesta='La asignatura se vinculó a otro curso.'))
            else:
                return Response({'detalle': 'Acción no válida.'}, status=404)
            s.respuesta = respuesta
            s.resuelta_por = request.user
            s.resuelta_en = timezone.now()
            s.save()
        return Response(fila_solicitud(_qs().get(pk=s.pk)))

