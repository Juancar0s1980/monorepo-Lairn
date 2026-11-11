"""
Notas del momento (ADR-019).

- `GET  notas-momento/momentos/`                   momentos con evaluaciones publicadas (selector), con el rango
  de fechas de esas evaluaciones. Filtros opcionales: `programa`, `periodo`, `desde`, `hasta`
  (AAAA-MM-DD, se cruza con el rango de fechas) y `q` (nombre del momento, programa o periodo).
- `GET  notas-momento/<momento_id>/`               notas por estudiante + resumen (JSON).
- `GET  notas-momento/<momento_id>/exportar/`      Excel; cada exportación queda registrada.
- `GET|PUT notas-momento/<momento_id>/esquema/`    ponderación examen/trabajo del momento (gestor).
- `GET|PUT notas-momento/esquema-institucional/`   valores institucionales (solo Administrador).

Lectura y exportación: Administrador, Coordinador y Vicerrector (decisión del usuario, cambia
ADR-012 para este dato). Docente y Estudiante: 403.
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Max, Min, Q

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import EsquemaCalificacion, MomentoEvaluacion
from apps.evaluacion_resultados.services.servicio_exportar_notas import a_excel
from apps.evaluacion_resultados.services.servicio_notas_momento import esquema_efectivo, notas_del_momento
from apps.evaluacion_resultados.services.servicio_trazabilidad import registrar_sincronizacion
from core.permissions.permisos_rol import EsAdministrador, EsGestorAcademico, EsLectorAnalitica

CAMPOS_MOMENTO = ('peso_examen', 'peso_trabajo')
ZONA_INSTITUCION = ZoneInfo('America/Bogota')
CAMPOS_INSTITUCIONALES = ('peso_momento_en_corte', 'peso_corte_en_definitiva', 'peso_examen', 'peso_trabajo')


def _pct(valor, campo):
    if valor in (None, ''):
        return None
    try:
        d = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise ValueError(f'"{campo}" debe ser un número.')
    if not Decimal(0) <= d <= Decimal(100):
        raise ValueError(f'"{campo}" debe estar entre 0 y 100.')
    return d.quantize(Decimal('0.01'))


def _guardar(esquema, datos, campos, usuario):
    limpio = {c: _pct(datos.get(c), c) for c in campos if c in datos}
    pe = limpio.get('peso_examen', esquema.peso_examen)
    pt = limpio.get('peso_trabajo', esquema.peso_trabajo)
    if (pe is None) != (pt is None):
        raise ValueError('Define los dos pesos (examen y trabajo) o deja ambos vacíos.')
    if pe is not None and pe + pt != 100:
        raise ValueError('El peso del examen y el del trabajo deben sumar 100 %.')
    for campo, valor in limpio.items():
        setattr(esquema, campo, valor)
    esquema.actualizado_por = usuario
    esquema.save()


def _fecha(valor):
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


class VistaMomentosConNotas(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        publicadas = Q(evaluaciones__estado='publicada')
        qs = (MomentoEvaluacion.objects.filter(publicadas).select_related('programa').distinct()
              .annotate(fecha_inicio=Min('evaluaciones__fecha_inicio', filter=publicadas),
                        fecha_fin=Max('evaluaciones__fecha_fin', filter=publicadas),
                        total_evaluaciones=Count('evaluaciones', filter=publicadas, distinct=True)))
        p = request.query_params
        if p.get('programa', '').isdigit():
            qs = qs.filter(programa_id=int(p['programa']))
        if p.get('periodo'):
            qs = qs.filter(periodo=p['periodo'])
        desde, hasta = _fecha(p.get('desde')), _fecha(p.get('hasta'))
        # Un momento entra si el rango de fechas de sus evaluaciones se cruza con [desde, hasta].
        # Los días son de Colombia (lo que ve el usuario), aunque el servidor trabaje en UTC.
        if desde:
            qs = qs.filter(fecha_fin__gte=datetime.combine(desde, time.min, ZONA_INSTITUCION))
        if hasta:
            qs = qs.filter(fecha_inicio__lte=datetime.combine(hasta, time.max, ZONA_INSTITUCION))
        texto = p.get('q', '').strip()
        if texto:
            qs = qs.filter(Q(nombre__icontains=texto) | Q(periodo__icontains=texto)
                           | Q(programa__codigo__icontains=texto) | Q(programa__nombre__icontains=texto))
        return Response([
            {'id': m.id, 'nombre': m.nombre, 'periodo': m.periodo, 'semestre_referencia': m.semestre_referencia,
             'programa_id': m.programa_id, 'programa': f'{m.programa.codigo} · {m.programa.nombre}',
             'fecha_inicio': m.fecha_inicio, 'fecha_fin': m.fecha_fin, 'total_evaluaciones': m.total_evaluaciones}
            for m in qs.order_by('programa__codigo', '-fecha_inicio', 'nombre')
        ])


class VistaNotasMomento(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request, momento_id):
        datos = notas_del_momento(get_object_or_404(MomentoEvaluacion, pk=momento_id))
        datos['puede_editar_esquema'] = EsGestorAcademico().has_permission(request, self)
        return Response(datos)


class VistaExportarNotasMomento(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request, momento_id):
        momento = get_object_or_404(MomentoEvaluacion.objects.select_related('programa'), pk=momento_id)
        datos = notas_del_momento(momento)
        contenido = a_excel(datos, request.user)
        # Trazabilidad de datos personales: quién exportó qué momento y cuándo.
        registrar_sincronizacion(
            origen='notas_momento', entidad='exportacion_notas', modo='exportacion',
            total_recibidos=len(datos['filas']), ejecutado_por=request.user,
            errores=[f'Momento {momento.id} · {momento.nombre} · {momento.programa.codigo}'],
        )
        respuesta = HttpResponse(
            contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        nombre = f'notas_momento_{momento.programa.codigo}_{momento.id}_{timezone.localdate():%Y%m%d}.xlsx'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


class VistaEsquemaMomento(APIView):
    """Ponderación examen/trabajo de un momento. Lectura: lectores; edición: gestor académico."""

    def get_permissions(self):
        return [EsGestorAcademico()] if self.request.method == 'PUT' else [EsLectorAnalitica()]

    def get(self, request, momento_id):
        momento = get_object_or_404(MomentoEvaluacion, pk=momento_id)
        return Response(esquema_efectivo(momento))

    def put(self, request, momento_id):
        momento = get_object_or_404(MomentoEvaluacion, pk=momento_id)
        esquema, _ = EsquemaCalificacion.objects.get_or_create(momento=momento)
        try:
            _guardar(esquema, request.data, CAMPOS_MOMENTO, request.user)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        return Response(esquema_efectivo(momento))


class VistaEsquemaInstitucional(APIView):
    def get_permissions(self):
        return [EsAdministrador()] if self.request.method == 'PUT' else [EsLectorAnalitica()]

    def get(self, request):
        e = EsquemaCalificacion.objects.filter(momento__isnull=True).first()
        return Response({c: (None if e is None or getattr(e, c) is None else float(getattr(e, c)))
                         for c in CAMPOS_INSTITUCIONALES})

    def put(self, request):
        esquema = EsquemaCalificacion.objects.filter(momento__isnull=True).first() or EsquemaCalificacion(momento=None)
        try:
            _guardar(esquema, request.data, CAMPOS_INSTITUCIONALES, request.user)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        return self.get(request)
