from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views.vista_iniciar_sesion import VistaIniciarSesion
from apps.users.views.vista_registrar import VistaRegistrar
from apps.users.views.vista_mis_datos import VistaMisDatos
from apps.users.views.vista_cerrar_sesion import VistaCerrarSesion

urlpatterns = [
    path('registrar/', VistaRegistrar.as_view(), name='registrar'),
    path('iniciar-sesion/', VistaIniciarSesion.as_view(), name='iniciar-sesion'),
    path('mis-datos/', VistaMisDatos.as_view(), name='mis-datos'),
    path('cerrar-sesion/', VistaCerrarSesion.as_view(), name='cerrar-sesion'),
    path('token/actualizar/', TokenRefreshView.as_view(), name='token-actualizar'),
]
