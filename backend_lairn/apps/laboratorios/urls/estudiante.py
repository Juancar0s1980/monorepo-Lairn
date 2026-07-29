"""
Rutas de la app `laboratorios` accedidas por el rol Estudiante.
"""

from django.urls import path
from apps.laboratorios.views import (
    VistaLaboratoriosCursoEstudiante,
    VistaDetalleLaboratorioEstudiante,
    VistaEjecutarCodigo,
    VistaEnviarRespuesta,
    VistaMisEntregas,
)

urlpatterns = [
    # Listado de laboratorios disponibles en un curso donde el estudiante está inscrito.
    path('mis-cursos/<int:curso_id>/laboratorios/', VistaLaboratoriosCursoEstudiante.as_view(), name='laboratorios_curso_estudiante'),

    # Detalle de un laboratorio (preguntas sin casos de test ocultos).
    path('mis-cursos/<int:curso_id>/laboratorios/<int:laboratorio_id>/', VistaDetalleLaboratorioEstudiante.as_view(), name='detalle_laboratorio_estudiante'),

    # "Run": ejecuta el código del estudiante contra los casos de test públicos. Solo tipo=codigo. No persiste nada.
    path('preguntas/<int:pregunta_id>/ejecutar/', VistaEjecutarCodigo.as_view(), name='ejecutar_codigo'),

    # "Submit": envío calificado (código: todos los casos; respuesta abierta: la IA la califica). Persiste un intento.
    path('preguntas/<int:pregunta_id>/enviar/', VistaEnviarRespuesta.as_view(), name='enviar_respuesta'),

    # Historial de mis propias entregas para una pregunta (intentos usados/restantes).
    path('preguntas/<int:pregunta_id>/mis-entregas/', VistaMisEntregas.as_view(), name='mis_entregas'),
]
