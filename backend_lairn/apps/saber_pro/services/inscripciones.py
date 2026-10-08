"""
Lógica de negocio de las inscripciones de estudiantes a cursos Saber Pro (HU-18).

Centraliza las reglas de la inscripción por código en un servicio desacoplado
de las vistas (patrón del módulo: la vista compone la respuesta, el servicio
decide). Esto evita duplicar reglas entre la inscripción (HU-18) y los futuros
consumidores de la relación estudiante-curso (HU-19.5: solo los inscritos ven
los simulacros del curso; HU-23/24: analítica por curso).

Reglas que este servicio garantiza:

- `resolver_curso_por_codigo`: traduce el código de acceso al `CursoSaberPro`
  vigente. Un código inválido o regenerado (HU-18.2) ya no coincide con ningún
  curso porque `codigo` es único y la regeneración (HU-17.3) reemplaza el
  valor; un curso desactivado (HU-17.6) no admite ingresos nuevos.
- `inscribir_estudiante`: crea la inscripción rechazando el duplicado
  (HU-18.4). La consulta previa da un mensaje amable y `unique_together` del
  modelo resuelve la condición de carrera a nivel de base de datos.
- `esta_inscrito` y `obtener_cursos_de_estudiante`: consultas reutilizables
  para decidir visibilidad (HU-19.5) y para el listado del panel (HU-18.3).

Las excepciones de dominio (`CodigoInvalidoError`, `CursoDesactivadoError`,
`YaInscritoError`) trasladan el motivo a la vista sin acoplar la lógica a HTTP.
"""

from django.db import IntegrityError

from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro


class ErrorInscripcionSaberPro(Exception):
    """Base de los errores de dominio de la inscripción Saber Pro (HU-18)."""


class CodigoInvalidoError(ErrorInscripcionSaberPro):
    """El código no corresponde a ningún curso vigente (HU-18.2)."""


class CursoDesactivadoError(ErrorInscripcionSaberPro):
    """El curso fue desactivado y no admite inscripciones nuevas (HU-17.6/HU-18.2)."""


class YaInscritoError(ErrorInscripcionSaberPro):
    """El estudiante ya pertenece al curso (HU-18.4)."""


# Mensajes por error de dominio. La vista los devuelve tal cual en la respuesta.
MENSAJE_CODIGO_INVALIDO = 'El código no es válido, fue regenerado o ya no existe.'
MENSAJE_CURSO_DESACTIVADO = 'El curso está desactivado y no admite nuevos integrantes.'
MENSAJE_YA_INSCRITO = 'Ya perteneces a este curso.'


def resolver_curso_por_codigo(codigo):
    """Resuelve el `CursoSaberPro` vigente al que apunta un código de acceso.

    Lanza `CodigoInvalidoError` si el código no coincide con ningún curso
    (incluye el caso "regenerado": el código viejo dejó de existir) y
    `CursoDesactivadoError` si el curso está desactivado (HU-17.6).
    """
    from apps.saber_pro.models.curso_saber_pro import CursoSaberPro

    try:
        curso = CursoSaberPro.objects.get(codigo=codigo.upper().strip())
    except CursoSaberPro.DoesNotExist:
        raise CodigoInvalidoError(MENSAJE_CODIGO_INVALIDO)

    if not curso.activo:
        raise CursoDesactivadoError(MENSAJE_CURSO_DESACTIVADO)

    return curso


def inscribir_estudiante(estudiante, codigo):
    """Inscribe a un estudiante en el curso resuelto por código.

    Rechaza el duplicado (HU-18.4): la consulta previa da un mensaje claro y,
    ante una condición de carrera, la restricción `unique_together` del modelo
    convierte el `IntegrityError` en el mismo error de dominio.
    """
    curso = resolver_curso_por_codigo(codigo)

    if InscripcionCursoSaberPro.objects.filter(estudiante=estudiante, curso=curso).exists():
        raise YaInscritoError(MENSAJE_YA_INSCRITO)

    try:
        return InscripcionCursoSaberPro.objects.create(estudiante=estudiante, curso=curso)
    except IntegrityError:
        raise YaInscritoError(MENSAJE_YA_INSCRITO)


def esta_inscrito(estudiante, curso):
    """Indica si un estudiante pertenece al curso (reutilizable por HU-19.5)."""
    return InscripcionCursoSaberPro.objects.filter(estudiante=estudiante, curso=curso).exists()


def obtener_cursos_de_estudiante(estudiante):
    """Devuelve las inscripciones del estudiante con su curso precargado.

    `select_related` trae `curso` y las relaciones `area`/`docente` del curso en
    la misma consulta para evitar N+1 al serializar el listado del panel (HU-18.3).
    """
    return InscripcionCursoSaberPro.objects.filter(estudiante=estudiante).select_related(
        'curso__area'
    )