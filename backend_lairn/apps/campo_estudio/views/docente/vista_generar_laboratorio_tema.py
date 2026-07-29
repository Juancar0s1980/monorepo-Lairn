"""
Vista para generar (o recuperar) el laboratorio de práctica de un tema de
estudio, para el rol Docente.

Expone `POST /campo-estudio/temas/<tema_id>/generar-laboratorio/`: crea un
`Laboratorio` (con `tema_estudio=tema`) y una `Pregunta` de tipo
`respuesta_libre` generada con IA a partir del título y contenido del tema
(`agente_respuesta_libre.generar_borrador_respuesta_libre`) — funciona para
cualquier carrera, no solo programación, igual que el resto del tema.

Es idempotente: si el tema ya tiene un laboratorio de práctica vinculado, lo
devuelve tal cual en vez de crear uno nuevo. El docente puede después abrirlo
en el editor normal de laboratorios para ajustarlo (mismo patrón
"generar → curar → guardar = publicado" que ya usa Laboratorios; no hay un
segundo circuito de aprobación aparte del que ya tiene el tema).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.campo_estudio.models import TemaEstudio
from apps.laboratorios.models import Laboratorio, Pregunta
from apps.laboratorios.serializers import SerializadorLaboratorioDetalleDocente
from apps.laboratorios.services.agente_respuesta_libre import generar_borrador_respuesta_libre


@extend_schema(
    tags=['Campo de Estudio'],
    summary='Generar el laboratorio de práctica de un tema (idempotente)',
    description=(
        'Genera con IA una pregunta de respuesta abierta anclada al tema y crea un '
        'Laboratorio vinculado a él. Si ya existe uno, lo devuelve sin duplicar.'
    ),
    request=None,
    parameters=[OpenApiParameter('tema_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: SerializadorLaboratorioDetalleDocente,
        201: SerializadorLaboratorioDetalleDocente,
        404: OpenApiResponse(description='Tema no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar la práctica'),
    },
)
class VistaGenerarLaboratorioTema(APIView):
    permission_classes = [EsDocente]

    def post(self, request, tema_id):
        try:
            tema = TemaEstudio.objects.select_related('curso').get(id=tema_id, curso__docente=request.user)
        except TemaEstudio.DoesNotExist:
            return Response({'detalle': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        existente = tema.laboratorios_practica.first()
        if existente:
            return Response(SerializadorLaboratorioDetalleDocente(existente).data)

        try:
            borrador = generar_borrador_respuesta_libre(
                objetivo_texto=f'{tema.titulo}: {tema.contenido}',
                tema_curso=tema.curso.nombre,
            )
        except ValueError as e:
            return Response(
                {'detalle': f'No se pudo generar la práctica: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        laboratorio = Laboratorio.objects.create(
            curso=tema.curso,
            tema_estudio=tema,
            titulo=f'Práctica: {tema.titulo}',
            instrucciones=f'Ejercicio de práctica generado a partir del tema "{tema.titulo}".',
        )
        Pregunta.objects.create(
            laboratorio=laboratorio,
            tipo='respuesta_libre',
            enunciado=borrador['enunciado'],
            criterios_ia=borrador['criterios_ia'],
        )

        return Response(
            SerializadorLaboratorioDetalleDocente(laboratorio).data,
            status=status.HTTP_201_CREATED,
        )
