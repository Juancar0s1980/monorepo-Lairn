from django.urls import path
from apps.motor_adaptativo.views import VistaIniciarExamen, VistaResponder

urlpatterns = [
    path('iniciar/', VistaIniciarExamen.as_view(), name='iniciar_examen'),
    path('<int:sesion_id>/responder/', VistaResponder.as_view(), name='responder'),
]
