"""
Aprobación de cuentas administrativas (HU-26). Solo el Administrador.

- `GET  usuarios/administracion/solicitudes-cuenta/?estado=pendiente|aprobada|rechazada|todas`
- `POST usuarios/administracion/solicitudes-cuenta/<id>/aprobar/`    activa la cuenta con el rol pedido
- `POST usuarios/administracion/solicitudes-cuenta/<id>/rechazar/`   {motivo} la cuenta sigue inactiva
"""

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import OpcionesEstadoCuenta, SolicitudCuenta
from core.permissions.permisos_rol import EsAdministrador


def _nombre(u) -> str:
    return ' '.join(p for p in (u.first_name, u.second_name, u.first_last_name, u.second_last_name) if p and p != '-')


def serializar(s: SolicitudCuenta) -> dict:
    return {
        'id': s.id,
        'estado': s.estado,
        'rol_solicitado': s.rol_solicitado.name,
        'motivo': s.motivo,
        'creada_en': s.creada_en,
        'resuelta_en': s.resuelta_en,
        'resuelta_por': _nombre(s.resuelta_por) if s.resuelta_por else '',
        'usuario': {'id': s.usuario_id, 'nombre': _nombre(s.usuario), 'email': s.usuario.email},
    }


class VistaSolicitudesCuenta(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(tags=['Usuarios'], summary='Solicitudes de cuenta administrativa')
    def get(self, request):
        qs = SolicitudCuenta.objects.select_related('usuario', 'rol_solicitado', 'resuelta_por')
        estado = request.query_params.get('estado', OpcionesEstadoCuenta.PENDIENTE)
        if estado in OpcionesEstadoCuenta.values:
            qs = qs.filter(estado=estado)
        pendientes = SolicitudCuenta.objects.filter(estado=OpcionesEstadoCuenta.PENDIENTE).count()
        return Response({'pendientes': pendientes, 'solicitudes': [serializar(s) for s in qs[:200]]})


class VistaResolverSolicitudCuenta(APIView):
    permission_classes = [EsAdministrador]

    @extend_schema(tags=['Usuarios'], summary='Aprobar o rechazar una solicitud de cuenta')
    def post(self, request, pk, accion):
        if accion not in ('aprobar', 'rechazar'):
            return Response({'detalle': 'Acción no válida.'}, status=404)
        motivo = str(request.data.get('motivo') or '').strip()[:1000]
        if accion == 'rechazar' and not motivo:
            return Response({'motivo': ['Escribe el motivo del rechazo.']}, status=400)
        with transaction.atomic():
            solicitud = SolicitudCuenta.objects.select_for_update().filter(pk=pk).first()
            if solicitud is None:
                return Response({'detalle': 'La solicitud no existe.'}, status=404)
            if solicitud.estado != OpcionesEstadoCuenta.PENDIENTE:
                return Response({'detalle': 'La solicitud ya fue resuelta.'}, status=409)
            usuario = solicitud.usuario
            if accion == 'aprobar':
                usuario.role = solicitud.rol_solicitado
                usuario.is_active = True
                usuario.save(update_fields=['role', 'is_active'])
                solicitud.estado = OpcionesEstadoCuenta.APROBADA
            else:
                solicitud.estado = OpcionesEstadoCuenta.RECHAZADA
            solicitud.motivo = motivo
            solicitud.resuelta_por = request.user
            solicitud.resuelta_en = timezone.now()
            solicitud.save()
        solicitud = SolicitudCuenta.objects.select_related('usuario', 'rol_solicitado', 'resuelta_por').get(pk=pk)
        return Response(serializar(solicitud))
