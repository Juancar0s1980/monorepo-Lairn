"""
Vista del panel principal del módulo Saber Pro (HU-16).

Expone `GET /api/saber-pro/panel/`. A diferencia del resto de la plataforma
(exámenes, laboratorios, campo de estudio), este endpoint NO depende de que
el usuario esté inscrito o tenga un curso académico: cualquier Docente o
Estudiante autenticado puede consultarlo (HU-16.2).

Responde qué mostrar según el rol:
  - `funcionalidades`: avances del módulo (HU-19 a HU-24) desde
    `services.funcionalidades.obtener_funcionalidades`.
  - `tiene_cursos` y `accion_vacia`: estado vacío de HU-16.3 (invitación a
    crear curso para el docente o a unirse con código para el estudiante)
    desde `services.estado_panel`. Hasta que HU-17/18 persistan cursos, el
    panel siempre está en estado vacío.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsDocente, EsEstudiante
from apps.saber_pro.serializers import SerializadorPanelSaberPro
from apps.saber_pro.services.estado_panel import obtener_accion_vacia, obtener_tiene_cursos
from apps.saber_pro.services.funcionalidades import obtener_funcionalidades


@extend_schema(
    tags=['Saber Pro'],
    summary='Panel principal de Saber Pro (docente o estudiante)',
    description=(
        'Devuelve la información del panel del módulo Saber Pro para el rol del '
        'usuario autenticado: estado vacío (HU-16.3) y funcionalidades por rol. '
        'No depende de estar inscrito en un curso académico regular.'
    ),
    responses={
        200: SerializadorPanelSaberPro,
        403: OpenApiResponse(description='Solo Docentes y Estudiantes pueden acceder al módulo Saber Pro'),
    },
)
class VistaPanelSaberPro(APIView):
    permission_classes = [EsDocente | EsEstudiante]

    def get(self, request):
        rol_nombre = request.user.role.name if request.user.role else None
        funcionalidades = obtener_funcionalidades(rol_nombre)
        if not funcionalidades:
            return Response(
                {'detalle': 'Tu rol no tiene un panel de Saber Pro.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializador = SerializadorPanelSaberPro({
            'rol': rol_nombre,
            'tiene_cursos': obtener_tiene_cursos(request.user),
            'accion_vacia': obtener_accion_vacia(rol_nombre),
            'funcionalidades': funcionalidades,
        })
        return Response(serializador.data)