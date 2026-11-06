"""
Alerta temprana (HU-10).

- `GET/PUT alertas/regla/`                    ver (Admin y Coordinador) / definir (solo Admin) la regla (HU-10.1)
- `GET programas/<id>/alertas/?estado=&tipo=` tablero: reevalúa y lista (Admin y Coordinador, HU-10.2)
- `POST alertas/<id>/atender/ {nota}`         el Coordinador registra el seguimiento
- `GET programas/<id>/alertas/exportar/`      CSV para Excel (solo Admin, HU-10.3)
"""

import csv
import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    OpcionesEstadoAlerta,
    ProgramaAcademico,
    ReglaAlerta,
)
from apps.evaluacion_resultados.services.servicio_alertas import evaluar_alertas
from core.permissions.permisos_rol import EsAdministrador, EsGestorAcademico


class SerializadorRegla(serializers.ModelSerializer):
    class Meta:
        model = ReglaAlerta
        fields = ['porcentaje_minimo', 'actividades_minimas', 'activa', 'actualizado_en']
        read_only_fields = ['actualizado_en']

    def validate_porcentaje_minimo(self, valor):
        if not 1 <= valor <= 100:
            raise serializers.ValidationError('El porcentaje debe estar entre 1 y 100.')
        return valor

    def validate_actividades_minimas(self, valor):
        if not 1 <= valor <= 50:
            raise serializers.ValidationError('El número de actividades debe estar entre 1 y 50.')
        return valor


def _fila(alerta):
    est = alerta.estudiante
    return {
        'id': alerta.id, 'tipo': alerta.tipo, 'estado': alerta.estado,
        'estudiante': {'id': est.id, 'nombre': f'{est.first_name} {est.first_last_name}'.strip(), 'email': est.email} if est else None,
        'asignatura': {'id': alerta.asignatura_id, 'codigo': alerta.asignatura.codigo, 'nombre': alerta.asignatura.nombre}
        if alerta.asignatura_id else None,
        'actividades_bajas': alerta.actividades_bajas, 'total_actividades': alerta.total_actividades,
        'detalle': alerta.detalle, 'nota_seguimiento': alerta.nota_seguimiento,
        'atendida_en': alerta.atendida_en, 'creada_en': alerta.creada_en, 'actualizada_en': alerta.actualizada_en,
    }


def _alertas(programa, params):
    qs = AlertaDesempeno.objects.filter(programa=programa).select_related('estudiante', 'asignatura')
    estado = params.get('estado', 'abierta')
    if estado in OpcionesEstadoAlerta.values:
        qs = qs.filter(estado=estado)
    if params.get('tipo') in ('estudiante', 'curso'):
        qs = qs.filter(tipo=params['tipo'])
    return qs


class VistaReglaAlerta(APIView):
    def get_permissions(self):
        return [EsAdministrador()] if self.request.method == 'PUT' else [EsGestorAcademico()]

    def get(self, request):
        return Response(SerializadorRegla(ReglaAlerta.vigente()).data)

    def put(self, request):
        regla = ReglaAlerta.vigente()
        serial = SerializadorRegla(regla, data=request.data, partial=True)
        serial.is_valid(raise_exception=True)
        serial.save(actualizado_por=request.user)
        # Con la regla nueva se reevalúan todas las alertas de inmediato.
        resumen = evaluar_alertas()
        return Response({**serial.data, 'resumen': resumen})


class VistaAlertasPrograma(APIView):
    permission_classes = [EsGestorAcademico]

    def get(self, request, programa_id):
        programa = get_object_or_404(ProgramaAcademico, pk=programa_id)
        resumen = evaluar_alertas(programa)
        regla = ReglaAlerta.vigente()
        return Response({
            'regla': SerializadorRegla(regla).data,
            'resumen': resumen,
            'abiertas': AlertaDesempeno.objects.filter(programa=programa, estado=OpcionesEstadoAlerta.ABIERTA).count(),
            'alertas': [_fila(a) for a in _alertas(programa, request.query_params)],
        })


class VistaAtenderAlerta(APIView):
    permission_classes = [EsGestorAcademico]

    def post(self, request, pk):
        alerta = get_object_or_404(AlertaDesempeno, pk=pk)
        if alerta.estado != OpcionesEstadoAlerta.ABIERTA:
            return Response({'detalle': 'Solo se pueden atender alertas abiertas.'}, status=409)
        nota = str(request.data.get('nota') or '').strip()
        if not nota:
            return Response({'nota': ['Describe la acción de seguimiento realizada.']}, status=400)
        alerta.estado = OpcionesEstadoAlerta.ATENDIDA
        alerta.nota_seguimiento = nota[:2000]
        alerta.atendida_por = request.user
        alerta.atendida_en = timezone.now()
        alerta.save()
        return Response(_fila(alerta))


class VistaExportarAlertas(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request, programa_id):
        programa = get_object_or_404(ProgramaAcademico, pk=programa_id)
        evaluar_alertas(programa)
        salida = io.StringIO()
        # `;` y BOM: Excel en español abre el archivo con columnas y tildes correctas.
        escritor = csv.writer(salida, delimiter=';')
        escritor.writerow(['Tipo', 'Estudiante', 'Correo', 'Asignatura', 'Actividades bajo el umbral',
                           'Total de actividades', 'Detalle', 'Estado', 'Seguimiento', 'Detectada'])
        for a in _alertas(programa, request.query_params):
            f = _fila(a)
            escritor.writerow([
                'Estudiante' if a.tipo == 'estudiante' else 'Curso',
                f['estudiante']['nombre'] if f['estudiante'] else '',
                f['estudiante']['email'] if f['estudiante'] else '',
                f'{f["asignatura"]["codigo"]} {f["asignatura"]["nombre"]}' if f['asignatura'] else '',
                a.actividades_bajas, a.total_actividades,
                ' | '.join(f'{d["nombre"]} ({d["porcentaje"]}%)' for d in a.detalle),
                a.get_estado_display(), a.nota_seguimiento,
                timezone.localtime(a.creada_en).strftime('%Y-%m-%d %H:%M'),
            ])
        respuesta = HttpResponse('﻿' + salida.getvalue(), content_type='text/csv; charset=utf-8')
        respuesta['Content-Disposition'] = f'attachment; filename="alertas_{programa.codigo}.csv"'
        return respuesta
