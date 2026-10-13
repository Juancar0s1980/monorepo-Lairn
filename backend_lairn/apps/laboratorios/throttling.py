"""
Throttle específico de `VistaEnviarRespuesta`: esa vista atiende los 4 tipos
de pregunta en un solo endpoint, pero solo 'respuesta_libre' (agente
evaluador) y 'pronunciacion' (transcripción + comparación) llaman a un
proveedor de IA — 'codigo' corre en el sandbox del ejecutor y
'problema_visual' es una comparación exacta de índice, ninguno cuesta IA.

Aplicar el límite de IA a la vista completa penalizaría también los envíos
de código/problema_visual (probablemente el uso más frecuente del endpoint,
un estudiante reintentando un ejercicio de código muchas veces), así que
esta subclase solo cuenta contra el límite cuando la pregunta enviada es
efectivamente de un tipo que golpea al proveedor de IA.
"""

from apps.laboratorios.models import Pregunta
from core.throttling import ThrottleIA

TIPOS_QUE_LLAMAN_IA = {'respuesta_libre', 'pronunciacion'}


class ThrottleEnviarRespuesta(ThrottleIA):
    def allow_request(self, request, view):
        pregunta_id = view.kwargs.get('pregunta_id')
        tipo = Pregunta.objects.filter(id=pregunta_id).values_list('tipo', flat=True).first()
        if tipo not in TIPOS_QUE_LLAMAN_IA:
            return True
        return super().allow_request(request, view)
