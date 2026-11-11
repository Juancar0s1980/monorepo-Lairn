from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views.vista_iniciar_sesion import VistaIniciarSesion
from apps.users.views.vista_acceso_google import VistaConfigAcceso, VistaIniciarSesionGoogle
from apps.users.views.vista_registrar import VistaRegistrar
from apps.users.views.vista_mis_datos import VistaMisDatos
from apps.users.views.vista_cerrar_sesion import VistaCerrarSesion
from apps.users.views.vista_lista_usuarios import VistaListaUsuarios
from apps.users.views.vista_detalle_usuario_admin import VistaDetalleUsuarioAdmin
from apps.users.views.vista_lista_roles import VistaListaRoles
from apps.users.views.vista_solicitar_recuperacion import VistaSolicitarRecuperacion
from apps.users.views.vista_restablecer_contrasena import VistaRestablecerContrasena
from apps.users.views.vista_solicitudes_cuenta import VistaResolverSolicitudCuenta, VistaSolicitudesCuenta

urlpatterns = [
    path('registrar/', VistaRegistrar.as_view(), name='registrar'),
    path('iniciar-sesion/', VistaIniciarSesion.as_view(), name='iniciar-sesion'),
    path('iniciar-sesion-google/', VistaIniciarSesionGoogle.as_view(), name='iniciar-sesion-google'),
    path('config-acceso/', VistaConfigAcceso.as_view(), name='config-acceso'),
    path('mis-datos/', VistaMisDatos.as_view(), name='mis-datos'),
    path('cerrar-sesion/', VistaCerrarSesion.as_view(), name='cerrar-sesion'),
    path('token/actualizar/', TokenRefreshView.as_view(), name='token-actualizar'),
    path('recuperar-contrasena/', VistaSolicitarRecuperacion.as_view(), name='recuperar-contrasena'),
    path('restablecer-contrasena/', VistaRestablecerContrasena.as_view(), name='restablecer-contrasena'),

    # Rutas accedidas por el rol Administrador (gestión de usuarios y roles).
    path('administracion/usuarios/', VistaListaUsuarios.as_view(), name='lista-usuarios'),
    path('administracion/usuarios/<int:usuario_id>/', VistaDetalleUsuarioAdmin.as_view(), name='detalle-usuario-admin'),
    path('administracion/solicitudes-cuenta/', VistaSolicitudesCuenta.as_view(), name='solicitudes-cuenta'),
    path('administracion/solicitudes-cuenta/<int:pk>/<str:accion>/', VistaResolverSolicitudCuenta.as_view(),
         name='resolver-solicitud-cuenta'),
    path('roles/', VistaListaRoles.as_view(), name='lista-roles'),
]
