"""
Vista de historial de entregas del estudiante para una pregunta, para el
rol Estudiante.

Expone `/laboratorios/preguntas/<pregunta_id>/mis-entregas/`: lista sus
propios envíos calificados (no el detalle de casos, solo el resumen de cada
intento) más cuántos intentos le quedan, para que la UI pueda mostrar
"2/3 intentos usados" antes de que envíe.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import Pregunta, Entrega


@extend_schema(
    tags=['Laboratorios'],
    summary='Historial de mis entregas para una pregunta',
    responses={
        200: OpenApiResponse(description='Entregas del estudiante autenticado para esa pregunta'),
        403: OpenApiResponse(description='No estás inscrito en este curso'),
        404: OpenApiResponse(description='Pregunta no encontrada'),
    },
)
class VistaMisEntregas(APIView):
    permission_classes = [EsEstudiante]

    def get(self, request, pregunta_id):
        try:
            pregunta = Pregunta.objects.select_related('laboratorio__curso').get(id=pregunta_id)
        except Pregunta.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        laboratorio = pregunta.laboratorio
        if not Inscripcion.objects.filter(estudiante=request.user, curso=laboratorio.curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        entregas = Entrega.objects.filter(pregunta=pregunta, estudiante=request.user).order_by('intento')
        datos = [
            {
                'id': e.id,
                'intento': e.intento,
                'casos_pasados': e.casos_pasados if pregunta.tipo == 'codigo' else None,
                'casos_totales': e.casos_totales if pregunta.tipo == 'codigo' else None,
                'puntaje': e.puntaje,
                'retroalimentacion': e.resultados.get('retroalimentacion') if pregunta.tipo == 'respuesta_libre' else None,
                'opcion_seleccionada': e.opcion_seleccionada if pregunta.tipo == 'problema_visual' else None,
                'transcripcion': e.resultados.get('transcripcion') if pregunta.tipo == 'pronunciacion' else None,
                'audio_respuesta': (request.build_absolute_uri(e.audio_respuesta.url)
                                     if pregunta.tipo == 'pronunciacion' and e.audio_respuesta else None),
                'enviado_en': e.enviado_en,
            }
            for e in entregas
        ]

        return Response({
            'entregas': datos,
            'max_intentos': laboratorio.max_intentos,
            'intentos_usados': len(datos),
            'intentos_restantes': (laboratorio.max_intentos - len(datos)) if laboratorio.max_intentos else None,
            'fecha_limite': laboratorio.fecha_limite,
        })
