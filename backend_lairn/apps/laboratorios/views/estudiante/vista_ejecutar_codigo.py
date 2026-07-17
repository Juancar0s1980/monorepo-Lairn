"""
Vista "Ejecutar" (equivalente a "Run" en un juez en línea), para el rol
Estudiante.

Expone `/laboratorios/preguntas/<pregunta_id>/ejecutar/`: corre el código o
consulta que el estudiante está escribiendo contra los casos de test
PÚBLICOS de la pregunta, en el sandbox del microservicio ejecutor, y
devuelve el resultado. NO GUARDA NADA — es retroalimentación inmediata
mientras el estudiante programa, no una entrega calificada (eso es la
Fase 4: un endpoint "Enviar" aparte que correrá también los casos ocultos
y persistirá el resultado).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import PreguntaCodigo
from apps.laboratorios.serializers import SerializadorEjecutarCodigo, SerializadorResultadoEjecucion
from apps.laboratorios.services.cliente_ejecutor import correr_casos_test, EjecutorNoDisponible


@extend_schema(
    tags=['Laboratorios'],
    summary='Ejecutar código contra los casos de test públicos',
    request=SerializadorEjecutarCodigo,
    responses={
        200: SerializadorResultadoEjecucion,
        400: OpenApiResponse(description='Datos inválidos'),
        403: OpenApiResponse(description='No estás inscrito en el curso de esta pregunta'),
        404: OpenApiResponse(description='Pregunta no encontrada'),
        503: OpenApiResponse(description='El servicio de ejecución no está disponible'),
    },
)
class VistaEjecutarCodigo(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, pregunta_id):
        try:
            pregunta = PreguntaCodigo.objects.select_related('laboratorio__curso').get(id=pregunta_id)
        except PreguntaCodigo.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        curso = pregunta.laboratorio.curso
        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        serializador = SerializadorEjecutarCodigo(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        casos_publicos = pregunta.casos_test.filter(es_publico=True)
        if not casos_publicos.exists():
            return Response(
                {'detalle': 'Esta pregunta no tiene casos de ejemplo públicos para probar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultados = correr_casos_test(pregunta, serializador.validated_data['codigo'], casos_publicos)
        except EjecutorNoDisponible:
            return Response(
                {'detalle': 'El servicio de ejecución de código no está disponible en este momento.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'casos_publicos_totales': len(resultados),
            'casos_publicos_pasados': sum(1 for r in resultados if r['paso']),
            'resultados': resultados,
        })
