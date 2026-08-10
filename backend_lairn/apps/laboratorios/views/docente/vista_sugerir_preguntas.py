"""
Vista de sugerencia de preguntas con IA, para el rol Docente.

Expone `POST /laboratorios/laboratorios/<laboratorio_id>/preguntas/sugerir-ia/`
con `{"tipo": "codigo"|"respuesta_libre"|"problema_visual"}` en el body
(default "codigo" si se omite, por compatibilidad): genera UNA pregunta por
cada objetivo del curso, del tipo pedido.

- `tipo="codigo"`: usa `agente_codigo.generar_borrador_pregunta` y verifica
  los casos de test ejecutando la solución de referencia en el sandbox del
  ejecutor (`verificador_casos.verificar_casos`) — igual que antes.
- `tipo="respuesta_libre"`: usa
  `agente_respuesta_libre.generar_borrador_respuesta_libre`. Sin casos de
  test que verificar (no hay nada que ejecutar en un ensayo).
- `tipo="problema_visual"`: usa
  `agente_problema_visual.generar_variantes_problema_visual` (texto con
  Groq, diagramas con Hugging Face). Genera un enunciado genérico + 5
  variantes (cada una con su propio diagrama y sus 4 opciones de respuesta),
  todo viaja en el borrador con las imágenes en base64 (nunca se guardan en
  disco hasta que el docente acepta el borrador — ver
  `SerializadorPreguntaDocente`).

Importante: NO guarda nada. El docente acepta/descarta cada borrador en la
UI y los aceptados se crean con el POST normal de `/preguntas/`.

Si el curso no tiene objetivos, 400 (no hay de dónde generar). Si algún
objetivo no produce una pregunta utilizable, se omite y se reporta en
`objetivos_sin_generar` en vez de tumbar toda la operación.
"""

import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.laboratorios.models import Laboratorio
from apps.laboratorios.services.agente_codigo import generar_borrador_pregunta
from apps.laboratorios.services.agente_respuesta_libre import generar_borrador_respuesta_libre
from apps.laboratorios.services.agente_problema_visual import generar_variantes_problema_visual
from apps.laboratorios.services.agente_pronunciacion import generar_practica_pronunciacion
from apps.laboratorios.services.verificador_casos import verificar_casos


@extend_schema(
    tags=['Laboratorios'],
    summary='Sugerir preguntas con IA (una por objetivo del curso, código o respuesta abierta)',
    request=inline_serializer(
        name='SugerirPreguntasEntrada',
        fields={'tipo': drf_serializers.ChoiceField(choices=['codigo', 'respuesta_libre', 'problema_visual', 'pronunciacion'], required=False)},
    ),
    parameters=[OpenApiParameter('laboratorio_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: inline_serializer(
            name='RespuestaSugerirPreguntas',
            fields={
                'preguntas': drf_serializers.ListField(),
                'objetivos_sin_generar': drf_serializers.ListField(child=drf_serializers.CharField()),
            },
        ),
        400: OpenApiResponse(description='El curso no tiene objetivos definidos'),
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Laboratorio no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar ninguna pregunta verificable'),
    },
)
class VistaSugerirPreguntas(APIView):
    permission_classes = [EsDocente]

    def post(self, request, laboratorio_id):
        try:
            laboratorio = Laboratorio.objects.select_related('curso').get(
                id=laboratorio_id, curso__docente=request.user
            )
        except Laboratorio.DoesNotExist:
            return Response({'detalle': 'Laboratorio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        tipo = request.data.get('tipo', 'codigo')
        if tipo not in ('codigo', 'respuesta_libre', 'problema_visual', 'pronunciacion'):
            return Response(
                {'detalle': '"tipo" debe ser "codigo", "respuesta_libre", "problema_visual" o "pronunciacion".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        curso = laboratorio.curso
        objetivos = list(curso.objetivos.all())
        if not objetivos:
            return Response(
                {'detalle': 'El curso no tiene objetivos definidos. Agrégalos en la tab Objetivos antes de generar preguntas con IA.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preguntas = []
        objetivos_sin_generar = []

        for orden, objetivo in enumerate(objetivos):
            if tipo == 'pronunciacion':
                try:
                    borrador = generar_practica_pronunciacion(objetivo.descripcion, curso.nombre)
                except ValueError:
                    objetivos_sin_generar.append(objetivo.descripcion)
                    continue

                preguntas.append({
                    'objetivo_id': objetivo.id,
                    'objetivo': objetivo.descripcion,
                    'tipo': 'pronunciacion',
                    'enunciado': borrador['enunciado'],
                    'texto_pronunciar': borrador['texto_pronunciar'],
                    'criterios_ia': '',
                    'puntos': 100,
                    'orden': orden,
                    'casos_test': [],
                })
                continue

            if tipo == 'problema_visual':
                try:
                    borrador = generar_variantes_problema_visual(objetivo.descripcion, curso.nombre, cantidad=5)
                except ValueError:
                    objetivos_sin_generar.append(objetivo.descripcion)
                    continue

                preguntas.append({
                    'objetivo_id': objetivo.id,
                    'objetivo': objetivo.descripcion,
                    'tipo': 'problema_visual',
                    'enunciado': borrador['enunciado'],
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
                        for v in borrador['variantes']
                    ],
                })
                continue

            if tipo == 'respuesta_libre':
                try:
                    borrador = generar_borrador_respuesta_libre(objetivo.descripcion, curso.nombre)
                except ValueError:
                    objetivos_sin_generar.append(objetivo.descripcion)
                    continue

                preguntas.append({
                    'objetivo_id': objetivo.id,
                    'objetivo': objetivo.descripcion,
                    'tipo': 'respuesta_libre',
                    'enunciado': borrador['enunciado'],
                    'criterios_ia': borrador['criterios_ia'],
                    'puntos': 100,
                    'orden': orden,
                    'casos_test': [],
                })
                continue

            try:
                borrador = generar_borrador_pregunta(objetivo.descripcion, curso.nombre)
            except ValueError:
                objetivos_sin_generar.append(objetivo.descripcion)
                continue

            casos = verificar_casos(
                borrador['lenguaje'],
                borrador['solucion_referencia'],
                borrador.get('setup_sql', ''),
                borrador['casos'],
            )
            if not casos:
                objetivos_sin_generar.append(objetivo.descripcion)
                continue

            preguntas.append({
                'objetivo_id': objetivo.id,
                'objetivo': objetivo.descripcion,
                'tipo': 'codigo',
                'enunciado': borrador['enunciado'],
                'lenguaje': borrador['lenguaje'],
                'codigo_inicial': borrador.get('codigo_inicial', ''),
                'setup_sql': borrador.get('setup_sql', ''),
                'criterios_ia': '',
                'puntos': 100,
                'orden': orden,
                'casos_test': casos,
            })

        if not preguntas:
            return Response(
                {'detalle': 'La IA no pudo generar ni verificar ninguna pregunta para los objetivos del curso.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'preguntas': preguntas, 'objetivos_sin_generar': objetivos_sin_generar})
