"""
Estado vacío del panel de Saber Pro (HU-16.3) y utilidades del panel.

HU-16 habilita el punto de entrada del módulo: el ítem "Saber Pro" en el menú
(HU-16.1), el acceso al panel general sin depender de un curso académico
(HU-16.2) y el estado vacío que invita a empezar (HU-16.3): el docente crea
un curso y el estudiante se une mediante código.

La creación de cursos Saber Pro se implementa en la HU-17 y la inscripción por
código en la HU-18. `obtener_accion_vacia` define la invitación según el rol y
`obtener_tiene_cursos` consulta los modelos reales: para el docente, los
`CursoSaberPro` activos que creó (HU-17); para el estudiante, las
`InscripcionCursoSaberPro` que tenga (HU-18, la tabla ya existe desde HU-17).
Con esto el front alterna entre estado vacío y listado de cursos sin otro cambio.

Esta configuración vive aquí (y no en la vista) siguiendo el mismo criterio
que `funcionalidades.py`: la vista solo compone la respuesta del panel.
"""

from apps.saber_pro.models import CursoSaberPro, InscripcionCursoSaberPro

# Estado vacío para el rol Docente preparador (HU-16.3): invita a crear un curso.
_ACCION_VACIA_DOCENTE = {
    'tipo': 'crear_curso',
    'titulo': 'Crea tu primer curso Saber Pro',
    'descripcion': (
        'Elige el área que vas a preparar (Razonamiento Cuantitativo, Lectura '
        'Crítica, Competencias Ciudadanas, Comunicación Escrita o Inglés), define '
        'el nombre del curso y comparte el código de acceso que el sistema '
        'generará automáticamente con tus estudiantes.'
    ),
    'etiqueta_accion': 'Crear curso',
}

# Estado vacío para el rol Estudiante (HU-16.3): invita a unirse con código.
_ACCION_VACIA_ESTUDIANTE = {
    'tipo': 'unirse_codigo',
    'titulo': 'Únete a un curso de preparación',
    'descripcion': (
        'Ingresa el código de acceso que te compartió tu docente para unirte a su '
        'curso Saber Pro y empezar a prepararte con sus simulacros, contenido '
        'generado con IA y analítica de desempeño.'
    ),
    'etiqueta_accion': 'Unirme con código',
}


def obtener_accion_vacia(rol_nombre):
    """Devuelve la invitación del estado vacío (HU-16.3) para el rol dado.

    `rol_nombre` es el `Role.name` del usuario autenticado. Cada rol tiene su
    propia ruta de entrada: el docente crea un curso y el estudiante se une
    con el código que ese docente le comparte. Si el rol no aplica (p. ej.
    Administrador), devuelve `None`.
    """
    if rol_nombre == 'Docente':
        return _ACCION_VACIA_DOCENTE
    if rol_nombre == 'Estudiante':
        return _ACCION_VACIA_ESTUDIANTE
    return None


def obtener_tiene_cursos(usuario):
    """Indica si el usuario ya participa en algún curso Saber Pro.

    HU-16 dejó el panel en estado vacío fijo porque no persistía cursos. Con la
    HU-17 ya existen los modelos, así que este helper consulta la realidad según
    el rol del usuario: el docente tiene cursos si creó alguno activo (HU-17) y
    el estudiante si tiene inscripciones (HU-18, la tabla nace aquí). No se toca
    la vista ni el frontend para alternar entre estado vacío y listado.
    """
    if not usuario.role:
        return False

    if usuario.role.name == 'Docente':
        return CursoSaberPro.objects.filter(docente=usuario, activo=True).exists()

    if usuario.role.name == 'Estudiante':
        return InscripcionCursoSaberPro.objects.filter(estudiante=usuario).exists()

    return False