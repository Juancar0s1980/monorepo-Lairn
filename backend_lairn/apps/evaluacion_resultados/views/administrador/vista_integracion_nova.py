"""
Vistas de integración NOVA (HU-03.1 / 03.2 en modo compatible).

- `POST /integracion/importar-json/`: recibe el JSON del correo TI.
  `modo=simulacro` valida sin escribir (para la sesión con TI);
  `modo=real` hace upsert idempotente de programas/asignaturas.
  Usuarios NO se auto-crean en real (seguridad): se reportan.
- `GET /integracion/registros/`: bitácora auditable.
- El `sync` real contra NOVA queda tras feature flag: hoy responde
  501 intencional para no fingir una conexión que no existe.
"""

from rest_framework import generics, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import RegistroSincronizacion
from apps.evaluacion_resultados.serializers import SerializadorRegistroSync
from apps.evaluacion_resultados.services.servicio_importador_nova import (
    importar_programas_json,
)
from core.permissions.permisos_rol import EsAdministrador


class SerializadorImportacion(drf_serializers.Serializer):
    datos = drf_serializers.JSONField()
    modo = drf_serializers.ChoiceField(choices=['simulacro', 'real'], default='simulacro')


class VistaImportarJson(APIView):
    permission_classes = [EsAdministrador]

    def post(self, request):
        serial = SerializadorImportacion(data=request.data)
        serial.is_valid(raise_exception=True)
        resumen = importar_programas_json(
            serial.validated_data['datos'],
            modo=serial.validated_data['modo'],
            ejecutado_por=request.user,
        )
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
