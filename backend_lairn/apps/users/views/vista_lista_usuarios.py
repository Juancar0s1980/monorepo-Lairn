"""
Vista colección de usuarios para el rol Administrador.

Expone el endpoint `/administracion/usuarios/` con:
- GET: lista todos los usuarios del sistema con su rol asignado.
- POST: crea una cuenta institucional (HU-26). Con el acceso solo por Google, el registro público
  queda cerrado y el Administrador (o TI por importación) da de alta las cuentas. La cuenta se crea
  sin contraseña utilizable: solo inicia sesión con su cuenta Google institucional.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.users.models.user import User
from apps.users.serializers.serializador_gestion_usuario import SerializadorGestionUsuario
from apps.users.services.autenticacion_google import correo_institucional
from apps.users.views.vista_acceso_google import solo_institucional
from django.conf import settings
from rest_framework import status


@extend_schema(
    tags=['Usuarios'],
    summary='Listar usuarios',
    description='Retorna todos los usuarios del sistema con su rol asignado. Solo accesible para el Administrador.',
    responses={
        200: SerializadorGestionUsuario(many=True),
        403: OpenApiResponse(description='Solo el administrador puede acceder'),
    },
)
class VistaListaUsuarios(APIView):
    permission_classes = [EsAdministrador]

    # Lista todos los usuarios del sistema junto con su rol.
    def get(self, request):
        # Las cuentas sin rol son solicitudes administrativas sin aprobar: se gestionan en su propia bandeja.
        usuarios = User.objects.select_related('role').filter(role__isnull=False).order_by('email')
        serializador = SerializadorGestionUsuario(usuarios, many=True)
        return Response(serializador.data)

    # Alta de una cuenta institucional por el Administrador (HU-26).
    def post(self, request):
        datos = request.data
        correo = str(datos.get('email') or '').strip().lower()
        errores = {}
        if not correo or '@' not in correo:
            errores['email'] = ['Escribe un correo válido.']
        elif solo_institucional() and not correo_institucional(correo):
            dominios = ', '.join('@' + d for d in settings.DOMINIOS_INSTITUCIONALES)
            errores['email'] = [f'Usa un correo institucional ({dominios}).']
        elif User.objects.filter(email__iexact=correo).exists():
            errores['email'] = ['Ya existe una cuenta con ese correo.']
        for campo, texto in (('first_name', 'el primer nombre'), ('first_last_name', 'el primer apellido')):
            if not str(datos.get(campo) or '').strip():
                errores[campo] = [f'Escribe {texto}.']
        from apps.users.models.role import Role
        rol = Role.objects.filter(pk=datos.get('role_id')).first()
        if rol is None:
            errores['role_id'] = ['Elige el rol de la cuenta.']
        if errores:
            return Response(errores, status=status.HTTP_400_BAD_REQUEST)
        usuario = User.objects.create_user(
            email=correo, password=None, role=rol,
            first_name=str(datos['first_name']).strip()[:50], second_name=str(datos.get('second_name') or '').strip()[:50],
            first_last_name=str(datos['first_last_name']).strip()[:50],
            second_last_name=str(datos.get('second_last_name') or '').strip()[:50],
        )
        return Response(SerializadorGestionUsuario(usuario).data, status=status.HTTP_201_CREATED)
