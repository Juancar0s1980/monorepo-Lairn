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
- `problema_visual`: opción múltiple, sin IA de por medio en este paso. Se
  compara `opcion_seleccionada` contra `respuesta_correcta` de la variante
  ya asignada al estudiante (`AsignacionVariante.obtener_o_asignar`) —
  comparación exacta, instantánea.
- `pronunciacion`: multipart con `audio` (la grabación del estudiante). Se
  transcribe con Whisper (`agente_pronunciacion.transcribir_audio`) y se
  compara el texto contra `pregunta.texto_pronunciar`
  (`agente_pronunciacion.calcular_similitud`) para el puntaje.
"""

import openai
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import Pregunta, Entrega, AsignacionVariante
from apps.laboratorios.serializers import SerializadorEnviarRespuesta
from apps.laboratorios.services.cliente_ejecutor import correr_casos_test, EjecutorNoDisponible
from apps.laboratorios.services.agente_evaluador import evaluar_respuesta_libre
from apps.laboratorios.services.agente_pronunciacion import transcribir_audio, calcular_similitud


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

        if pregunta.tipo == 'problema_visual':
            return self._enviar_problema_visual(
                pregunta, laboratorio, request.user, request.data.get('opcion_seleccionada'), entregas_previas
            )

        if pregunta.tipo == 'pronunciacion':
            return self._enviar_pronunciacion(
                pregunta, laboratorio, request.user, request.FILES.get('audio'), entregas_previas
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

    def _enviar_pronunciacion(self, pregunta, laboratorio, estudiante, audio, entregas_previas):
        if audio is None:
            return Response({'detalle': 'Falta el archivo "audio" con la grabación.'}, status=status.HTTP_400_BAD_REQUEST)

        audio_bytes = audio.read()
        audio.seek(0)
        try:
            transcripcion = transcribir_audio(audio_bytes, audio.name)
        except openai.APIError as e:
            return Response({'detalle': f'No se pudo transcribir el audio: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        puntaje = calcular_similitud(pregunta.texto_pronunciar, transcripcion)

        entrega = Entrega.objects.create(
            pregunta=pregunta,
            estudiante=estudiante,
            respuesta='',
            audio_respuesta=audio,
            resultados={'transcripcion': transcripcion},
            puntaje=puntaje,
            intento=entregas_previas + 1,
        )

        return Response({
            'id': entrega.id,
            'casos_pasados': None,
            'casos_totales': None,
            'puntaje': entrega.puntaje,
            'retroalimentacion': None,
            'transcripcion': transcripcion,
            'intento': entrega.intento,
            'intentos_restantes': (laboratorio.max_intentos - entrega.intento) if laboratorio.max_intentos else None,
            'resultados': [],
            'enviado_en': entrega.enviado_en,
        })

    def _enviar_problema_visual(self, pregunta, laboratorio, estudiante, opcion_seleccionada, entregas_previas):
        if not isinstance(opcion_seleccionada, int) or not (0 <= opcion_seleccionada <= 3):
            return Response({'detalle': '"opcion_seleccionada" debe ser un entero entre 0 y 3.'}, status=status.HTTP_400_BAD_REQUEST)

        asignacion = AsignacionVariante.obtener_o_asignar(pregunta, estudiante)
        if asignacion is None:
            return Response({'detalle': 'Esta pregunta todavía no tiene variantes generadas.'}, status=status.HTTP_400_BAD_REQUEST)

        puntaje = 100.0 if opcion_seleccionada == asignacion.variante.respuesta_correcta else 0.0

        entrega = Entrega.objects.create(
            pregunta=pregunta,
            estudiante=estudiante,
            respuesta='',
            opcion_seleccionada=opcion_seleccionada,
            puntaje=puntaje,
            intento=entregas_previas + 1,
        )

        return Response({
            'id': entrega.id,
            'casos_pasados': None,
            'casos_totales': None,
            'puntaje': entrega.puntaje,
            'retroalimentacion': None,
            'opcion_seleccionada': opcion_seleccionada,
            'respuesta_correcta': asignacion.variante.respuesta_correcta,
            'intento': entrega.intento,
            'intentos_restantes': (laboratorio.max_intentos - entrega.intento) if laboratorio.max_intentos else None,
            'resultados': [],
            'enviado_en': entrega.enviado_en,
        })
