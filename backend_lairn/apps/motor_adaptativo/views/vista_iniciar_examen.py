from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiExample
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Examen, Inscripcion
from apps.motor_adaptativo.models import SesionExamen, ModeloConocimiento
from apps.motor_adaptativo.serializers import SerializadorIniciarExamen
from apps.motor_adaptativo.services.agente_ia import generar_pregunta


@extend_schema(
    tags=['Motor Adaptativo'],
    summary='Iniciar o reanudar examen',
    description=(
        'Inicia una nueva sesión de examen o reanuda una sesión en progreso. '
        'Si el estudiante ya tiene una sesión activa para ese examen, la retoma desde donde la dejó. '
        'El agente de IA genera la primera pregunta adaptada al modelo de conocimiento previo del estudiante.\n\n'
        '**Modos de respuesta:**\n'
        '- `fijo`: incluye `total_preguntas` (número exacto).\n'
        '- `maestria`: incluye `min_preguntas` y `max_preguntas`.\n'
        '- Si `es_guiado=true`: incluye `explicacion` del concepto antes de cada pregunta.'
    ),
    request=SerializadorIniciarExamen,
    examples=[
        OpenApiExample(
            name='Iniciar examen 1',
            value={'examen_id': 1},
            request_only=True,
        ),
    ],
    responses={
        200: inline_serializer(
            name='RespuestaIniciarExamen',
            fields={
                'sesion_id': drf_serializers.IntegerField(),
                'modo': drf_serializers.CharField(),
                'intento_actual': drf_serializers.IntegerField(),
                'intentos_completados': drf_serializers.IntegerField(),
                'max_intentos': drf_serializers.IntegerField(help_text='0 = ilimitado'),
                'tiempo_total_minutos': drf_serializers.IntegerField(),
                'dificultad_actual': drf_serializers.IntegerField(help_text='1=Fácil 2=Medio 3=Difícil'),
                'pregunta_numero': drf_serializers.IntegerField(),
                'pregunta': drf_serializers.CharField(),
                'opciones': drf_serializers.ListField(child=drf_serializers.CharField()),
                'total_preguntas': drf_serializers.IntegerField(help_text='Solo en modo fijo'),
                'min_preguntas': drf_serializers.IntegerField(help_text='Solo en modo maestría'),
                'max_preguntas': drf_serializers.IntegerField(help_text='Solo en modo maestría'),
                'explicacion': drf_serializers.CharField(help_text='Solo si es_guiado=true'),
            },
        ),
        400: OpenApiResponse(description='Agotaste los intentos permitidos o datos inválidos'),
        403: OpenApiResponse(description='No estás inscrito en el curso de este examen'),
        404: OpenApiResponse(description='Examen no encontrado'),
    },
)
class VistaIniciarExamen(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request):
        serializador = SerializadorIniciarExamen(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            examen = Examen.objects.get(id=serializador.validated_data['examen_id'])
        except Examen.DoesNotExist:
            return Response({'detalle': 'Examen no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not Inscripcion.objects.filter(estudiante=request.user, curso=examen.curso).exists():
            return Response(
                {'detalle': 'No estás inscrito en el curso de este examen.'},
                status=status.HTTP_403_FORBIDDEN
            )

        intentos_completados = SesionExamen.objects.filter(
            estudiante=request.user, examen=examen, estado='completado'
        ).count()

        if examen.max_intentos != 0 and intentos_completados >= examen.max_intentos:
            return Response(
                {'detalle': f'Agotaste los {examen.max_intentos} intento(s) permitidos para este examen.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sesion = SesionExamen.objects.filter(
            estudiante=request.user, examen=examen, estado='en_progreso'
        ).first()

        if not sesion:
            sesion = SesionExamen.objects.create(
                estudiante=request.user,
                examen=examen,
                dificultad_actual=examen.dificultad_inicial,
                intento=intentos_completados + 1
            )

        if sesion.pregunta_actual is None:
            modelo = ModeloConocimiento.objects.filter(
                estudiante=request.user, examen=examen
            ).first()
            modelo_conceptos = modelo.conceptos if modelo else None

            pregunta = generar_pregunta(
                examen.tema,
                sesion.dificultad_actual,
                [],
                guiado=examen.es_guiado,
                modelo_conocimiento=modelo_conceptos
            )
            sesion.pregunta_actual = pregunta
            sesion.save()

        respuesta_data = {
            'sesion_id': sesion.id,
            'modo': examen.modo,
            'intento_actual': sesion.intento,
            'intentos_completados': intentos_completados,
            'max_intentos': examen.max_intentos,
            'tiempo_total_minutos': examen.tiempo,
            'dificultad_actual': sesion.dificultad_actual,
            'pregunta_numero': sesion.preguntas_respondidas + 1,
            'pregunta': sesion.pregunta_actual['pregunta'],
            'opciones': sesion.pregunta_actual['opciones'],
        }

        if examen.modo == 'maestria':
            respuesta_data['min_preguntas'] = examen.num_preguntas
            respuesta_data['max_preguntas'] = examen.max_preguntas
        else:
            respuesta_data['total_preguntas'] = examen.num_preguntas

        if examen.es_guiado:
            respuesta_data['explicacion'] = sesion.pregunta_actual.get('explicacion', '')

        return Response(respuesta_data)
