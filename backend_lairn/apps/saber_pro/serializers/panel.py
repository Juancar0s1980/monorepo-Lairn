"""
Serializadores de la respuesta del panel principal de Saber Pro (HU-16).

No están atados a un modelo: la lista de funcionalidades por rol se arma en
`apps.saber_pro.services.funcionalidades`, la invitación del estado vacío y el
flag de cursos en `apps.saber_pro.services.estado_panel`, y estos serializadores
solo les dan forma y los documentan en el schema de OpenAPI.

Campos de la respuesta (GET /api/saber-pro/panel/):
  - `rol`: nombre del rol del usuario ('Docente' | 'Estudiante').
  - `tiene_cursos`: False hasta que HU-17/18 persistan cursos Saber Pro; el
    front lo usa para alternar entre estado vacío y listado de cursos.
  - `accion_vacia`: invitación del estado vacío (HU-16.3), según el rol.
  - `funcionalidades`: avances de las herramientas del módulo (HU-19 a HU-24).
"""

from rest_framework import serializers


class SerializadorFuncionalidadSaberPro(serializers.Serializer):
    clave = serializers.CharField(help_text='Identificador estable de la funcionalidad, ej. "simulacros".')
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    disponible = serializers.BooleanField(
        help_text='False si la funcionalidad todavía no está implementada (se muestra como "Próximamente").'
    )


class SerializadorAccionVaciaSaberPro(serializers.Serializer):
    tipo = serializers.CharField(
        help_text='Tipo de acción del estado vacío: "crear_curso" (docente) o "unirse_codigo" (estudiante).'
    )
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    etiqueta_accion = serializers.CharField(
        help_text='Texto del botón de llamada a la acción, ej. "Crear curso".'
    )


class SerializadorPanelSaberPro(serializers.Serializer):
    rol = serializers.CharField()
    tiene_cursos = serializers.BooleanField(
        help_text='False mientras el usuario no tenga cursos Saber Pro (estado vacío, HU-16.3).'
    )
    accion_vacia = SerializadorAccionVaciaSaberPro(
        allow_null=True, required=False,
        help_text='Invitación a crear un curso (docente) o unirse con código (estudiante).',
    )
    funcionalidades = SerializadorFuncionalidadSaberPro(many=True)