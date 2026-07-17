"""
Modelo de dominio `EntregaCodigo`.

Un envío CALIFICADO (a diferencia de "Ejecutar", que solo corre contra los
casos públicos y no persiste nada). Corre el código del estudiante contra
TODOS los casos de test de la pregunta (públicos y ocultos) y guarda el
resultado. `intento` cuenta los envíos previos del mismo estudiante a la
misma pregunta — se usa para aplicar `Laboratorio.max_intentos`.

`resultados` guarda el detalle por caso (mismo shape que devuelve
`cliente_ejecutor.correr_casos_test`), pero la vista que expone esto al
estudiante redacta `salida_esperada`/`salida_obtenida` de los casos ocultos
antes de responder — el registro completo sí queda en la base para que el
docente pueda auditarlo.
"""

from django.conf import settings
from django.db import models


class EntregaCodigo(models.Model):
    pregunta = models.ForeignKey(
        'PreguntaCodigo',
        on_delete=models.CASCADE,
        related_name='entregas'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entregas_codigo'
    )
    codigo = models.TextField()
    resultados = models.JSONField(default=list, blank=True)
    casos_pasados = models.PositiveIntegerField(default=0)
    casos_totales = models.PositiveIntegerField(default=0)
    puntaje = models.FloatField(default=0.0, help_text='0-100, = casos_pasados/casos_totales * 100')
    intento = models.PositiveIntegerField(default=1)
    enviado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'entregas_codigo'
        ordering = ['-enviado_en']
