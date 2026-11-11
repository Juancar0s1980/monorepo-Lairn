"""
Catálogo de funcionalidades del módulo Saber Pro, por rol (HU-16).

El módulo se organiza alrededor de cursos Saber Pro (HU-17 crearlos, HU-18
unirse): cada funcionalidad opera dentro de los cursos del usuario. Estas
entradas son los avances del panel: se muestran como "Próximamente" y las épicas
siguientes (HU-19 a HU-24) las van implementando y voltean `disponible` a `True`
sin tocar la vista ni el serializador.

Numeración de épicas que implementan cada funcionalidad:
  - HU-19: creación y gestión de simulacros dentro de un curso.
  - HU-20: generación y gestión de contenido con IA (banco).
  - HU-21: presentación de simulacro por el estudiante.
  - HU-23: comparación de desempeño (percentil estudiante / ranking docente).
  - HU-24: analítica de resultados por curso.

"""

# Funcionalidades visibles para el rol Docente preparador.
# El ranking nominal se retiró del panel: la analítica del curso ya le da al
# docente el detalle individual y agregado, así que la tarjeta se eliminó en
# vez de marcarse como "Próximamente" (que sugeriría que volverá).
_FUNCIONALIDADES_DOCENTE = [
    {
        'clave': 'cursos',
        'titulo': 'Cursos Saber Pro',
        'descripcion': 'Crea y administra tus cursos de preparación: área, nombre, descripción, código de acceso y estudiantes inscritos.',
        'disponible': True,
    },
    {
        'clave': 'simulacros',
        'titulo': 'Simulacros',
        'descripcion': 'Crea simulacros dentro de tus cursos Saber Pro eligiendo competencias, afirmaciones y distribución de preguntas.',
        'disponible': True,
    },
    {
        'clave': 'banco_contenido',
        'titulo': 'Banco de contenido con IA',
        'descripcion': 'Genera, revisa y aprueba preguntas y consignas con apoyo de IA para el área de tus cursos.',
        'disponible': True,
    },
    {
        'clave': 'analitica',
        'titulo': 'Analítica',
        'descripcion': 'Consulta el desempeño de tus estudiantes por área, competencia y afirmación, con filtros, exportación a Excel y análisis de acciones con IA.',
        'disponible': True,
    },
]

# Funcionalidades visibles para el rol Estudiante.
_FUNCIONALIDADES_ESTUDIANTE = [
    {
        'clave': 'simulacros',
        'titulo': 'Simulacros',
        'descripcion': 'Consulta los simulacros activos de tus cursos de preparación y preséntalos con temporizador y condiciones controladas.',
        'disponible': True,
    },
    {
        'clave': 'desempeno',
        'titulo': 'Mi desempeño',
        'descripcion': 'Consulta tu percentil por área o simulacro frente a tu curso, sin ver datos de otros estudiantes.',
        'disponible': True,
    },
]


def obtener_funcionalidades(rol_nombre):
    """Devuelve la lista de funcionalidades del panel para el rol dado.

    `rol_nombre` es el `Role.name` del usuario autenticado ('Docente' o
    'Estudiante'; Administrador no tiene panel propio de Saber Pro). Si el
    rol no aplica, devuelve una lista vacía en vez de lanzar una excepción,
    para que la vista decida cómo responder.
    """
    if rol_nombre == 'Docente':
        return _FUNCIONALIDADES_DOCENTE
    if rol_nombre == 'Estudiante':
        return _FUNCIONALIDADES_ESTUDIANTE
    return []