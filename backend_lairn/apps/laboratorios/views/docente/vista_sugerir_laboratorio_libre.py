"""
Vista de generación de un laboratorio completo con IA a partir de un
enunciado libre, para el rol Docente.

Expone `POST /laboratorios/cursos/<curso_id>/laboratorios/sugerir-libre/`:
el docente describe en lenguaje natural qué laboratorio quiere y elige el
`tipo` de ejercicio (código, respuesta abierta, problema con imagen o
pronunciación) — no está limitado a programación, sirve para cualquier
carrera. La IA genera título, instrucciones y varias preguntas completas de
ese tipo:
- `codigo`: `agente_codigo.generar_laboratorio_libre` (requiere `lenguaje`),
  cada pregunta se verifica ejecutando su solución de referencia en el
  sandbox (`verificador_casos.verificar_casos`).
- `respuesta_libre`: `agente_respuesta_libre.generar_laboratorio_libre_respuesta_libre`.
- `problema_visual`: `agente_problema_visual.generar_laboratorio_libre_problema_visual`
  — cada pregunta es un problema con diagrama INDEPENDIENTE (con sus propias
  variantes), no repite el mismo problema con distintos números.
- `pronunciacion`: `agente_pronunciacion.generar_laboratorio_libre_pronunciacion`.

Importante: NO guarda nada. El docente revisa el borrador en la UI; al
aceptar, el frontend crea el `Laboratorio` (POST normal) y luego cada
pregunta aceptada dentro de él (POST normal de `/preguntas/`).

Si ninguna pregunta sobrevive la generación/verificación, 502 (nada que ofrecer).
"""

import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Curso
from apps.laboratorios.serializers import SerializadorSugerirLaboratorioLibre
from apps.laboratorios.services.agente_codigo import generar_laboratorio_libre
from apps.laboratorios.services.agente_respuesta_libre import generar_laboratorio_libre_respuesta_libre
from apps.laboratorios.services.agente_problema_visual import generar_laboratorio_libre_problema_visual
from apps.laboratorios.services.agente_pronunciacion import generar_laboratorio_libre_pronunciacion
from apps.laboratorios.services.verificador_casos import verificar_casos


@extend_schema(
    tags=['Laboratorios'],
    summary='Generar un laboratorio completo con IA a partir de un enunciado libre',
    request=SerializadorSugerirLaboratorioLibre,
    parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: inline_serializer(
            name='RespuestaSugerirLaboratorioLibre',
            fields={
                'titulo': drf_serializers.CharField(),
                'instrucciones': drf_serializers.CharField(),
                'preguntas': drf_serializers.ListField(),
            },
        ),
        400: OpenApiResponse(description='Datos inválidos'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Curso no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar ninguna pregunta verificable'),
    },
)
class VistaSugerirLaboratorioLibre(APIView):
    permission_classes = [EsDocente]

    def post(self, request, curso_id):
        try:
            curso = Curso.objects.get(id=curso_id, docente=request.user)
        except Curso.DoesNotExist:
            return Response({'detalle': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        entrada = SerializadorSugerirLaboratorioLibre(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)

        tipo = entrada.validated_data['tipo']
        enunciado_docente = entrada.validated_data['enunciado']
        cantidad_preguntas = entrada.validated_data['cantidad_preguntas']

        if tipo == 'respuesta_libre':
            return self._generar_respuesta_libre(enunciado_docente, cantidad_preguntas)
        if tipo == 'problema_visual':
            return self._generar_problema_visual(enunciado_docente, curso.nombre, cantidad_preguntas)
        if tipo == 'pronunciacion':
            return self._generar_pronunciacion(enunciado_docente, curso.nombre, cantidad_preguntas)
        return self._generar_codigo(enunciado_docente, entrada.validated_data['lenguaje'], cantidad_preguntas)

    def _generar_codigo(self, enunciado_docente, lenguaje, cantidad_preguntas):
        try:
            borrador = generar_laboratorio_libre(
                enunciado_docente=enunciado_docente, lenguaje=lenguaje, cantidad_preguntas=cantidad_preguntas
            )
        except ValueError as e:
            return Response({'detalle': f'No se pudo generar el laboratorio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        preguntas_verificadas = []
        for orden, pregunta in enumerate(borrador['preguntas']):
            casos = verificar_casos(
                pregunta['lenguaje'], pregunta['solucion_referencia'], pregunta.get('setup_sql', ''), pregunta['casos']
            )
            if not casos:
                continue
            preguntas_verificadas.append({
                'tipo': 'codigo',
                'enunciado': pregunta['enunciado'],
                'lenguaje': pregunta['lenguaje'],
                'codigo_inicial': pregunta.get('codigo_inicial', ''),
                'setup_sql': pregunta.get('setup_sql', ''),
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': casos,
            })

        if not preguntas_verificadas:
            return Response(
                {'detalle': 'La IA no pudo generar ninguna pregunta verificable para ese laboratorio.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'titulo': borrador['titulo'],
            'instrucciones': borrador['instrucciones'],
            'preguntas': preguntas_verificadas,
        })

    def _generar_respuesta_libre(self, enunciado_docente, cantidad_preguntas):
        try:
            borrador = generar_laboratorio_libre_respuesta_libre(enunciado_docente, cantidad_preguntas)
        except ValueError as e:
            return Response({'detalle': f'No se pudo generar el laboratorio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        preguntas = [
            {
                'tipo': 'respuesta_libre',
                'enunciado': p['enunciado'],
                'criterios_ia': p['criterios_ia'],
                'puntos': 100,
                'orden': orden,
                'casos_test': [],
            }
            for orden, p in enumerate(borrador['preguntas'])
        ]
        return Response({'titulo': borrador['titulo'], 'instrucciones': borrador['instrucciones'], 'preguntas': preguntas})

    def _generar_problema_visual(self, enunciado_docente, tema_curso, cantidad_preguntas):
        try:
            borrador = generar_laboratorio_libre_problema_visual(enunciado_docente, tema_curso, cantidad_preguntas)
        except ValueError as e:
            return Response({'detalle': f'No se pudo generar el laboratorio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        preguntas = [
            {
                'tipo': 'problema_visual',
                'enunciado': p['enunciado'],
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': [],
                'variantes': [
                    {
                        'opciones': v['opciones'],
                        'respuesta_correcta': v['respuesta_correcta'],
                        'imagen_base64': base64.b64encode(v['imagen_bytes']).decode('ascii'),
                    }
                    for v in p['variantes']
                ],
            }
            for orden, p in enumerate(borrador['preguntas'])
        ]
        return Response({'titulo': borrador['titulo'], 'instrucciones': borrador['instrucciones'], 'preguntas': preguntas})

    def _generar_pronunciacion(self, enunciado_docente, tema_curso, cantidad_preguntas):
        try:
            borrador = generar_laboratorio_libre_pronunciacion(enunciado_docente, tema_curso, cantidad_preguntas)
        except ValueError as e:
            return Response({'detalle': f'No se pudo generar el laboratorio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        preguntas = [
            {
                'tipo': 'pronunciacion',
                'enunciado': p['enunciado'],
                'texto_pronunciar': p['texto_pronunciar'],
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': [],
            }
            for orden, p in enumerate(borrador['preguntas'])
        ]
        return Response({'titulo': borrador['titulo'], 'instrucciones': borrador['instrucciones'], 'preguntas': preguntas})
