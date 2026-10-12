"""
Generación de códigos de acceso únicos para cursos Saber Pro (HU-17.2/17.3).

A diferencia del patrón de `examenes.Curso` (un `default` con `random.choices`),
aquí la unicidad se garantiza con reintento: se genera un candidato y se verifica
contra la tabla antes de asignarlo. Así el docente nunca percibe un error de
"código duplicado": esa validación es interna y automática (HU-17.2).

El código es opaco y de 8 caracteres alfanuméricos en mayúsculas: el docente no
lo digita en ningún momento (HU-17.1) y solo lo consulta o lo regenera (HU-17.3).
"""

import random
import string

from django.db import IntegrityError


# Longitud del código de acceso (alfanumérico en mayúsculas).
LONGITUD_CODIGO = 8

# Reintentos máximos con candidatos nuevos antes de ceder (probabilidad de
# agotarlos es despreciable; la restricción `unique` del modelo queda como respaldo).
MAXIMO_REINTENTOS = 20


def generar_candidato():
    """Devuelve un código alfanumérico aleatorio de 8 caracteres en mayúsculas."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=LONGITUD_CODIGO))


def generar_codigo_unico():
    """Genera y devuelve un código que todavía no existe en `CursoSaberPro`.

    Reintenta con candidatos nuevos hasta encontrar uno libre. En el caso
    extremo de agotar los reintentos por una condición de carrera, la restricción
    `unique` del modelo resuelve la unicidad y este servicio lanza
    `IntegrityError` (un error de servidor, nunca una validación del docente).
    """
    from apps.saber_pro.models.curso_saber_pro import CursoSaberPro

    for _ in range(MAXIMO_REINTENTOS):
        candidato = generar_candidato()
        if not CursoSaberPro.objects.filter(codigo=candidato).exists():
            return candidato

    raise IntegrityError('No se pudo generar un código único de curso Saber Pro.')