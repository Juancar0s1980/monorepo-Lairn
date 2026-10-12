"""
Comando seed del módulo Saber Pro.

Crea dos catálogos que el módulo referencia como FK:

1. `AreaSaberPro`: las cinco áreas oficiales del examen (HU-17.1), necesarias
   para que el docente cree sus cursos.
2. La jerarquía académica de las áreas estructuradas —`CompetenciaSaberPro` →
   `AfirmacionSaberPro` → `EvidenciaSaberPro`— que el docente selecciona al
   generar contenido con IA (HU-20.1). Comunicación Escrita e Inglés NO tienen
   jerarquía competencial (ver `services/catalogo_saber_pro.py`).

La jerarquía se transcribe de forma literal a la estructura oficial del
ICFES/Saber Pro (HU-20.1), que este catálogo replica sin abreviar:

- Razonamiento Cuantitativo: 3 competencias, 3 afirmaciones, 8 evidencias.
- Lectura Crítica: 1 competencia, 3 afirmaciones, 12 evidencias.
- Competencias Ciudadanas: 4 competencias, 7 afirmaciones, 17 evidencias
  (incluidas las evidencias 5.1/5.2 y 6.1/6.2 de Multiperspectivismo y las
  evidencias individuales de Conocimientos, antes pendientes de descripción).

Las instrucciones de generación que no son jerarquía (contenidos, contextos,
tipos de texto, distribuciones porcentuales, partes de Inglés y consignas de
Comunicación Escrita) viven en `services/agente_saber_pro.py` y
`services/catalogo_saber_pro.py`, que son los que alimentan el prompt.

Es idempotente y reconciliante: cada registro se busca primero por su
posición (`orden`) dentro del padre y se le actualiza el texto en sitio, de
modo que re-ejecutarlo corrige catálogos sembrados con versiones anteriores
sin duplicar filas ni dejar huérfanos (los textos oficiales se depuraron, así
que los nombres guardados antes ya no coinciden literalmente).

Ejecución:
    docker compose exec web python manage.py seed_saber_pro
"""

from django.core.management.base import BaseCommand

from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.evidencia_saber_pro import EvidenciaSaberPro


# Catálogo institucional de áreas de las pruebas Saber Pro, con su descripción
# y el orden con que se presentan en la interfaz (HU-16/17).
AREAS_SABER_PRO = [
    ('Razonamiento Cuantitativo', 'Competencias de interpretación, formulación y argumentación en contextos matemáticos y esquemáticos.'),
    ('Lectura Crítica', 'Comprensión y reflexión sobre textos continuos y discontinuos.'),
    ('Competencias Ciudadanas', 'Conocimientos, argumentación, multiperspectivismo y pensamiento sistémico.'),
    ('Comunicación Escrita', 'Producción de un texto argumentativo de máximo dos páginas.'),
    ('Inglés', 'Comunicación efectiva en inglés clasificada por niveles del MCER.'),
]

# Jerarquía académica por área estructurada, transcrita de la estructura
# oficial (HU-20.1):
#   nombre de competencia -> [(afirmación, [evidencias]), ...]
# Las áreas sin jerarquía (Comunicación Escrita e Inglés) no aparecen aquí.
CATALOGO_CRITERIOS = {
    'Razonamiento Cuantitativo': [
        ('Interpretación y representación', [
            (
                'Comprende y transforma la información cuantitativa y esquemática presentada en distintos formatos.',
                [
                    'Da cuenta de las características básicas de la información presentada en diferentes formatos, como series, gráficas, tablas y esquemas.',
                    'Transforma la representación de una o más piezas de información.',
                ],
            ),
        ]),
        ('Formulación y ejecución', [
            (
                'Frente a un problema que involucre información cuantitativa, plantea e implementa estrategias que lleven a soluciones adecuadas.',
                [
                    'Diseña planes para la solución de problemas que involucran información cuantitativa o esquemática.',
                    'Ejecuta un plan de solución para un problema que involucra información cuantitativa o esquemática.',
                    'Resuelve un problema que involucra información cuantitativa o esquemática.',
                ],
            ),
        ]),
        ('Argumentación', [
            (
                'Valida procedimientos y estrategias matemáticas utilizadas para dar solución a problemas.',
                [
                    'Plantea afirmaciones que sustentan o refutan una interpretación dada a la información disponible en el marco de la solución de un problema.',
                    'Argumenta a favor o en contra de un procedimiento para resolver un problema a la luz de criterios presentados o establecidos.',
                    'Establece la validez o pertinencia de una solución propuesta a un problema dado.',
                ],
            ),
        ]),
    ],
    'Lectura Crítica': [
        ('Comprensión lectora', [
            (
                'Identifica y entiende los contenidos locales que conforman un texto.',
                [
                    'Entiende el significado de los elementos locales que constituyen un texto.',
                    'Identifica los eventos narrados de manera explícita en un texto —literario, descriptivo, caricatura o cómic— y los personajes involucrados, si los hay.',
                ],
            ),
            (
                'Comprende cómo se articulan las partes de un texto para darle un sentido global.',
                [
                    'Comprende la estructura formal de un texto y la función de sus partes.',
                    'Identifica y caracteriza las diferentes voces o situaciones presentes en un texto.',
                    'Comprende las relaciones entre diferentes partes o enunciados de un texto.',
                    'Identifica y caracteriza las ideas o afirmaciones presentes en un texto informativo.',
                    'Identifica el tipo de relación existente entre diferentes elementos de un texto discontinuo.',
                ],
            ),
            (
                'Reflexiona a partir de un texto y evalúa su contenido.',
                [
                    'Establece la validez e implicaciones de un enunciado de un texto argumentativo o expositivo.',
                    'Establece relaciones entre un texto y otros textos o enunciados.',
                    'Reconoce contenidos valorativos presentes en un texto.',
                    'Reconoce las estrategias discursivas en un texto.',
                    'Contextualiza adecuadamente un texto o la información contenida en este.',
                ],
            ),
        ]),
    ],
    'Competencias Ciudadanas': [
        ('Conocimientos', [
            (
                'Comprende qué es la Constitución política de Colombia y sus principios fundamentales.',
                [
                    'Conoce las características básicas de la Constitución.',
                    'Reconoce que la Constitución promueve la diversidad étnica y cultural del país, y que es deber del Estado protegerla.',
                    'Comprende que Colombia es un Estado Social de Derecho e identifica sus características.',
                ],
            ),
            (
                'Conoce los derechos y deberes que la Constitución consagra.',
                [
                    'Conoce los derechos fundamentales de los individuos.',
                    'Reconoce situaciones en las que se protegen o vulneran los derechos sociales, económicos y culturales consagrados en la Constitución.',
                    'Conoce los derechos colectivos y del ambiente consagrados en la Constitución.',
                    'Conoce que la Constitución consagra deberes de los ciudadanos.',
                ],
            ),
            (
                'Conoce la organización del Estado de acuerdo con la Constitución.',
                [
                    'Conoce las funciones y alcances de las ramas del poder y de los organismos de control.',
                    'Conoce los mecanismos que los ciudadanos tienen a su disposición para participar activamente en la democracia y para garantizar el respeto de sus derechos.',
                ],
            ),
        ]),
        ('Argumentación', [
            (
                'Analiza y evalúa la pertinencia y solidez de enunciados y discursos.',
                [
                    'Devela prejuicios e intenciones en enunciados o argumentos.',
                    'Valora la solidez y pertinencia de enunciados o argumentos.',
                ],
            ),
        ]),
        ('Multiperspectivismo', [
            (
                'Reconoce la existencia de diferentes perspectivas en situaciones en donde interactúan diferentes partes.',
                [
                    'En situaciones de interacción, reconoce las posiciones o intereses de las partes presentes y puede identificar un conflicto.',
                    'Reconoce que las cosmovisiones, ideologías y roles sociales determinan diferentes argumentos, posiciones y conductas.',
                ],
            ),
            (
                'Analiza las diferentes perspectivas presentes en situaciones en donde interactúan diferentes partes.',
                [
                    'Compara las perspectivas de diferentes actores.',
                    'Establece relaciones entre las perspectivas de los individuos presentes en un conflicto y sus propuestas de solución.',
                ],
            ),
        ]),
        ('Pensamiento sistémico', [
            (
                'Comprende que los problemas y soluciones involucran distintas dimensiones y reconoce relaciones entre estas.',
                [
                    'Establece relaciones que hay entre las dimensiones presentes en una situación problemática.',
                    'Analiza los efectos, en distintas dimensiones, que tendría una solución.',
                ],
            ),
        ]),
    ],
}


def _obtener_o_actualizar(modelo, nombre, orden, **filtros):
    """Crea o reconcilia un registro del catálogo y devuelve `(registro, creado, actualizado)`.

    Busca primero por posición (`orden`) dentro de su padre: es el registro que
    sembró una ejecución anterior, y así se le puede corregir el texto en sitio
    cuando la fuente oficial cambió. Si no hay posición ocupada, reutiliza un
    registro con el mismo nombre (catálogos que cambiaron de orden) y, en
    último caso, lo crea. Nunca borra: los catálogos solo crecen y las filas
    pueden estar referenciadas por el banco de contenido.
    """
    registro = modelo.objects.filter(orden=orden, **filtros).first()
    if registro is None:
        registro = modelo.objects.filter(nombre=nombre, **filtros).first()
    if registro is None:
        return modelo.objects.create(nombre=nombre, orden=orden, **filtros), True, False

    actualizado = False
    if registro.nombre != nombre:
        registro.nombre = nombre
        actualizado = True
    if registro.orden != orden:
        registro.orden = orden
        actualizado = True
    if actualizado:
        registro.save()
    return registro, False, actualizado


class Command(BaseCommand):
    help = 'Crea el catálogo de áreas y criterios de evaluación de Saber Pro (idempotente).'

    def handle(self, *args, **options):
        areas_creadas = self._sembrar_areas()
        resumen = self._sembrar_criterios()
        self.stdout.write(self.style.SUCCESS(
            'Saber Pro listo: '
            f'{areas_creadas} áreas nuevas, '
            f'{resumen["competencias_creadas"]} competencias nuevas, '
            f'{resumen["afirmaciones_creadas"]} afirmaciones nuevas, '
            f'{resumen["evidencias_creadas"]} evidencias nuevas; '
            f'{resumen["actualizados"]} textos reconciliados con la estructura oficial.'
        ))

    def _sembrar_areas(self):
        """Crea (o reutiliza) las cinco áreas oficiales y devuelve cuántas creó."""
        creadas = 0
        for orden, (nombre, descripcion) in enumerate(AREAS_SABER_PRO, start=1):
            _, creada = AreaSaberPro.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion, 'orden': orden},
            )
            creadas += int(creada)
        return creadas

    def _sembrar_criterios(self):
        """Crea o reconcilia la jerarquía competencial de las áreas estructuradas.

        Devuelve un dict con los registros efectivamente creados por nivel y la
        cantidad de textos que hubo que actualizar (el catálogo anterior tenía
        evidencias abreviadas y Competencias Ciudadanas incompleta).
        """
        conteo = {
            'competencias_creadas': 0,
            'afirmaciones_creadas': 0,
            'evidencias_creadas': 0,
            'actualizados': 0,
        }
        for area_nombre, competencias_area in CATALOGO_CRITERIOS.items():
            area = AreaSaberPro.objects.get(nombre=area_nombre)
            for orden_competencia, (competencia_nombre, afirmaciones_area) in enumerate(competencias_area, start=1):
                competencia, creada, actualizada = _obtener_o_actualizar(
                    CompetenciaSaberPro, competencia_nombre, orden_competencia, area=area,
                )
                conteo['competencias_creadas'] += int(creada)
                conteo['actualizados'] += int(actualizada)

                for orden_afirmacion, (afirmacion_nombre, evidencias_area) in enumerate(afirmaciones_area, start=1):
                    afirmacion, creada, actualizada = _obtener_o_actualizar(
                        AfirmacionSaberPro, afirmacion_nombre, orden_afirmacion, competencia=competencia,
                    )
                    conteo['afirmaciones_creadas'] += int(creada)
                    conteo['actualizados'] += int(actualizada)

                    for orden_evidencia, evidencia_nombre in enumerate(evidencias_area, start=1):
                        _, creada, actualizada = _obtener_o_actualizar(
                            EvidenciaSaberPro, evidencia_nombre, orden_evidencia, afirmacion=afirmacion,
                        )
                        conteo['evidencias_creadas'] += int(creada)
                        conteo['actualizados'] += int(actualizada)
        return conteo
