"""
Modelo de dominio `Entrega`.

Un envío CALIFICADO (a diferencia de "Ejecutar", que solo corre contra los
casos públicos y no persiste nada, y que solo aplica a `tipo='codigo'`).
`intento` cuenta los envíos previos del mismo estudiante a la misma
pregunta — se usa para aplicar `Laboratorio.max_intentos`.

`respuesta` guarda lo que escribió el estudiante: código/consulta si
`pregunta.tipo='codigo'`, o el texto libre del ensayo si
`tipo='respuesta_libre'` — el mismo campo sirve para ambos. Va vacío si
`tipo='problema_visual'`: ahí lo que se guarda es `opcion_seleccionada`
(índice 0-3 de la variante asignada al estudiante, ver
`apps.laboratorios.models.AsignacionVariante`).

`resultados` guarda el detalle de la calificación, con forma distinta según
el tipo:
- `codigo`: detalle por caso de test (mismo shape que devuelve
  `cliente_ejecutor.correr_casos_test`); la vista que expone esto al
  estudiante redacta `salida_esperada`/`salida_obtenida` de los casos
  ocultos antes de responder.
- `respuesta_libre`: `{"retroalimentacion": "..."}` devuelto por
  `services/agente_evaluador.evaluar_respuesta_libre`; `casos_pasados`/
  `casos_totales` no aplican y quedan en 0.
- `problema_visual`: no aplica (`puntaje` es 0 o 100 según
  `opcion_seleccionada`, comparación exacta, sin IA de por medio).
- `pronunciacion`: `{"transcripcion": "..."}`, lo que Whisper entendió en
  `audio_respuesta`; `puntaje` es la similitud de texto contra
  `pregunta.texto_pronunciar` (ver `services/agente_pronunciacion.py`).
"""

from django.conf import settings
from django.db import models


class Entrega(models.Model):
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='entregas'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entregas_laboratorio'
    )
    respuesta = models.TextField(blank=True, default='')
    opcion_seleccionada = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Índice (0-3) de la opción elegida. Solo aplica si pregunta.tipo=problema_visual.'
    )
    audio_respuesta = models.FileField(
        upload_to='pronunciacion/respuestas/', null=True, blank=True,
        help_text='Grabación del estudiante. Solo aplica si pregunta.tipo=pronunciacion.'
    )
    resultados = models.JSONField(default=list, blank=True)
    casos_pasados = models.PositiveIntegerField(default=0)
    casos_totales = models.PositiveIntegerField(default=0)
    puntaje = models.FloatField(default=0.0, help_text='0-100. Código: casos_pasados/casos_totales * 100. Respuesta abierta: puntaje de la IA.')
    intento = models.PositiveIntegerField(default=1)
    enviado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'entregas_laboratorio'
        ordering = ['-enviado_en']
