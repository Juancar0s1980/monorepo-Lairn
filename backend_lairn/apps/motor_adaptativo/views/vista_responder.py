from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
from core.permissions.permisos_rol import EsEstudiante
from apps.motor_adaptativo.models import SesionExamen, ModeloConocimiento
from apps.motor_adaptativo.serializers import SerializadorResponder
from apps.motor_adaptativo.services.agente_ia import generar_pregunta, actualizar_modelo_conocimiento
from apps.analitica.models import Resultado, RespuestaEstudiante


def _ajustar_dificultad(sesion, es_correcta):
    if es_correcta and sesion.dificultad_actual < 3:
        sesion.dificultad_actual += 1
    elif not es_correcta and sesion.dificultad_actual > 1:
        sesion.dificultad_actual -= 1


def _debe_terminar(sesion, modelo_conceptos):
    """
    Decide si el examen debe terminar según el modo configurado.
    Retorna (terminar: bool, razon: str)
    """
    examen = sesion.examen
    respondidas = sesion.preguntas_respondidas

    if examen.modo == 'maestria':
        limite_alcanzado = respondidas >= examen.max_preguntas
        minimo_cumplido = respondidas >= examen.num_preguntas
        todos_dominados = (
            bool(modelo_conceptos) and
            all(d['nivel'] >= 3 for d in modelo_conceptos.values())
        )

        if limite_alcanzado:
            return True, 'limite_alcanzado'
        if minimo_cumplido and todos_dominados:
            return True, 'conceptos_dominados'
        return False, ''

    # Modo fijo
    if respondidas >= examen.num_preguntas:
        return True, 'preguntas_completadas'
    return False, ''


_EN_PROGRESO = 'Presente cuando completado=false'
_COMPLETADO = 'Presente cuando completado=true'

_RESPUESTA_RESPONDER = inline_serializer(
    name='RespuestaResponder',
    fields={
        'completado': drf_serializers.BooleanField(
            help_text='false=siguiente pregunta incluida, true=examen finalizado'
        ),
        'es_correcta': drf_serializers.BooleanField(help_text=_EN_PROGRESO),
        'concepto_evaluado': drf_serializers.CharField(help_text=_EN_PROGRESO),
        'pregunta_numero': drf_serializers.IntegerField(help_text=_EN_PROGRESO),
        'dificultad_actual': drf_serializers.IntegerField(help_text='1=Fácil 2=Medio 3=Difícil'),
        'pregunta': drf_serializers.CharField(help_text=_EN_PROGRESO),
        'opciones': drf_serializers.ListField(
            child=drf_serializers.CharField(),
            help_text=_EN_PROGRESO,
        ),
        'retroalimentacion': drf_serializers.DictField(
            help_text='Presente si retroalimentacion=true en el examen, null si no',
            allow_empty=True,
        ),
        'total_preguntas': drf_serializers.IntegerField(help_text='Solo en modo fijo'),
        'max_preguntas': drf_serializers.IntegerField(help_text='Solo en modo maestría'),
        'min_preguntas': drf_serializers.IntegerField(help_text='Solo en modo maestría'),
        'conceptos_pendientes': drf_serializers.ListField(
            child=drf_serializers.CharField(),
            help_text='Solo en modo maestría: conceptos aún no dominados',
        ),
        'explicacion': drf_serializers.CharField(help_text='Solo si es_guiado=true'),
        'razon_fin': drf_serializers.CharField(
            help_text=f'{_COMPLETADO}: preguntas_completadas | conceptos_dominados | limite_alcanzado'
        ),
        'puntaje': drf_serializers.FloatField(help_text=f'{_COMPLETADO}. Rango 0–100'),
        'nota': drf_serializers.FloatField(help_text=f'{_COMPLETADO}. Rango 1.0–5.0'),
        'correctas': drf_serializers.IntegerField(help_text=_COMPLETADO),
        'estado_conceptos': drf_serializers.DictField(
            help_text=f'{_COMPLETADO}. Mapa concepto→{{nivel, intentos, correctas}}'
        ),
    },
)


@extend_schema(
    tags=['Motor Adaptativo'],
    summary='Responder pregunta del examen',
    description=(
        'Envía la respuesta del estudiante a la pregunta activa de la sesión. '
        'El motor adaptativo evalúa la respuesta, ajusta la dificultad y genera la siguiente pregunta.\n\n'
        '**Cuando `completado=false`:** se incluye la siguiente pregunta.\n'
        '**Cuando `completado=true`:** se incluye `puntaje`, `nota` y `estado_conceptos`.\n\n'
        '**Razones de finalización (`razon_fin`):**\n'
        '- `preguntas_completadas`: modo fijo, se respondieron todas las preguntas.\n'
        '- `conceptos_dominados`: modo maestría, todos los conceptos tienen nivel 3.\n'
        '- `limite_alcanzado`: modo maestría, se alcanzó `max_preguntas`.'
    ),
    parameters=[
        OpenApiParameter('sesion_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='ID de la sesión de examen'),
    ],
    request=SerializadorResponder,
    examples=[
        OpenApiExample(
            name='Enviar respuesta',
            value={'respuesta': 'cos(x)', 'tiempo_segundos': 15},
            request_only=True,
        ),
    ],
    responses={
        200: _RESPUESTA_RESPONDER,
        400: OpenApiResponse(description='Examen ya completado, sin pregunta activa o datos inválidos'),
        404: OpenApiResponse(description='Sesión no encontrada'),
    },
)
class VistaResponder(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, sesion_id):
        serializador = SerializadorResponder(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            sesion = SesionExamen.objects.get(id=sesion_id, estudiante=request.user)
        except SesionExamen.DoesNotExist:
            return Response({'detalle': 'Sesión no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if sesion.estado == 'completado':
            return Response({'detalle': 'Este examen ya fue completado.'}, status=status.HTTP_400_BAD_REQUEST)

        if sesion.pregunta_actual is None:
            return Response({'detalle': 'No hay pregunta activa.'}, status=status.HTTP_400_BAD_REQUEST)

        respuesta = serializador.validated_data['respuesta']
        tiempo = serializador.validated_data['tiempo_segundos']
        pregunta_actual = sesion.pregunta_actual
        es_correcta = respuesta == pregunta_actual['respuesta_correcta']
        concepto = pregunta_actual.get('concepto', '')

        resultado, _ = Resultado.objects.get_or_create(
            sesion=sesion,
            defaults={
                'estudiante': request.user,
                'examen': sesion.examen,
                'total_preguntas': sesion.examen.num_preguntas,
            }
        )

        RespuestaEstudiante.objects.create(
            resultado=resultado,
            concepto=concepto,
            pregunta=pregunta_actual['pregunta'],
            respuesta_correcta=pregunta_actual['respuesta_correcta'],
            respuesta_incorrecta='' if es_correcta else respuesta,
            tiempo_por_pregunta=tiempo,
            dificultad=sesion.dificultad_actual,
        )

        if es_correcta:
            resultado.correctas += 1
            resultado.save()

        sesion.preguntas_respondidas += 1
        _ajustar_dificultad(sesion, es_correcta)

        # Actualizar modelo de conocimiento
        modelo, _ = ModeloConocimiento.objects.get_or_create(
            estudiante=request.user,
            examen=sesion.examen,
            defaults={'conceptos': {}}
        )
        if concepto:
            modelo.conceptos = actualizar_modelo_conocimiento(modelo.conceptos, concepto, es_correcta)
            modelo.save()

        retroalimentacion = None
        if sesion.examen.retroalimentacion:
            retroalimentacion = {
                'es_correcta': es_correcta,
                'respuesta_correcta': pregunta_actual['respuesta_correcta'],
                'concepto': concepto,
            }

        terminar, razon = _debe_terminar(sesion, modelo.conceptos)

        if terminar:
            sesion.estado = 'completado'
            sesion.completado_en = timezone.now()
            sesion.pregunta_actual = None
            sesion.save()

            # En modo maestría el total real puede diferir del inicial
            total_real = sesion.preguntas_respondidas
            resultado.total_preguntas = total_real
            resultado.puntaje = round((resultado.correctas / total_real) * 100, 2)
            resultado.nota = round(1.0 + (resultado.correctas / total_real) * 4.0, 1)
            resultado.save()

            estado_conceptos = {
                nombre: {
                    'nivel': datos['nivel'],
                    'intentos': datos['intentos'],
                    'correctas': datos['correctas'],
                }
                for nombre, datos in modelo.conceptos.items()
            }

            return Response({
                'completado': True,
                'razon_fin': razon,
                'puntaje': resultado.puntaje,
                'nota': resultado.nota,
                'correctas': resultado.correctas,
                'total_preguntas': total_real,
                'estado_conceptos': estado_conceptos,
                'retroalimentacion': retroalimentacion,
            })

        historial = list(
            RespuestaEstudiante.objects.filter(resultado=resultado).values('pregunta')
        )
        siguiente = generar_pregunta(
            sesion.examen.tema,
            sesion.dificultad_actual,
            historial,
            guiado=sesion.examen.es_guiado,
            modelo_conocimiento=modelo.conceptos
        )
        sesion.pregunta_actual = siguiente
        sesion.save()

        respuesta_data = {
            'completado': False,
            'es_correcta': es_correcta,
            'concepto_evaluado': concepto,
            'pregunta_numero': sesion.preguntas_respondidas + 1,
            'dificultad_actual': sesion.dificultad_actual,
            'pregunta': siguiente['pregunta'],
            'opciones': siguiente['opciones'],
            'retroalimentacion': retroalimentacion,
        }

        # En modo maestría no hay total fijo — mostrar el máximo como referencia
        if sesion.examen.modo == 'maestria':
            respuesta_data['max_preguntas'] = sesion.examen.max_preguntas
            respuesta_data['min_preguntas'] = sesion.examen.num_preguntas
            conceptos_debiles = [
                n for n, d in modelo.conceptos.items() if d['nivel'] < 3
            ]
            respuesta_data['conceptos_pendientes'] = conceptos_debiles
        else:
            respuesta_data['total_preguntas'] = sesion.examen.num_preguntas

        if sesion.examen.es_guiado:
            respuesta_data['explicacion'] = siguiente.get('explicacion', '')

        return Response(respuesta_data)
