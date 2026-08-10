"""
Cálculo del puntaje agregado de UN estudiante sobre UN laboratorio completo.

Reutiliza el mismo criterio que ya usa `VistaAnaliticaLaboratorio` (docente):
por cada pregunta se toma la MEJOR entrega del estudiante, no todas — un
reintento que mejora no debe "ensuciar" el promedio con sus intentos
fallidos previos. La diferencia es que aquí se exige que TODAS las preguntas
del laboratorio tengan al menos una entrega: esto se usa para decidir si un
estudiante ya puede "finalizar" el laboratorio como práctica de un examen
(ver `apps.laboratorios.views.estudiante.vista_finalizar_practica`), así que
una práctica a medias no debe poder cerrarse con nota.
"""

from apps.laboratorios.models import Entrega


def calcular_puntaje_laboratorio(laboratorio, estudiante) -> float | None:
    preguntas = list(laboratorio.preguntas.all())
    if not preguntas:
        return None

    entregas = Entrega.objects.filter(pregunta__laboratorio=laboratorio, estudiante=estudiante)

    mejor_por_pregunta = {}
    for entrega in entregas:
        pid = entrega.pregunta_id
        if pid not in mejor_por_pregunta or entrega.puntaje > mejor_por_pregunta[pid].puntaje:
            mejor_por_pregunta[pid] = entrega

    if len(mejor_por_pregunta) < len(preguntas):
        return None

    return round(sum(e.puntaje for e in mejor_por_pregunta.values()) / len(preguntas), 2)
