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
    VistaFinalizarPractica,
    VistaMiProgresoLaboratorio,
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

    # Finaliza la práctica de un examen (laboratorio con `examen` vinculado) y combina la nota final.
    path('laboratorios/<int:laboratorio_id>/finalizar-practica/', VistaFinalizarPractica.as_view(), name='finalizar_practica'),

    # Mi progreso en el laboratorio: mejor puntaje por pregunta, para pintar el selector de un vistazo.
    path('laboratorios/<int:laboratorio_id>/mi-progreso/', VistaMiProgresoLaboratorio.as_view(), name='mi_progreso_laboratorio'),
]
