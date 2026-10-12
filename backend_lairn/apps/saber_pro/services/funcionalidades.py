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
_FUNCIONALIDADES_DOCENTE = [
    {
        'clave': 'cursos',
        'titulo': 'Cursos Saber Pro',
        'descripcion': 'Crea y administra tus cursos de preparación: área, nombre, descripción, código de acceso y estudiantes inscritos (HU-17).',
        'disponible': True,
    },
    {
        'clave': 'simulacros',
        'titulo': 'Simulacros',
        'descripcion': 'Crea simulacros dentro de tus cursos Saber Pro eligiendo competencias, afirmaciones y distribución de preguntas (HU-19).',
        'disponible': False,
    },
    {
        'clave': 'banco_contenido',
        'titulo': 'Banco de contenido con IA',
        'descripcion': 'Genera, revisa y aprueba preguntas y consignas con apoyo de IA para el área de tus cursos (HU-20).',
        'disponible': False,
    },
    {
        'clave': 'analitica',
        'titulo': 'Analítica',
        'descripcion': 'Consulta el desempeño de tus estudiantes por área, competencia y afirmación en cada curso (HU-24).',
        'disponible': False,
    },
    {
        'clave': 'ranking',
        'titulo': 'Ranking',
        'descripcion': 'Consulta el listado nominal de tus estudiantes por simulacro o área, con fines pedagógicos (HU-23).',
        'disponible': False,
    },
]

# Funcionalidades visibles para el rol Estudiante.
_FUNCIONALIDADES_ESTUDIANTE = [
    {
        'clave': 'simulacros',
        'titulo': 'Simulacros',
        'descripcion': 'Presenta los simulacros de tus cursos de preparación, con temporizador y condiciones controladas (HU-21).',
        'disponible': False,
    },
    {
        'clave': 'desempeno',
        'titulo': 'Mi desempeño',
        'descripcion': 'Consulta tu percentil por área o simulacro frente a tu curso, sin ver datos de otros estudiantes (HU-23).',
        'disponible': False,
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