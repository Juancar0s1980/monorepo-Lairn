"""
Modelo de dominio `Entrega`.

Un envío CALIFICADO (a diferencia de "Ejecutar", que solo corre contra los
casos públicos y no persiste nada, y que solo aplica a `tipo='codigo'`).
`intento` cuenta los envíos previos del mismo estudiante a la misma
pregunta — se usa para aplicar `Laboratorio.max_intentos`.

`respuesta` guarda lo que escribió el estudiante: código/consulta si
`pregunta.tipo='codigo'`, o el texto libre del ensayo si
`tipo='respuesta_libre'` — el mismo campo sirve para ambos.

`resultados` guarda el detalle de la calificación, con forma distinta según
el tipo:
- `codigo`: detalle por caso de test (mismo shape que devuelve
  `cliente_ejecutor.correr_casos_test`); la vista que expone esto al
  estudiante redacta `salida_esperada`/`salida_obtenida` de los casos
  ocultos antes de responder.
- `respuesta_libre`: `{"retroalimentacion": "..."}` devuelto por
  `services/agente_evaluador.evaluar_respuesta_libre`; `casos_pasados`/
  `casos_totales` no aplican y quedan en 0.
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
    respuesta = models.TextField()
    resultados = models.JSONField(default=list, blank=True)
    casos_pasados = models.PositiveIntegerField(default=0)
    casos_totales = models.PositiveIntegerField(default=0)
    puntaje = models.FloatField(default=0.0, help_text='0-100. Código: casos_pasados/casos_totales * 100. Respuesta abierta: puntaje de la IA.')
    intento = models.PositiveIntegerField(default=1)
    enviado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'entregas_laboratorio'
        ordering = ['-enviado_en']
