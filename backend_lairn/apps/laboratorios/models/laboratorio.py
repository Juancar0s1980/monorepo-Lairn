"""
Modelo de dominio `Laboratorio`.

Un laboratorio es una actividad de código independiente del `Examen`
adaptativo: el docente la crea de antemano con preguntas y casos de test
curados, y el estudiante la resuelve en una página tipo "juez en línea"
(editor de código + ejecución contra casos de prueba), sin pasar por el
motor de generación de preguntas por IA en tiempo real.

No se conecta a `Examen`, `SesionExamen` ni `Resultado`: es un sistema
hermano que cuelga de `Curso`, igual que `Examen`.

`tema_estudio` es opcional: si está presente, este laboratorio es la
práctica ligada a ese tema del Campo de Estudio (generado desde ahí, ver
`apps.campo_estudio`) y el estudiante puede llegar a él con un botón
"Practicar" desde el chat del tema, además de verlo en el tab Laboratorios
normal del curso (sigue teniendo `curso`, no es un sistema aparte). Un
laboratorio sin `tema_estudio` es un laboratorio "suelto" de siempre.
"""

from django.db import models


class Laboratorio(models.Model):
    curso = models.ForeignKey(
        'examenes.Curso',
        on_delete=models.CASCADE,
        related_name='laboratorios'
    )
    tema_estudio = models.ForeignKey(
        'campo_estudio.TemaEstudio',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='laboratorios_practica'
    )
    titulo = models.CharField(max_length=200)
    instrucciones = models.TextField(blank=True, default='')
    max_intentos = models.PositiveIntegerField(
        default=0,
        help_text='Envíos calificados permitidos por pregunta. 0 = ilimitado.'
    )
    fecha_limite = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha límite para envíos calificados. Vacío = sin límite. No afecta "Ejecutar" (pruebas contra casos públicos).'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'laboratorios'
        ordering = ['-creado_en']
