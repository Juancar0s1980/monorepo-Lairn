"""
Vista "Enviar" (envío calificado), para el rol Estudiante.

A diferencia de "Ejecutar" (Run, solo contra los casos públicos, no
persiste nada — ver `vista_ejecutar_codigo.py`), esto corre el código
contra TODOS los casos de test (públicos y ocultos), calcula el puntaje y
GUARDA el resultado como un nuevo intento. Respeta `Laboratorio.max_intentos`
(0 = ilimitado) y `Laboratorio.fecha_limite`.

La respuesta redacta `salida_esperada`/`salida_obtenida` de los casos
OCULTOS (solo dice si pasó o no): el registro completo sí se guarda en la
base para que el docente pueda auditarlo, pero no tiene sentido revelarle
al estudiante el valor exacto de un test oculto solo porque envió código.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsEstudiante
from apps.examenes.models import Inscripcion
from apps.laboratorios.models import PreguntaCodigo, EntregaCodigo
from apps.laboratorios.serializers import SerializadorEjecutarCodigo
from apps.laboratorios.services.cliente_ejecutor import correr_casos_test, EjecutorNoDisponible


@extend_schema(
    tags=['Laboratorios'],
    summary='Enviar código para calificación (corre contra todos los casos, incluidos los ocultos)',
    request=SerializadorEjecutarCodigo,
    responses={
        200: OpenApiResponse(description='Resultado de la entrega calificada'),
        400: OpenApiResponse(description='Datos inválidos o la pregunta no tiene casos de test'),
        403: OpenApiResponse(description='No inscrito, límite de intentos alcanzado, o fecha límite superada'),
        404: OpenApiResponse(description='Pregunta no encontrada'),
        503: OpenApiResponse(description='El servicio de ejecución no está disponible'),
    },
)
class VistaEnviarCodigo(APIView):
    permission_classes = [EsEstudiante]

    def post(self, request, pregunta_id):
        try:
            pregunta = PreguntaCodigo.objects.select_related('laboratorio__curso').get(id=pregunta_id)
        except PreguntaCodigo.DoesNotExist:
            return Response({'detalle': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        laboratorio = pregunta.laboratorio
        curso = laboratorio.curso
        if not Inscripcion.objects.filter(estudiante=request.user, curso=curso).exists():
            return Response({'detalle': 'No estás inscrito en este curso.'}, status=status.HTTP_403_FORBIDDEN)

        if laboratorio.fecha_limite and timezone.now() > laboratorio.fecha_limite:
            return Response({'detalle': 'La fecha límite de este laboratorio ya pasó.'}, status=status.HTTP_403_FORBIDDEN)

        entregas_previas = EntregaCodigo.objects.filter(pregunta=pregunta, estudiante=request.user).count()
        if laboratorio.max_intentos and entregas_previas >= laboratorio.max_intentos:
            return Response(
                {'detalle': f'Alcanzaste el límite de {laboratorio.max_intentos} intento(s) para esta pregunta.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializador = SerializadorEjecutarCodigo(data=request.data)
        if not serializador.is_valid():
            return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

        casos = list(pregunta.casos_test.all())
        if not casos:
            return Response({'detalle': 'Esta pregunta no tiene casos de test definidos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultados = correr_casos_test(pregunta, serializador.validated_data['codigo'], casos)
        except EjecutorNoDisponible:
            return Response(
                {'detalle': 'El servicio de ejecución de código no está disponible en este momento.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        casos_pasados = sum(1 for r in resultados if r['paso'])
        casos_totales = len(resultados)
        puntaje = round(casos_pasados / casos_totales * 100, 1) if casos_totales else 0.0

        entrega = EntregaCodigo.objects.create(
            pregunta=pregunta,
            estudiante=request.user,
            codigo=serializador.validated_data['codigo'],
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
            'intento': entrega.intento,
            'intentos_restantes': (laboratorio.max_intentos - entrega.intento) if laboratorio.max_intentos else None,
            'resultados': resultados_redactados,
            'enviado_en': entrega.enviado_en,
        })
