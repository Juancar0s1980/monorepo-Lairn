"""
Vistas de integración NOVA (HU-03.1 / 03.2 en modo compatible).

- `POST /integracion/importar-url/`: `{url, modo, huella?}`. El servidor
  descarga el JSON con las defensas SSRF de `servicio_fuente_url`.
  `modo=real` exige la `huella` devuelta por la validación previa: si la
  fuente cambió entre validar y confirmar, responde 409 y no escribe.
- `POST /integracion/importar-json/`: `{datos, modo, fuente?, huella?}`
  para archivo .json o JSON pegado (contrato previo intacto).
  `modo=simulacro` valida sin escribir; `modo=real` hace upsert idempotente.
  Usuarios NO se crean ni modifican: solo se reportan.
- `GET /integracion/registros/`: bitácora auditable.
- El `sync` real contra NOVA queda tras feature flag: hoy responde
  501 intencional para no fingir una conexión que no existe.
"""

from rest_framework import generics, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import RegistroSincronizacion
from apps.evaluacion_resultados.serializers import SerializadorRegistroSync
from apps.evaluacion_resultados.services.servicio_fuente_url import (
    ErrorFuenteUrl,
    obtener_json_desde_url,
)
from apps.evaluacion_resultados.services.servicio_importador_nova import (
    ErrorImportacion,
    importar_programas_json,
)
from core.permissions.permisos_rol import EsAdministrador

ORIGEN_POR_FUENTE = {'pegado': 'api_nova_json', 'archivo': 'json_archivo'}


class LimiteImportacionUrl(UserRateThrottle):
    """Cada validación descarga un recurso externo: se limita por usuario."""

    scope = 'importacion_url'
    rate = '20/min'


class SerializadorImportacion(drf_serializers.Serializer):
    datos = drf_serializers.JSONField()
    modo = drf_serializers.ChoiceField(choices=['simulacro', 'real'], default='simulacro')
    fuente = drf_serializers.ChoiceField(choices=list(ORIGEN_POR_FUENTE), default='pegado')
    huella = drf_serializers.CharField(required=False, allow_blank=True, max_length=64)


class SerializadorImportacionUrl(drf_serializers.Serializer):
    url = drf_serializers.CharField(max_length=2000)
    modo = drf_serializers.ChoiceField(choices=['simulacro', 'real'], default='simulacro')
    huella = drf_serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate(self, attrs):
        if attrs['modo'] == 'real' and not attrs.get('huella'):
            raise drf_serializers.ValidationError(
                {'huella': 'Valida los datos antes de confirmar la importación.'}
            )
        return attrs


def _respuesta_error(exc: Exception) -> Response:
    return Response({'detalle': str(exc)}, status=getattr(exc, 'estado', 400))


class VistaImportarJson(APIView):
    permission_classes = [EsAdministrador]

    def post(self, request):
        serial = SerializadorImportacion(data=request.data)
        serial.is_valid(raise_exception=True)
        datos = serial.validated_data
        try:
            resumen = importar_programas_json(
                datos['datos'],
                modo=datos['modo'],
                ejecutado_por=request.user,
                origen=ORIGEN_POR_FUENTE[datos['fuente']],
                huella_esperada=datos.get('huella') or None,
            )
        except ErrorImportacion as exc:
            return _respuesta_error(exc)
        return Response(resumen, status=200)


class VistaImportarUrl(APIView):
    permission_classes = [EsAdministrador]
    throttle_classes = [LimiteImportacionUrl]

    def post(self, request):
        serial = SerializadorImportacionUrl(data=request.data)
        serial.is_valid(raise_exception=True)
        datos = serial.validated_data
        try:
            payload = obtener_json_desde_url(datos['url'])
            resumen = importar_programas_json(
                payload,
                modo=datos['modo'],
                ejecutado_por=request.user,
                origen='json_url',
                huella_esperada=datos.get('huella') or None,
            )
        except (ErrorFuenteUrl, ErrorImportacion) as exc:
            return _respuesta_error(exc)
        return Response(resumen, status=200)


class VistaListaRegistros(generics.ListAPIView):
    permission_classes = [EsAdministrador]
    queryset = RegistroSincronizacion.objects.all()[:100]
    serializer_class = SerializadorRegistroSync


class VistaSincronizarNova(APIView):
    """Placeholder honesto: sin credenciales/endpoint TI, no hay sync real."""

    permission_classes = [EsAdministrador]

    def post(self, request):
        return Response(
            {
                'detalle': (
                    'Sincronización NOVA aún no configurada (sin endpoint ni '
                    'credenciales TI). Usa importar-json en modo simulacro/real '
                    'o cargue documental mientras tanto. Todo queda bitacorado.'
                ),
            },
            status=501,
        )
