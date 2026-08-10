"""
Vista para generar (o recuperar) el laboratorio de práctica de un examen,
para el rol Docente.

Expone `POST /examenes/examenes/<examen_id>/generar-practica/`: crea un
`Laboratorio` (con `examen=examen`) y una `Pregunta` de tipo `respuesta_libre`
generada con IA a partir del tema y curso del examen
(`agente_respuesta_libre.generar_borrador_respuesta_libre`) — funciona para
cualquier carrera, no solo programación.

Es idempotente: si el examen ya tiene un laboratorio de práctica vinculado,
lo devuelve tal cual en vez de crear uno nuevo. El docente puede después
abrirlo en el editor normal de laboratorios para ajustarlo o agregar
preguntas de tipo código si el curso es técnico (mismo patrón
"generar → curar → guardar = publicado" que ya usa Laboratorios).

Esto NO activa por sí solo la combinación de notas: eso depende de que el
examen tenga `peso_practica > 0` y de que el estudiante finalice la práctica
(ver `apps.laboratorios.views.estudiante.vista_finalizar_practica`).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsDocente
from apps.examenes.models import Examen
from apps.laboratorios.models import Laboratorio, Pregunta
from apps.laboratorios.serializers import SerializadorLaboratorioDetalleDocente
from apps.laboratorios.services.agente_respuesta_libre import generar_borrador_respuesta_libre


@extend_schema(
    tags=['Exámenes'],
    summary='Generar el laboratorio de práctica de un examen (idempotente)',
    description=(
        'Genera con IA una pregunta de respuesta abierta anclada al tema del examen y crea '
        'un Laboratorio vinculado a él. Si ya existe uno, lo devuelve sin duplicar.'
    ),
    request=None,
    parameters=[OpenApiParameter('examen_id', OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses={
        200: SerializadorLaboratorioDetalleDocente,
        201: SerializadorLaboratorioDetalleDocente,
        403: OpenApiResponse(description='Solo los docentes pueden acceder'),
        404: OpenApiResponse(description='Examen no encontrado'),
        502: OpenApiResponse(description='La IA no pudo generar la práctica'),
    },
)
class VistaGenerarPracticaExamen(APIView):
    permission_classes = [EsDocente]

    def post(self, request, examen_id):
        try:
            examen = Examen.objects.select_related('curso').get(id=examen_id, curso__docente=request.user)
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        existente = examen.laboratorio_practica.first()
        if existente:
            return Response(SerializadorLaboratorioDetalleDocente(existente).data)

        try:
            borrador = generar_borrador_respuesta_libre(
                objetivo_texto=examen.tema,
                tema_curso=examen.curso.nombre,
            )
        except ValueError as e:
            return Response(
                {'detalle': f'No se pudo generar la práctica: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        laboratorio = Laboratorio.objects.create(
            curso=examen.curso,
            examen=examen,
            titulo=f'Práctica: {examen.titulo}',
            instrucciones=f'Ejercicio práctico generado a partir del examen "{examen.titulo}".',
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
