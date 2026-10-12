"""
Catálogo académico por área del módulo Saber Pro (HU-20).

No todas las áreas se evalúan igual (skill de Saber Pro, sección "Estructura
para generación de contenido"), así que este módulo es la única fuente que
decide QUÉ estructura le corresponde a cada área:

- `competencias`: Razonamiento Cuantitativo, Lectura Crítica y Competencias
  Ciudadanas usan la jerarquía Competencia → Afirmación → Evidencia.
- `partes`: Inglés se evalúa en 7 partes con pesos del MCER, sin jerarquía
  competencial. Cada parte se genera como un bloque completo (una fila del
  banco) que replica la estructura del examen: la parte 1 es de relacionar (8
  letras A–H para `descripciones` descripciones, ver `es_parte_relacion`) y las
  partes 2 a 7 son bloques con `preguntas` (ítems autocontenidos en 2 y 3, o un
  texto base con sus preguntas en 4 a 7). La cantidad de preguntas por parte la
  define el examen real (ver `PREGUNTAS_POR_PARTE_INGLES`).
- `consigna`: Comunicación Escrita es una pregunta abierta (texto argumentativo
  de máximo dos páginas), por lo que NO se le imponen criterios ni opciones.

Las vistas y el agente de IA consultan estas funciones para validar las
solicitudes del docente y construir el prompt correcto, de modo que agregar o
modificar una estructura en un solo lugar es suficiente.
"""

from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro

# Valores de estructura que consume el resto del módulo.
ESTRUCTURA_COMPETENCIAS = 'competencias'
ESTRUCTURA_PARTES = 'partes'
ESTRUCTURA_CONSIGNA = 'consigna'

# Áreas que usan la jerarquía competencia → afirmación → evidencia.
AREAS_ESTRUCTURA_COMPETENCIAS = (
    'Razonamiento Cuantitativo',
    'Lectura Crítica',
    'Competencias Ciudadanas',
)
AREA_CONSIGNA = 'Comunicación Escrita'
AREA_PARTES = 'Inglés'

# Cantidad de opciones de respuesta de cada parte del examen de Inglés.
# La parte 1 se presenta como listado de letras A–H: 8 palabras para 5
# descripciones. En esta plataforma el ítem se construye con 5 palabras de
# respuesta (una por descripción) y 3 distractores que no corresponden a
# ninguna descripción (decisión del equipo: no se almacena el ejemplo
# oficial del test).
OPCIONES_POR_PARTE_INGLES = {
    1: 8,
    2: 3,
    3: 3,
    4: 3,
    5: 3,
    6: 4,
    7: 4,
}

# Parte de Inglés cuya tarea es relacionar descripciones con palabras y NO
# es de opción múltiple (no tiene "respuesta_correcta" única).
PARTE_RELACIONAR = 1

# Descripciones a relacionar en cada parte; solo la parte 1 es de tipo
# relacionar, por eso las demás partes no tienen entradas aquí.
DESCRIPCIONES_POR_PARTE_INGLES = {
    1: 5,
}

# Cantidad de preguntas de cada parte cuando se genera como bloque completo del
# examen real: la parte 1 trae 5 descripciones (ver `DESCRIPCIONES_POR_PARTE_INGLES`),
# la 2 son 5 avisos, la 3 son 5 conversaciones y las partes 4 a 7 comparten un
# texto base: 8 espacios, 7 preguntas, 5 de inferencia y 10 espacios, en ese orden.
PREGUNTAS_POR_PARTE_INGLES = {
    1: 5,
    2: 5,
    3: 5,
    4: 8,
    5: 7,
    6: 5,
    7: 10,
}

# Partes cuyo bloque comparte un texto base en `contexto` que enmarca todas sus
# preguntas (como el examen real). Las partes 2 y 3 son ítems autocontenidos.
PARTES_CON_TEXTO_COMUN_INGLES = {
    4,
    5,
    6,
    7,
}

# Partes cuyo texto base lleva espacios numerados __1__, __2__, ... (uno por
# pregunta). Las partes 5 y 6 comparten texto pero sin espacios en blanco.
PARTES_CON_ESPACIOS_INGLES = {
    4,
    7,
}

# Las 7 partes del examen de Inglés con su peso porcentual y tarea (HU-20.1
# las usa para poblar el selector de criterios del área de Inglés).
PARTES_INGLES = [
    {
        'numero': 1,
        'nombre': 'Relacionar descripciones con palabras',
        'peso': 11,
        'opciones': 8,
        'descripciones': 5,
        'preguntas': 5,
        'texto_comun': False,
        'espacios': False,
        'descripcion': (
            'Se presentan 5 descripciones y 8 palabras listadas de la letra A a la H: '
            'el estudiante relaciona cada descripción con una de esas palabras y 3 palabras '
            'quedan sin utilizar (distractores).'
        ),
    },
    {
        'numero': 2,
        'nombre': 'Avisos',
        'peso': 11,
        'opciones': 3,
        'descripciones': 0,
        'preguntas': 5,
        'texto_comun': False,
        'espacios': False,
        'descripcion': 'Se presentan avisos; identificar en qué lugar podría encontrarse el aviso.',
    },
    {
        'numero': 3,
        'nombre': 'Completar conversación',
        'peso': 11,
        'opciones': 3,
        'descripciones': 0,
        'preguntas': 5,
        'texto_comun': False,
        'espacios': False,
        'descripcion': 'Se presenta la primera parte de una conversación; seleccionar la opción que mejor la completa.',
    },
    {
        'numero': 4,
        'nombre': 'Texto con espacios: palabra adecuada',
        'peso': 18,
        'opciones': 3,
        'descripciones': 0,
        'preguntas': 8,
        'texto_comun': True,
        'espacios': True,
        'descripcion': 'Texto de conocimiento general con espacios en blanco; seleccionar la palabra adecuada para cada espacio.',
    },
    {
        'numero': 5,
        'nombre': 'Información explícita con paráfrasis',
        'peso': 16,
        'opciones': 3,
        'descripciones': 0,
        'preguntas': 7,
        'texto_comun': True,
        'espacios': False,
        'descripcion': 'Texto de conocimiento general; responder enunciados basados en información explícita, utilizando paráfrasis.',
    },
    {
        'numero': 6,
        'nombre': 'Inferir información',
        'peso': 11,
        'opciones': 4,
        'descripciones': 0,
        'preguntas': 5,
        'texto_comun': True,
        'espacios': False,
        'descripcion': 'Texto de conocimiento general; responder preguntas donde es necesario inferir información.',
    },
    {
        'numero': 7,
        'nombre': 'Texto con espacios: contexto',
        'peso': 22,
        'opciones': 4,
        'descripciones': 0,
        'preguntas': 10,
        'texto_comun': True,
        'espacios': True,
        'descripcion': 'Texto de conocimiento general con espacios en blanco; seleccionar la palabra adecuada para cada espacio.',
    },
]


def obtener_estructura_area(area) -> str:
    """Devuelve la estructura de evaluación que le corresponde al área.

    Recibe una instancia de `AreaSaberPro` y devuelve una de las constantes
    `ESTRUCTURA_*`. Es la decisión central del módulo: la vista de generación
    la usa para saber si pide criterios, una parte o nada, y para fijar el
    `tipo` del contenido generado.
    """
    nombre = (area.nombre or '').strip()
    if nombre in AREAS_ESTRUCTURA_COMPETENCIAS:
        return ESTRUCTURA_COMPETENCIAS
    if nombre == AREA_PARTES:
        return ESTRUCTURA_PARTES
    return ESTRUCTURA_CONSIGNA


def opciones_de_parte(parte: int) -> int:
    """Cantidad de opciones de respuesta de una parte del examen de Inglés."""
    return OPCIONES_POR_PARTE_INGLES.get(parte, 4)


def es_parte_relacion(parte) -> bool:
    """Indica si una parte del examen de Inglés es de relacionar (no MCQ).

    Solo la parte 1: el ítem tiene 8 palabras y 5 descripciones en el campo
    `relaciones` del contenido, sin `respuesta_correcta` única.
    """
    return parte == PARTE_RELACIONAR


def descripciones_de_parte(parte: int) -> int:
    """Descripciones a relacionar en una parte; 0 en las partes de opción múltiple."""
    return DESCRIPCIONES_POR_PARTE_INGLES.get(parte, 0)


def preguntas_de_parte(parte: int) -> int:
    """Preguntas de una parte de Inglés cuando se genera como bloque completo.

    En la parte 1 coincide con las 5 descripciones del relacionar; en las
    partes 4 y 7 también fija la cantidad de espacios numerados del texto base.
    """
    return PREGUNTAS_POR_PARTE_INGLES.get(parte, 5)


def parte_usa_texto_comun(parte: int) -> bool:
    """Indica si la parte comparte un texto base en `contexto` para sus preguntas."""
    return parte in PARTES_CON_TEXTO_COMUN_INGLES


def parte_exige_espacios(parte: int) -> bool:
    """Indica si el texto base de la parte lleva espacios numerados `__N__`."""
    return parte in PARTES_CON_ESPACIOS_INGLES


def validar_relacion(opciones, relaciones) -> tuple:
    """Valida la forma de un ítem de la parte 1 de Inglés y lo normaliza.

    Devuelve `(opciones, relaciones)` con las cadenas recortadas. Lanza
    `ValueError` con un mensaje en español si la estructura no corresponde:
    exactamente 8 palabras distintas, exactamente 5 descripciones, cada
    descripción no vacía y su respuesta única dentro de las palabras, sin
    repetir palabra entre descripciones. El agente usa la excepción para
    reintentar con la IA y el serializer de edición para responder 400.
    """
    if not isinstance(opciones, (list, tuple)) or not isinstance(relaciones, (list, tuple)):
        raise ValueError('las opciones y las relaciones deben ser listas.')

    palabras = [str(opcion).strip() for opcion in opciones]
    total_palabras = OPCIONES_POR_PARTE_INGLES[PARTE_RELACIONAR]
    total_descripciones = DESCRIPCIONES_POR_PARTE_INGLES[PARTE_RELACIONAR]

    if len(palabras) != total_palabras or any(not palabra for palabra in palabras):
        raise ValueError(f'debe haber exactamente {total_palabras} palabras, sin vacíos.')
    if len(set(palabras)) != total_palabras:
        raise ValueError(f'las {total_palabras} palabras deben ser distintas entre sí.')
    if len(relaciones) != total_descripciones:
        raise ValueError(f'debe haber exactamente {total_descripciones} descripciones.')

    normalizadas = []
    for indice, relacion in enumerate(relaciones, start=1):
        if not isinstance(relacion, dict):
            raise ValueError(f'la relación {indice} debe ser un objeto con "descripcion" y "respuesta".')
        descripcion = str(relacion.get('descripcion') or '').strip()
        respuesta = str(relacion.get('respuesta') or '').strip()
        if not descripcion:
            raise ValueError(f'la descripción {indice} está vacía.')
        if respuesta not in palabras:
            raise ValueError(f'la respuesta de la descripción {indice} debe ser una de las {total_palabras} palabras.')
        normalizadas.append({'descripcion': descripcion, 'respuesta': respuesta})

    respuestas = [relacion['respuesta'] for relacion in normalizadas]
    if len(set(respuestas)) != len(respuestas):
        raise ValueError('dos descripciones no pueden compartir la misma palabra.')
    descripciones = [relacion['descripcion'] for relacion in normalizadas]
    if len(set(descripciones)) != len(descripciones):
        raise ValueError('las descripciones deben ser distintas entre sí.')

    return palabras, normalizadas


def partes_ingles() -> list:
    """Copia de las 7 partes de Inglés para exponerlas en la API."""
    return [dict(p) for p in PARTES_INGLES]


def criterios_area(area) -> list:
    """Jerarquía competencial agrupada de un área, para el selector del docente.

    Devuelve lista de dicts `{'id', 'nombre', 'afirmaciones': [{'id', 'nombre',
    'evidencias': [{'id', 'nombre'}]}]` anclados al área. Solo tiene sentido
    para las áreas con `ESTRUCTURA_COMPETENCIAS`; en Inglés y Comunicación
    Escrita devuelve lista vacía (se usan `partes_ingles()` o ningún criterio).
    """
    competencias = (
        CompetenciaSaberPro.objects.filter(area=area)
        .prefetch_related('afirmaciones__evidencias')
        .order_by('orden', 'nombre')
    )
    return [
        {
            'id': competencia.id,
            'nombre': competencia.nombre,
            'afirmaciones': [
                {
                    'id': afirmacion.id,
                    'nombre': afirmacion.nombre,
                    'evidencias': [
                        {'id': evidencia.id, 'nombre': evidencia.nombre}
                        for evidencia in sorted(afirmacion.evidencias.all(), key=lambda e: (e.orden, e.id))
                    ],
                }
                for afirmacion in sorted(competencia.afirmaciones.all(), key=lambda a: (a.orden, a.id))
            ],
        }
        for competencia in competencias
    ]
