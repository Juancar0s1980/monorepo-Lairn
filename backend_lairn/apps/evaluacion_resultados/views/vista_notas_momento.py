"""
Notas del momento (ADR-019).

- `GET  notas-momento/momentos/?programa=`         momentos con evaluaciones publicadas (selector).
- `GET  notas-momento/<momento_id>/`               notas por estudiante + resumen (JSON).
- `GET  notas-momento/<momento_id>/exportar/`      Excel; cada exportación queda registrada.
- `GET|PUT notas-momento/<momento_id>/esquema/`    ponderación examen/trabajo del momento (gestor).
- `GET|PUT notas-momento/esquema-institucional/`   valores institucionales (solo Administrador).

Lectura y exportación: Administrador, Coordinador y Vicerrector (decisión del usuario, cambia
ADR-012 para este dato). Docente y Estudiante: 403.
"""

from decimal import Decimal, InvalidOperation

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


class VistaMomentosConNotas(APIView):
    permission_classes = [EsLectorAnalitica]

    def get(self, request):
        qs = MomentoEvaluacion.objects.filter(evaluaciones__estado='publicada').select_related('programa').distinct()
        programa = request.query_params.get('programa', '')
        if programa.isdigit():
            qs = qs.filter(programa_id=int(programa))
        return Response([
            {'id': m.id, 'nombre': m.nombre, 'periodo': m.periodo, 'semestre_referencia': m.semestre_referencia,
             'programa_id': m.programa_id, 'programa': f'{m.programa.codigo} · {m.programa.nombre}'}
            for m in qs.order_by('programa__codigo', 'semestre_referencia', 'nombre')
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
