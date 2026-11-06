"""
Capa interpretativa del reporte (ADR-015): comparación, calidad de datos,
hallazgos y conclusiones DESCRIPTIVAS.

Principios (analista de datos / gobierno del dato):
  - Reglas explícitas y reproducibles sobre las cifras ya calculadas: nada
    de IA generativa ni de texto inventado. Cada hallazgo trae su evidencia
    (indicador, valor y tamaño de la muestra) y un filtro para verlo.
  - Se describe, no se infiere causalidad. Las variaciones entre momentos
    se acompañan de la advertencia de que pueden medir RA distintos.
  - Muestras pequeñas (n < 30 estudiantes) se advierten siempre.
  - La calidad de los datos es un hallazgo más: un vacío no es un resultado.
"""

from collections import defaultdict

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    MomentoEvaluacion,
    PerfilAcademico,
    ResultadoAprendizaje,
)

from .servicio_desempeno_ra import METRICA_PROVISIONAL, porcentaje, ra_logrado

MUESTRA_MINIMA = 30
VARIACION_RELEVANTE_PP = 10
ERROR_ALTO = 70
PARTICIPACION_BAJA = 80


def _medida(g) -> dict:
    pct = porcentaje(g['aciertos'], g['presentadas'])
    return {'porcentaje': pct, 'presentadas': g['presentadas'], 'estudiantes': len(g['estudiantes']),
            'logrado': ra_logrado(pct)}


def comparacion(obs, a) -> dict:
    """Comparaciones entre dimensiones equivalentes con los mismos criterios."""
    def agrupar(clave, etiqueta, filtro):
        grupos = defaultdict(lambda: {'aciertos': 0, 'presentadas': 0, 'estudiantes': set()})
        nombres = {}
        for o in obs:
            k = clave(o)
            g = grupos[k]
            g['presentadas'] += 1
            g['aciertos'] += int(o.acierto)
            g['estudiantes'].add(o.estudiante)
            nombres.setdefault(k, etiqueta(o))
        return sorted(({'id': k, 'nombre': nombres[k], **_medida(g), 'filtro': filtro(k)} for k, g in grupos.items()),
                      key=lambda x: x['nombre'])

    variaciones = []
    if a['tendencia'].get('disponible'):
        general = a['tendencia']['general']
        momentos = a['tendencia']['momentos']
        for i in range(1, len(general)):
            antes, ahora = general[i - 1]['porcentaje'], general[i]['porcentaje']
            if antes is None or ahora is None:
                continue
            variaciones.append({'desde': momentos[i - 1]['nombre'], 'hasta': momentos[i]['nombre'],
                                'antes': antes, 'despues': ahora, 'variacion_pp': round(ahora - antes, 1)})
    return {
        'por_programa': agrupar(lambda o: o.programa.id, lambda o: f'{o.programa.codigo} · {o.programa.nombre}',
                                lambda k: {'programa': k}),
        'por_semestre': agrupar(lambda o: o.semestre or 0,
                                lambda o: f'Semestre {o.semestre}' if o.semestre else 'Sin semestre en la malla',
                                lambda k: {'semestre': k} if k else {}),
        'por_momento': agrupar(lambda o: o.momento.id, lambda o: f'{o.momento.nombre} · {o.programa.codigo}',
                               lambda k: {'momento': k}),
        'variaciones': variaciones,
        'advertencia': ('Comparar solo dimensiones medidas con los mismos criterios. Cada momento puede evaluar RA y '
                        'preguntas distintas: una variación no se atribuye por sí sola a un cambio de desempeño.'),
    }


def calidad_datos(programa_id=None) -> list:
    """Vacíos de información que limitan el análisis (no son resultados académicos)."""
    from apps.users.models import User

    asignaturas = AsignaturaMalla.objects.filter(activo=True)
    momentos = MomentoEvaluacion.objects.filter(activo=True)
    ras = ResultadoAprendizaje.objects.filter(activo=True)
    if programa_id:
        asignaturas = asignaturas.filter(programa_id=programa_id)
        momentos = momentos.filter(programa_id=programa_id)
        ras = ras.filter(competencia__programa_id=programa_id)
    total_asig = asignaturas.count()
    total_mom = momentos.count()
    estudiantes = User.objects.filter(role__name='Estudiante', is_active=True).count()
    items = [
        {'clave': 'asignaturas_sin_semestre', 'titulo': 'Asignaturas activas sin semestre en la malla',
         'valor': asignaturas.filter(semestre__isnull=True).count(), 'total': total_asig,
         'impacto': 'El desglose por semestre las agrupa como "Sin semestre en la malla".'},
        {'clave': 'asignaturas_sin_curso', 'titulo': 'Asignaturas activas sin curso (docente) vinculado',
         'valor': asignaturas.filter(curso_vinculado__isnull=True).count(), 'total': total_asig,
         'impacto': 'Sin curso no hay convocatoria por curso, ni docente asociado, ni participación por curso.'},
        {'clave': 'momentos_sin_periodo', 'titulo': 'Momentos activos sin periodo académico',
         'valor': momentos.filter(periodo='').count(), 'total': total_mom,
         'impacto': 'No se puede comparar por periodo académico; se compara por momento y fecha.'},
        {'clave': 'ra_sin_preguntas', 'titulo': 'RA activos sin preguntas aprobadas en el banco',
         'valor': ras.exclude(preguntas_banco__estado='aprobada').distinct().count(), 'total': ras.count(),
         'impacto': 'No pueden evaluarse con cuestionario hasta que el docente apruebe preguntas.'},
        {'clave': 'estudiantes_sin_perfil', 'titulo': 'Estudiantes sin perfil académico (código, programa, semestre)',
         'valor': max(0, estudiantes - PerfilAcademico.objects.filter(usuario__role__name='Estudiante').count()),
         'total': estudiantes,
         'impacto': 'No hay cohortes ni semestre del estudiante: no se calculan deserción ni retención.'},
    ]
    for item in items:
        item['porcentaje'] = porcentaje(item['valor'], item['total'])
    return items


def hallazgos(a) -> list:
    """Situaciones relevantes, priorizadas (1 = más importante)."""
    u = METRICA_PROVISIONAL['umbral_logro_porcentaje']
    lista = []

    def agregar(tipo, prioridad, titulo, detalle, indicador, valor, n=None, filtro=None, etapa='profundizar'):
        lista.append({'tipo': tipo, 'prioridad': prioridad, 'titulo': titulo, 'detalle': detalle,
                      'evidencia': {'indicador': indicador, 'valor': valor, 'n': n}, 'filtro': filtro, 'etapa': etapa})

    g = a['logro_general']
    if g['presentadas'] == 0:
        agregar('calidad', 1, 'No hay resultados con estos filtros',
                'No se encontraron evaluaciones formales presentadas. Amplía los filtros o verifica que haya evaluaciones publicadas.',
                'logro_general', None, 0, etapa='panorama')
        return lista
    if g['estudiantes'] < MUESTRA_MINIMA:
        agregar('calidad', 2, f'Muestra pequeña: {g["estudiantes"]} estudiante(s)',
                f'Con menos de {MUESTRA_MINIMA} estudiantes los porcentajes son inestables: úsalos como indicio, no como conclusión.',
                'logro_general', g['porcentaje'], g['presentadas'], etapa='evidencia')

    debiles = [r for r in a['logro_ra'] if r['porcentaje'] is not None and r['porcentaje'] < u]
    for r in debiles[:3]:
        agregar('atencion', 3, f'RA por debajo del umbral: {r["porcentaje"]} %',
                f'"{r["descripcion"]}" ({r["asignatura"]}, {r["competencia"]}) está {round(u - r["porcentaje"], 1)} pp por debajo del umbral de {u} %.',
                'logro_ra', r['porcentaje'], r['presentadas'], r['filtro'])
    fuertes = [r for r in a['logro_ra'] if r['porcentaje'] is not None and r['porcentaje'] >= u + 20]
    for r in fuertes[-2:]:
        agregar('positivo', 6, f'RA con logro alto: {r["porcentaje"]} %',
                f'"{r["descripcion"]}" ({r["asignatura"]}) supera el umbral en {round(r["porcentaje"] - u, 1)} pp.',
                'logro_ra', r['porcentaje'], r['presentadas'], r['filtro'])

    tipos = a['logro_por_tipo']
    if tipos.get('especifica') and tipos.get('transversal'):
        e, t = tipos['especifica']['porcentaje'], tipos['transversal']['porcentaje']
        if e is not None and t is not None and abs(e - t) >= VARIACION_RELEVANTE_PP:
            menor = 'transversales' if t < e else 'específicas'
            agregar('informativo', 5, f'Brecha entre competencias: {abs(round(e - t, 1))} pp',
                    f'Las competencias {menor} tienen menor logro (específicas {e} %, transversales {t} %).',
                    'logro_competencia', abs(round(e - t, 1)), etapa='comparar')

    for c in a['cobertura']:
        if c['sin_evaluar']:
            agregar('atencion', 4, f'{c["nombre"]}: {len(c["sin_evaluar"])} RA obligatorio(s) sin evaluar',
                    f'Cobertura {c["evaluados"]} de {c["obligatorios"]} en {c["programa"]}. Sin evaluación publicada: '
                    + '; '.join(r['descripcion'].rstrip('.') for r in c['sin_evaluar'][:3]) + '.',
                    'cobertura_ra', c['porcentaje'], filtro={'momento': c['momento']}, etapa='comparar')

    p = a['participacion']
    if p['porcentaje_participacion'] is not None and p['porcentaje_participacion'] < PARTICIPACION_BAJA:
        agregar('atencion', 4, f'Participación de {p["porcentaje_participacion"]} %',
                f'{p["presentaron"]} de {p["convocados"]} convocatorias se presentaron. La baja participación reduce la representatividad del logro.',
                'participacion', p['porcentaje_participacion'], p['convocados'])

    for v in a.get('comparacion', {}).get('variaciones', []):
        if abs(v['variacion_pp']) >= VARIACION_RELEVANTE_PP:
            sube = v['variacion_pp'] > 0
            agregar('positivo' if sube else 'atencion', 5,
                    f'{"Aumento" if sube else "Descenso"} de {abs(v["variacion_pp"])} pp entre momentos',
                    f'De {v["desde"]} ({v["antes"]} %) a {v["hasta"]} ({v["despues"]} %). Verifica que ambos momentos midan RA comparables.',
                    'logro_general', v['variacion_pp'], etapa='comparar')

    for q in a['mapas']['preguntas_error']:
        if (q['porcentaje_error'] or 0) >= ERROR_ALTO and q['presentadas'] >= 2:
            agregar('atencion', 6, f'Pregunta con {q["porcentaje_error"]} % de error',
                    f'"{q["enunciado"][:110]}…" ({q["asignatura"]}). Revisar redacción, dificultad o enseñanza del tema.',
                    'preguntas_error', q['porcentaje_error'], q['presentadas'], q['filtro'])
            break

    integ = a['integridad']
    if integ['anulaciones'] or integ['suspendidos_ahora']:
        agregar('atencion', 5, f'Integridad: {integ["anulaciones"]} anulación(es), {integ["suspendidos_ahora"]} suspendido(s)',
                'Los anulados por fraude se excluyen del logro. Los suspendidos esperan la decisión del docente.',
                'integridad', integ['anulaciones'], etapa='evidencia')
    if a['alertas']['abiertas']:
        agregar('atencion', 5, f'{a["alertas"]["abiertas"]} alerta(s) temprana(s) abiertas',
                'Estudiantes o cursos con varias actividades por debajo del umbral de la regla de alertas.',
                'alertas', a['alertas']['abiertas'], etapa='evidencia')

    for item in a.get('calidad_datos', []):
        if item['valor'] and item['total'] and item['porcentaje'] and item['porcentaje'] >= 20:
            agregar('calidad', 7, f'{item["titulo"]}: {item["valor"]} de {item["total"]}', item['impacto'],
                    'calidad_datos', item['porcentaje'], etapa='evidencia')

    lista.sort(key=lambda h: h['prioridad'])
    return lista


def conclusiones(a) -> dict:
    """Síntesis descriptiva en lenguaje claro, con las limitaciones visibles."""
    u = METRICA_PROVISIONAL['umbral_logro_porcentaje']
    g = a['logro_general']
    if g['presentadas'] == 0:
        return {'puntos': ['No hay evaluaciones formales presentadas con los filtros aplicados.'], 'limitaciones': []}
    puntos = [
        f'Se analizaron {g["presentadas"]} respuestas de {g["estudiantes"]} estudiante(s) en '
        f'{a["evaluaciones"]["presentadas"]} evaluación(es) con resultados.',
        f'El logro general es {g["porcentaje"]} %; {g["ra_logrados"]} de {g["ra_evaluados"]} RA alcanzan el umbral de {u} %.',
    ]
    if a['logro_ra']:
        peor, mejor = a['logro_ra'][0], a['logro_ra'][-1]
        puntos.append(f'El RA con menor logro es "{peor["descripcion"]}" ({peor["porcentaje"]} %, n={peor["presentadas"]})'
                      + (f' y el de mayor logro "{mejor["descripcion"]}" ({mejor["porcentaje"]} %).' if mejor is not peor else '.'))
    obligatorios = sum(c['obligatorios'] for c in a['cobertura'])
    if obligatorios:
        evaluados = sum(c['evaluados'] for c in a['cobertura'])
        puntos.append(f'Cobertura de RA obligatorios: {evaluados} de {obligatorios} con evaluación publicada.')
    p = a['participacion']
    if p['convocados']:
        puntos.append(f'Participación: {p["presentaron"]} de {p["convocados"]} convocatorias ({p["porcentaje_participacion"]} %).')
    if a['niveles']['total']:
        puntos.append(f'Aprobación (nivel Suficiente o superior): {a["niveles"]["aprobacion"]} % de {a["niveles"]["total"]} notas.')
    limitaciones = [
        'Conclusiones descriptivas: no establecen causas.',
        f'Métrica provisional (umbral {u} %, niveles y tratamiento de preguntas sin responder), pendiente de definición con Vicerrectoría (ADR-006).',
        'Indicadores institucionales propios: no son indicadores oficiales del MEN.',
    ]
    if g['estudiantes'] < MUESTRA_MINIMA:
        limitaciones.append(f'Muestra pequeña ({g["estudiantes"]} estudiante(s); mínimo sugerido {MUESTRA_MINIMA}): las cifras son indicativas.')
    for item in a.get('calidad_datos', []):
        if item['valor'] and item['clave'] in ('momentos_sin_periodo', 'estudiantes_sin_perfil'):
            limitaciones.append(f'{item["titulo"]}: {item["valor"]} de {item["total"]}. {item["impacto"]}')
    return {'puntos': puntos, 'limitaciones': limitaciones}
