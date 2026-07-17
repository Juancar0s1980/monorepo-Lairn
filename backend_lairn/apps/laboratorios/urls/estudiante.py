"""
Rutas de la app `laboratorios` accedidas por el rol Estudiante.
"""

from django.urls import path
from apps.laboratorios.views import (
    VistaLaboratoriosCursoEstudiante,
    VistaDetalleLaboratorioEstudiante,
    VistaEjecutarCodigo,
    VistaEnviarCodigo,
    VistaMisEntregas,
)

urlpatterns = [
    # Listado de laboratorios disponibles en un curso donde el estudiante está inscrito.
    path('mis-cursos/<int:curso_id>/laboratorios/', VistaLaboratoriosCursoEstudiante.as_view(), name='laboratorios_curso_estudiante'),

    # Detalle de un laboratorio (preguntas sin casos de test ocultos).
    path('mis-cursos/<int:curso_id>/laboratorios/<int:laboratorio_id>/', VistaDetalleLaboratorioEstudiante.as_view(), name='detalle_laboratorio_estudiante'),

    # "Run": ejecuta el código del estudiante contra los casos de test públicos. No persiste nada.
    path('preguntas/<int:pregunta_id>/ejecutar/', VistaEjecutarCodigo.as_view(), name='ejecutar_codigo'),

    # "Submit": envío calificado contra TODOS los casos (públicos y ocultos). Persiste un intento.
    path('preguntas/<int:pregunta_id>/enviar/', VistaEnviarCodigo.as_view(), name='enviar_codigo'),

    # Historial de mis propias entregas para una pregunta (intentos usados/restantes).
    path('preguntas/<int:pregunta_id>/mis-entregas/', VistaMisEntregas.as_view(), name='mis_entregas'),
]
