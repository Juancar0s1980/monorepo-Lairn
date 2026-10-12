"""
Vista de generación de contenido Saber Pro con IA, para el rol Docente (HU-20.1/20.2).

Expone `POST /docente/cursos/<curso_id>/contenido/generar/`: genera contenido
para el área del curso según su estructura de evaluación y lo persiste como
`pendiente` en el banco del docente (HU-20.3 decide luego aprobarlo o descartarlo).

- Áreas estructuradas e Inglés: preguntas de selección múltiple, respetando
  competencia/afirmación/evidencia (cuando aplican) o la parte de Inglés. La
  parte 1 de Inglés es de relacionar: 8 palabras para 5 descripciones y se
  persiste en `relaciones` (sin `respuesta_correcta`). Las partes 2 a 7 se
  generan como la parte COMPLETA del examen (un solo bloque con `preguntas`,
  ver `catalogo_saber_pro.PREGUNTAS_POR_PARTE_INGLES`).
- Comunicación Escrita: consignas de escritura (HU-20.2).

La vista no arma prompts: valida la solicitud con el serializer (que conoce el
área y su estructura) y delega la generación en `services/agente_saber_pro.py`.
La IA puede devolver una estructura inválida tras sus reintentos; en ese caso
se responde 502 sin persistir nada.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from core.permissions.permisos_rol import EsDocente
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.serializers import SerializadorContenidoBanco, SerializadorGenerarContenido
from apps.saber_pro.services.agente_saber_pro import generar_consignas, generar_preguntas
from apps.saber_pro.services.catalogo_saber_pro import (
    ESTRUCTURA_CONSIGNA,
    ESTRUCTURA_PARTES,
    obtener_estructura_area,
)


@extend_schema(
    tags=['Saber Pro - Docente'],
    summary='Generar contenido del banco con IA',
    description=(
        'Genera con IA contenido para el área del curso y lo deja como contenido '
        'pendiente de revisión. En áreas estructuradas recibe competencia/afirmación/'
        'evidencia; en Inglés, la parte (la parte 1 es de relacionar, no de opción '
        'múltiple); en Comunicación Escrita, nada.'
    ),
    request=SerializadorGenerarContenido,
    examples=[
        OpenApiExample(
            name='Área estructurada',
            value={'competencia_id': 1, 'afirmacion_id': 1, 'evidencia_id': 1, 'cantidad': 3},
            request_only=True,
        ),
        OpenApiExample(
            name='Inglés (parte 1: relacionar)',
            value={'parte': 1},
            request_only=True,
        ),
        OpenApiExample(
            name='Inglés (parte 4)',
            value={'parte': 4},
            request_only=True,
        ),
    ],
    responses={
        201: SerializadorContenidoBanco(many=True),
        400: OpenApiResponse(description='Solicitud inválida para la estructura del área'),
        404: OpenApiResponse(description='Curso Saber Pro no encontrado'),
        502: OpenApiResponse(description='La IA no produjo contenido válido'),
    },
)
class VistaGenerarContenidoSaberPro(APIView):
    permission_classes = [EsDocente]

    def post(self, request, curso_id):
        try:
            curso = CursoSaberPro.objects.select_related('area').get(id=curso_id, docente=request.user)
        except CursoSaberPro.DoesNotExist:
            return Response({'detalle': 'Curso Saber Pro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        area = curso.area
        estructura = obtener_estructura_area(area)
        serializador = SerializadorGenerarContenido(
            data=request.data,
            context={'area': area, 'estructura': estructura},
        )
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializador.validated_data
        es_consigna = estructura == ESTRUCTURA_CONSIGNA
        # En Inglés cada llamada genera la parte COMPLETA como un solo bloque
        # (texto base + sus preguntas), replicando el examen real; la cantidad
        # de preguntas la define el catálogo, no el docente.
        cantidad = 1 if estructura == ESTRUCTURA_PARTES else datos['cantidad']

        try:
            if es_consigna:
                generados = generar_consignas(cantidad)
            else:
                generados = generar_preguntas(
                    area.nombre,
                    cantidad=cantidad,
                    competencia=datos['competencia'].nombre if datos.get('competencia') else '',
                    afirmacion=datos['afirmacion'].nombre if datos.get('afirmacion') else '',
                    evidencia=datos['evidencia'].nombre if datos.get('evidencia') else '',
                    parte=datos.get('parte'),
                )
        except ValueError as e:
            return Response({'detalle': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        creados = [self._persistir(area, request.user, datos, item, es_consigna) for item in generados]
        return Response(
            SerializadorContenidoBanco(creados, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    def _persistir(self, area, docente, datos, item, es_consigna):
        """Crea el registro del banco a partir de un ítem generado por la IA."""
        if es_consigna:
            return ContenidoBancoSaberPro.objects.create(
                area=area,
                docente=docente,
                tipo='consigna_escrita',
                tema=item['tema'],
                contexto=item['contexto'],
                enunciado=item['enunciado'],
            )
        return ContenidoBancoSaberPro.objects.create(
            area=area,
            docente=docente,
            tipo='seleccion_multiple',
            competencia=datos.get('competencia'),
            afirmacion=datos.get('afirmacion'),
            evidencia=datos.get('evidencia'),
            parte=datos.get('parte'),
            contexto=item['contexto'],
            enunciado=item['enunciado'],
            opciones=item.get('opciones', []),
            # Vacío en la parte 1 de Inglés: ese ítem guarda sus respuestas en
            # `relaciones`; las partes 2 a 7 las guardan en `preguntas`.
            respuesta_correcta=item.get('respuesta_correcta', ''),
            relaciones=item.get('relaciones', []),
            preguntas=item.get('preguntas', []),
        )