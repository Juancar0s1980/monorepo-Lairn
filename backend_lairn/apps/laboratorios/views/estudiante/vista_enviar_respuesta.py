"""
Vista "Enviar" (envío calificado), para el rol Estudiante.

A diferencia de "Ejecutar" (Run, solo contra los casos públicos, no
persiste nada, y solo aplica a `tipo='codigo'` — ver
`vista_ejecutar_codigo.py`), esto SIEMPRE persiste un nuevo intento
(`Entrega`) y respeta `Laboratorio.max_intentos` (0 = ilimitado) y
`Laboratorio.fecha_limite`, para cualquier tipo de pregunta.

La calificación se bifurca por `pregunta.tipo`:
- `codigo`: corre `respuesta` contra TODOS los casos de test (públicos y
  ocultos) en el sandbox del ejecutor, igual que siempre. La respuesta
  redacta `salida_esperada`/`salida_obtenida` de los casos OCULTOS (solo
  dice si pasó o no) — el registro completo sí se guarda en la base.
- `respuesta_libre`: no hay nada que ejecutar. Se llama a
  `agente_evaluador.evaluar_respuesta_libre` con la rúbrica
  (`pregunta.criterios_ia`) y se guarda el puntaje + retroalimentación que
  devuelve la IA.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import Pregunta, Entrega
from apps.laboratorios.serializers import SerializadorEnviarRespuesta
from apps.laboratorios.services.cliente_ejecutor import correr_casos_test, EjecutorNoDisponible
from apps.laboratorios.services.agente_evaluador import evaluar_respuesta_libre


@extend_schema(
    tags=['Laboratorios'],
    summary='Enviar respuesta para calificación (código: corre todos los casos; respuesta abierta: la califica la IA)',
    request=SerializadorEnviarRespuesta,
    responses={
        200: OpenApiResponse(description='Resultado de la entrega calificada'),
        400: OpenApiResponse(description='Datos inválidos o la pregunta no tiene casos de test'),
        403: OpenApiResponse(description='No inscrito, límite de intentos alcanzado, o fecha límite superada'),
        404: OpenApiResponse(description='Pregunta no encontrada'),
        502: OpenApiResponse(description='La IA no pudo calificar la respuesta'),
        503: OpenApiResponse(description='El servicio de ejecución no está disponible'),
    },
)
class VistaEnviarRespuesta(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, pregunta_id):
        try:
            pregunta = Pregunta.objects.select_related('laboratorio__curso').get(id=pregunta_id)
        except Pregunta.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        laboratorio = pregunta.laboratorio
        curso = laboratorio.curso
        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        if laboratorio.fecha_limite and timezone.now() > laboratorio.fecha_limite:
            return Response({'detalle': 'La fecha límite de este laboratorio ya pasó.'}, status=status.HTTP_403_FORBIDDEN)

        entregas_previas = Entrega.objects.filter(pregunta=pregunta, estudiante=request.user).count()
        if laboratorio.max_intentos and entregas_previas >= laboratorio.max_intentos:
            return Response(
                {'detalle': f'Alcanzaste el límite de {laboratorio.max_intentos} intento(s) para esta pregunta.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializador = SerializadorEnviarRespuesta(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
        respuesta_texto = serializador.validated_data['respuesta']

        if pregunta.tipo == 'respuesta_libre':
            return self._enviar_respuesta_libre(pregunta, laboratorio, request.user, respuesta_texto, entregas_previas)
        return self._enviar_codigo(pregunta, laboratorio, request.user, respuesta_texto, entregas_previas)

    def _enviar_codigo(self, pregunta, laboratorio, estudiante, codigo, entregas_previas):
        casos = list(pregunta.casos_test.all())
        if not casos:
            return Response({'detalle': 'Esta pregunta no tiene casos de test definidos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultados = correr_casos_test(pregunta, codigo, casos)
        except EjecutorNoDisponible:
            return Response(
                {'detalle': 'El servicio de ejecución de código no está disponible en este momento.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        casos_pasados = sum(1 for r in resultados if r['paso'])
        casos_totales = len(resultados)
        puntaje = round(casos_pasados / casos_totales * 100, 1) if casos_totales else 0.0

        entrega = Entrega.objects.create(
            pregunta=pregunta,
            estudiante=estudiante,
            respuesta=codigo,
            resultados=resultados,
            casos_pasados=casos_pasados,
            casos_totales=casos_totales,
            puntaje=puntaje,
            intento=entregas_previas + 1,
        )

        resultados_redactados = [
            r if r['es_publico'] else {
                'caso_test_id': r['caso_test_id'],
                'es_publico': False,
                'paso': r['paso'],
                'salida_obtenida': None,
                'salida_esperada': None,
                'stderr': r['stderr'] if not r['paso'] else '',
                'timeout': r['timeout'],
            }
            for r in resultados
        ]

        return Response({
            'id': entrega.id,
            'casos_pasados': casos_pasados,
            'casos_totales': casos_totales,
            'puntaje': puntaje,
            'retroalimentacion': None,
            'intento': entrega.intento,
            'intentos_restantes': (laboratorio.max_intentos - entrega.intento) if laboratorio.max_intentos else None,
            'resultados': resultados_redactados,
            'enviado_en': entrega.enviado_en,
        })

    def _enviar_respuesta_libre(self, pregunta, laboratorio, estudiante, texto, entregas_previas):
        try:
            evaluacion = evaluar_respuesta_libre(pregunta.enunciado, pregunta.criterios_ia, texto)
        except ValueError as e:
            return Response({'detalle': f'La IA no pudo calificar la respuesta: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        entrega = Entrega.objects.create(
            pregunta=pregunta,
            estudiante=estudiante,
            respuesta=texto,
            resultados={'retroalimentacion': evaluacion['retroalimentacion']},
            puntaje=evaluacion['puntaje'],
            intento=entregas_previas + 1,
        )

        return Response({
            'id': entrega.id,
            'casos_pasados': None,
            'casos_totales': None,
            'puntaje': entrega.puntaje,
            'retroalimentacion': evaluacion['retroalimentacion'],
            'intento': entrega.intento,
            'intentos_restantes': (laboratorio.max_intentos - entrega.intento) if laboratorio.max_intentos else None,
            'resultados': [],
            'enviado_en': entrega.enviado_en,
        })
