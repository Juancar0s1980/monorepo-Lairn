"""
Servicios de ensamblaje de simulacros Saber Pro (HU-19).

Toda la selección de preguntas vive aquí para que las vistas y los
serializadores no dupliquen reglas:

- `disponibilidad_area`: cuenta el contenido aprobado del docente por
  competencia, afirmación y parte de Inglés, para que el docente sepa cuántas
  preguntas puede distribuir antes de guardar. En Inglés informa las 7 partes
  obligatorias y su cantidad fija de preguntas.
- `seleccionar_preguntas`: elige aleatoriamente contenido `aprobado` del área
  del curso, respetando la distribución configurada y sin repetir una pieza
  dentro del mismo simulacro (HU-19.3 y HU-20.4). En Inglés siempre toma un
  bloque completo por cada una de las 7 partes.
- `guardar_distribuciones`: reconstruye la configuración académica del
  simulacro a partir de criterios ya validados.

Si el banco no alcanza para la cantidad solicitada, se lanza
`ContenidoInsuficienteError` con mensajes claros por criterio. El llamador debe
ejecutar la operación dentro de una transacción para no dejar un simulacro a
medias.
"""

import random

from django.db.models import Count

from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.distribucion_simulacro import DistribucionSimulacro
from apps.saber_pro.models.simulacro_pregunta import SimulacroPregunta
from apps.saber_pro.services.catalogo_saber_pro import (
    ESTRUCTURA_COMPETENCIAS,
    ESTRUCTURA_PARTES,
    PARTES_INGLES,
    criterios_oficiales_area,
    distribuir_por_pesos,
    obtener_estructura_area,
    peso_de_criterio,
)


class ContenidoInsuficienteError(Exception):
    """El banco aprobado no alcanza para la distribución solicitada."""

    def __init__(self, mensaje, detalles=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or []


def banco_aprobado(curso):
    """Contenido aprobado del docente para el área del curso (HU-20.4)."""
    return ContenidoBancoSaberPro.objects.filter(
        docente=curso.docente,
        area=curso.area,
        estado='aprobado',
    )


def disponibilidad_area(curso):
    """Resumen del contenido aprobado disponible para un curso.

    Devuelve la estructura del área y los conteos por criterio para que el
    formulario del docente muestre qué puede distribuir. En Comunicación
    Escrita se informa solo el total de consignas aprobadas.
    """
    base = banco_aprobado(curso)
    estructura = obtener_estructura_area(curso.area)
    total = base.count()

    if estructura == ESTRUCTURA_COMPETENCIAS:
        por_competencia = {
            fila['competencia_id']: fila['total']
            for fila in base.exclude(competencia__isnull=True)
            .values('competencia_id')
            .annotate(total=Count('id'))
        }
        por_afirmacion = {
            fila['afirmacion_id']: fila['total']
            for fila in base.exclude(afirmacion__isnull=True)
            .values('afirmacion_id')
            .annotate(total=Count('id'))
        }
        competencias = []
        for competencia in CompetenciaSaberPro.objects.filter(area=curso.area).prefetch_related('afirmaciones'):
            competencias.append({
                'id': competencia.id,
                'nombre': competencia.nombre,
                'peso': peso_de_criterio(competencia=competencia),
                'disponibles': por_competencia.get(competencia.id, 0),
                'afirmaciones': [
                    {
                        'id': afirmacion.id,
                        'nombre': afirmacion.nombre,
                        'peso': peso_de_criterio(competencia=competencia, afirmacion=afirmacion),
                        'disponibles': por_afirmacion.get(afirmacion.id, 0),
                    }
                    for afirmacion in competencia.afirmaciones.all()
                ],
            })
        return {
            'tipo_estructura': estructura,
            'total_aprobados': total,
            'competencias': competencias,
            'partes': [],
        }

    if estructura == ESTRUCTURA_PARTES:
        por_parte = {
            fila['parte']: fila['total']
            for fila in base.exclude(parte__isnull=True)
            .values('parte')
            .annotate(total=Count('id'))
        }
        return {
            'tipo_estructura': estructura,
            'total_aprobados': total,
            'competencias': [],
            'partes': [
                {
                    'numero': parte['numero'],
                    'nombre': parte['nombre'],
                    'peso': parte['peso'],
                    'preguntas': parte['preguntas'],
                    'disponibles': por_parte.get(parte['numero'], 0),
                }
                for parte in PARTES_INGLES
            ],
        }

    return {
        'tipo_estructura': estructura,
        'total_aprobados': total,
        'competencias': [],
        'partes': [],
    }


def distribuciones_ingles_obligatorias():
    """Distribuciones fijas de un simulacro de Inglés.

    El examen real siempre cubre las 7 partes y cada parte se genera como un
    bloque completo, así que cada distribución aporta exactamente un bloque.
    """
    return [
        {
            'competencia': None,
            'afirmacion': None,
            'parte': parte['numero'],
            'cantidad': 1,
        }
        for parte in PARTES_INGLES
    ]


def cantidades_automaticas(num_preguntas, cantidad_criterios, pesos=None):
    """Reparte las preguntas entre criterios según sus pesos oficiales.

    Sin `pesos` (o con una lista que no coincide) cae al reparto equitativo para
    no romper llamadas antiguas. Con pesos usa el método del mayor residuo para
    que la suma sea exactamente `num_preguntas` y se respeten los porcentajes
    oficiales del área.
    """
    if cantidad_criterios <= 0:
        return []
    if pesos and len(pesos) == cantidad_criterios:
        return distribuir_por_pesos(num_preguntas, pesos)
    base, residuo = divmod(num_preguntas, cantidad_criterios)
    return [base + 1 if indice < residuo else base for indice in range(cantidad_criterios)]


def distribuciones_oficiales(area):
    """Distribuciones por defecto de un área estructurada, ordenadas como el examen."""
    return [
        {
            **criterio,
            'cantidad': None,
            'peso': peso_de_criterio(
                competencia=criterio.get('competencia'),
                afirmacion=criterio.get('afirmacion'),
            ),
        }
        for criterio in criterios_oficiales_area(area)
    ]


def _etiqueta_distribucion(distribucion):
    if distribucion.get('afirmacion'):
        return distribucion['afirmacion'].nombre
    if distribucion.get('competencia'):
        return distribucion['competencia'].nombre
    if distribucion.get('parte'):
        return f'Parte {distribucion["parte"]} de Inglés'
    return 'Criterio sin definir'


def _filtrar_por_criterio(queryset, distribucion):
    if distribucion.get('afirmacion'):
        return queryset.filter(afirmacion=distribucion['afirmacion'])
    if distribucion.get('competencia'):
        return queryset.filter(competencia=distribucion['competencia'])
    if distribucion.get('parte'):
        return queryset.filter(parte=distribucion['parte'])
    return queryset


def _seleccionar_bloques_ingles(base):
    """Elige un bloque aprobado para cada una de las 7 partes de Inglés."""
    seleccionados = []
    faltantes = []

    for parte in PARTES_INGLES:
        numero = parte['numero']
        candidatos = list(base.filter(parte=numero).values_list('id', flat=True))
        if not candidatos:
            faltantes.append(f'Parte {numero}: no hay bloques aprobados disponibles.')
            continue
        seleccionados.append(random.choice(candidatos))

    if faltantes:
        raise ContenidoInsuficienteError(
            'El banco no cubre las 7 partes obligatorias del examen de Inglés.',
            faltantes,
        )
    return seleccionados


def seleccionar_preguntas(simulacro):
    """Asigna aleatoriamente contenido aprobado al simulacro (HU-19.3).

    Inglés siempre usa un bloque completo por cada una de sus 7 partes. En las
    demás áreas el serializador resuelve la distribución oficial (competencias
    o afirmaciones) y aquí solo se respeta la cantidad de cada criterio. Si un
    simulacro antiguo no tiene distribución, se conserva el fallback de tomar
    `num_preguntas` del banco completo. Las afirmaciones se procesan antes que
    las competencias para evitar que un criterio amplio consuma las preguntas
    de un criterio más específico.
    """
    base = banco_aprobado(simulacro.curso)
    estructura = obtener_estructura_area(simulacro.curso.area)

    if estructura == ESTRUCTURA_PARTES:
        seleccionados = _seleccionar_bloques_ingles(base)
    else:
        distribuciones = list(simulacro.distribuciones.all())

        if distribuciones:
            total_configurado = sum(distribucion.cantidad for distribucion in distribuciones)
            if total_configurado != simulacro.num_preguntas:
                raise ContenidoInsuficienteError(
                    'La distribución no coincide con el número de preguntas del simulacro.',
                    [f'La suma de cantidades es {total_configurado} y se esperaban {simulacro.num_preguntas}.'],
                )

            ordenadas = sorted(
                distribuciones,
                key=lambda distribucion: (
                    0 if distribucion.afirmacion_id else 1 if distribucion.competencia_id else 2
                ),
            )
            seleccionados = []
            seleccionados_ids = set()

            for distribucion in ordenadas:
                candidatos = list(
                    _filtrar_por_criterio(base, {
                        'afirmacion': distribucion.afirmacion,
                        'competencia': distribucion.competencia,
                        'parte': distribucion.parte,
                    })
                    .exclude(id__in=seleccionados_ids)
                    .values_list('id', flat=True)
                )
                if len(candidatos) < distribucion.cantidad:
                    raise ContenidoInsuficienteError(
                        'No hay suficientes preguntas aprobadas para la distribución definida.',
                        [
                            (
                                f'"{distribucion.etiqueta()}": hay {len(candidatos)} disponibles '
                                f'y se requieren {distribucion.cantidad}.'
                            )
                        ],
                    )
                elegidos = random.sample(candidatos, distribucion.cantidad)
                seleccionados.extend(elegidos)
                seleccionados_ids.update(elegidos)
        else:
            candidatos = list(base.values_list('id', flat=True))
            if len(candidatos) < simulacro.num_preguntas:
                raise ContenidoInsuficienteError(
                    'No hay suficientes preguntas aprobadas en el banco del área.',
                    [
                        (
                            f'Hay {len(candidatos)} preguntas aprobadas disponibles '
                            f'y el simulacro requiere {simulacro.num_preguntas}.'
                        )
                    ],
                )
            seleccionados = random.sample(candidatos, simulacro.num_preguntas)

        random.shuffle(seleccionados)

    SimulacroPregunta.objects.filter(simulacro=simulacro).delete()
    SimulacroPregunta.objects.bulk_create([
        SimulacroPregunta(simulacro=simulacro, contenido_id=contenido_id, orden=indice)
        for indice, contenido_id in enumerate(seleccionados, start=1)
    ])


def guardar_distribuciones(simulacro, distribuciones):
    """Reemplaza las distribuciones del simulacro por las ya validadas."""
    simulacro.distribuciones.all().delete()
    DistribucionSimulacro.objects.bulk_create([
        DistribucionSimulacro(
            simulacro=simulacro,
            competencia=distribucion.get('competencia'),
            afirmacion=distribucion.get('afirmacion'),
            parte=distribucion.get('parte'),
            cantidad=distribucion['cantidad'],
        )
        for distribucion in distribuciones
    ])
