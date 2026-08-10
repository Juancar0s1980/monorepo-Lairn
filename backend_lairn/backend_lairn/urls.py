"""
URL configuration for backend_Peseudotutor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.utils.vista_media_con_rango import servir_media_con_rango

urlpatterns = [
    path('api/usuarios/', include('apps.users.urls')),
    path('api/analitica/', include('apps.analitica.urls')),
    path('api/motor-adaptativo/', include('apps.motor_adaptativo.urls')),
    path('api/examenes/', include('apps.examenes.urls')),
    path('api/moderacion/', include('apps.moderacion.urls')),
    path('api/laboratorios/', include('apps.laboratorios.urls')),
    path('api/campo-estudio/', include('apps.campo_estudio.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    # `view=servir_media_con_rango` en vez del default `django.views.static.serve`:
    # ese soporta Range requests (necesario para que <audio>/<video> reproduzcan
    # bien en el navegador), el default de Django siempre devuelve el archivo
    # completo con 200 sin importar el header Range.
    urlpatterns += static(settings.MEDIA_URL, view=servir_media_con_rango, document_root=settings.MEDIA_ROOT)
