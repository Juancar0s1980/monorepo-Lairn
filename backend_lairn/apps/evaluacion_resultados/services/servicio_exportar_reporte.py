"""
Exportación del informe de resultados de aprendizaje a PDF (reportlab) y Excel
(openpyxl). HU-11.3, ADR-011, ADR-015 y ADR-016.

Reglas:
  - Mismos datos que la pantalla: el archivo se arma con el mismo diccionario
    que devuelve `vista_reporte_ejecutivo._datos` (indicadores, desglose y
    `analitica` con hallazgos, conclusiones, comparación y calidad de datos).
    No se recalcula nada aquí: solo se presenta.
  - Misma secuencia que la pantalla (ADR-015): Panorama → Hallazgos →
    Profundizar → Comparar → Conclusiones → Evidencia y metodología.
  - Cada tabla y gráfico lleva título, unidad y fuente. Los gráficos se dibujan
    con matplotlib a partir de las mismas cifras; si no hay datos, no hay gráfico.
  - Contenido agregado: no incluye nombres ni documentos de estudiantes
    (protección de datos personales, Ley 1581 de 2012).
"""

import io
from xml.sax.saxutils import escape

from django.utils import timezone

from .servicio_analitica_ra import ZONA_INSTITUCIONAL
from .escala_institucional import FUENTES as FUENTES_ESCALA, rangos as rangos_escala

# Escala institucional (ADR-019), con un decimal (Acuerdo 005, Art. 45).
TEXTO_ESCALA = ('Niveles de nota (0-5, un decimal): '
                + ' · '.join(f'{e} {mn}-{mx}'.replace('.', ',') for _c, e, mn, mx in rangos_escala())
                + f". Fuente: {FUENTES_ESCALA['niveles']}.")

INSTITUCION = 'Corporación Universitaria Autónoma del Cauca'
SISTEMA = 'LAIRN'
ETIQUETAS_FILTRO = {
    'programa': 'Programa', 'semestre': 'Semestre', 'momento': 'Momento', 'desde': 'Desde', 'hasta': 'Hasta',
    'asignatura': 'Asignatura', 'docente': 'Docente', 'competencia': 'Competencia', 'resultado': 'RA',
    'evaluacion': 'Evaluación',
}
AVISO_DATOS = ('Uso institucional. Información agregada: no incluye datos personales de estudiantes '
               '(Ley 1581 de 2012).')

FUENTE_RA = 'intentos enviados (no anulados) de evaluaciones formales tipo cuestionario · ' + SISTEMA
FUENTE_NOTAS = 'notas por asignatura de intentos y tareas calificadas · ' + SISTEMA
FUENTE_PARTICIPACION = 'ev_convocados_evaluacion, ev_intentos_evaluacion, ev_asistencias_evaluacion · ' + SISTEMA
FUENTE_INTEGRIDAD = 'ev_incidentes_intento, ev_resoluciones_integridad · ' + SISTEMA
FUENTE_COBERTURA = 'ev_momentos_resultados, ev_evaluaciones_formales · ' + SISTEMA
FUENTE_CALIDAD = 'malla curricular, momentos, banco de preguntas y perfiles académicos · ' + SISTEMA
FUENTE_HALLAZGOS = 'reglas explícitas sobre las cifras de este informe (ADR-015) · ' + SISTEMA

ETAPAS = [
    ('Panorama', '¿Cuál es la situación actual?'),
    ('Hallazgos', '¿Qué requiere atención y qué va bien?'),
    ('Profundizar', '¿Dónde ocurre?'),
    ('Comparar', '¿Qué cambió y cómo se comparan?'),
    ('Conclusiones', '¿Qué se puede concluir?'),
    ('Evidencia y metodología', '¿Qué respalda estas cifras?'),
]
TIPO_HALLAZGO = {
    'atencion': 'Requiere atención', 'positivo': 'Resultado favorable',
    'informativo': 'Para tener en cuenta', 'calidad': 'Calidad de los datos',
}
REFERENTES = [
    'Decreto 1330 de 2019 (MEN): condiciones de calidad; los programas definen y evalúan resultados de aprendizaje.',
    'Acuerdo CESU 02 de 2020, Factor 5 (aspectos académicos y resultados de aprendizaje). '
    'El Acuerdo CESU 01 de 2025 actualiza el modelo: confirmar la versión vigente antes de citarla en un trámite.',
    'Resolución Uniautónoma 0125 de 2022: lineamientos para formular y evaluar resultados de aprendizaje '
    '(por validar con Vicerrectoría).',
    'Todos los indicadores de este informe son institucionales propios; ninguno es un indicador oficial del MEN '
    '(SNIES, SPADIES).',
]


# ------------------------------------------------------------------ utilidades

def _v(valor, sufijo=''):
    return '—' if valor is None else f'{valor}{sufijo}'


def _pct(valor):
    return '—' if valor is None else f'{valor:.1f} %'.replace('.', ',')


def _titulo(datos) -> str:
    if datos['nivel'] == 'institucion':
        return 'Reporte institucional de evaluación de resultados de aprendizaje'
    return f"Reporte del programa {datos['programa']['codigo']} — {datos['programa']['nombre']}"


def _filtros_texto(datos) -> str:
    analitica = datos.get('analitica') or {}
    ruta = ' → '.join(r['nombre'] for r in analitica.get('ruta', []))
    otros = [f'{ETIQUETAS_FILTRO.get(k, k)}: {v}' for k, v in (analitica.get('filtros') or {}).items()
             if k in ('momento', 'desde', 'hasta', 'docente', 'competencia')]
    partes = [f'Nivel: {ruta}' if ruta else 'Nivel: Institución']
    if otros:
        partes.append('Filtros: ' + '; '.join(otros))
    return ' · '.join(partes)


def _corte(datos):
    return timezone.localtime(
        datos['analitica']['fecha_corte'] if datos.get('analitica') else timezone.now(), timezone=ZONA_INSTITUCIONAL,
    )


def _periodo(datos) -> str:
    f = (datos.get('analitica') or {}).get('filtros') or {}
    if f.get('desde') or f.get('hasta'):
        return f"Periodo: {f.get('desde') or 'inicio'} a {f.get('hasta') or 'corte'}"
    return 'Periodo: todo el historial disponible'


def _cabecera(datos) -> list:
    filas = [INSTITUCION, _titulo(datos), _filtros_texto(datos),
             f'Fecha de corte: {_corte(datos):%Y-%m-%d %H:%M} (hora de Colombia)']
    if datos.get('analitica'):
        filas.append(datos['analitica']['metrica_provisional']['aviso'])
    return filas


def _filas_indicadores(ind) -> list:
    return [
        ('Estudiantes evaluados', ind['estudiantes']),
        ('Resultados registrados', ind['resultados']),
        ('Puntaje promedio (0-5)', _v(ind['promedio'])),
        ('Desviación estándar', _v(ind['desviacion'])),
        ('Resultados por encima de la media', ind['por_encima']),
        ('Resultados por debajo de la media', ind['por_debajo']),
    ]


def _encabezado_desglose(datos) -> list:
    nivel = 'Programa' if datos['nivel'] == 'institucion' else 'Materia'
    return ['Código', nivel, 'Estudiantes', 'Resultados', 'Promedio', 'Desviación', 'Sobre la media', 'Bajo la media']


def _filas_desglose(datos) -> list:
    return [
        [d['codigo'], d['nombre'], d['estudiantes'], d['resultados'], _v(d['promedio']), _v(d['desviacion']),
         d['por_encima'], d['por_debajo']]
        for d in datos['desglose']
    ]


def _cobertura_total(a):
    oblig = sum(c['obligatorios'] for c in a['cobertura'])
    return sum(c['evaluados'] for c in a['cobertura']), oblig


def _kpis(a) -> list:
    """(indicador, valor, detalle) del panorama; mismas cifras que las tarjetas de la pantalla."""
    g, p, n = a['logro_general'], a['participacion'], a['niveles']
    evaluados, obligatorios = _cobertura_total(a)
    umbral = a['metrica_provisional']['umbral_logro_porcentaje']
    return [
        ('% de logro general', _pct(g['porcentaje']), f"n = {g['presentadas']} respuestas · umbral {umbral} %"),
        ('RA logrados', f"{g['ra_logrados']} / {g['ra_evaluados']}", 'RA con al menos una respuesta'),
        ('% de aprobación', _pct(n['aprobacion']), f"nivel Suficiente o superior · {n['total']} notas"),
        ('Cobertura de RA obligatorios', f'{evaluados} / {obligatorios}', 'con evaluación publicada'),
        ('Participación', _pct(p['porcentaje_participacion']), f"{p['presentaron']} de {p['convocados']} convocatorias"),
        ('Evaluaciones con resultados', f"{a['evaluaciones']['presentadas']} / {a['evaluaciones']['publicadas']}",
         'publicadas'),
        ('Alertas tempranas abiertas', str(a['alertas']['abiertas']), 'estudiantes con alerta'),
        ('Integridad', f"{a['integridad']['suspensiones']} / {a['integridad']['anulaciones']}",
         'suspensiones / anulaciones'),
    ]


def _secciones(datos) -> list:
    """(título, encabezados, filas) de la analítica de RA, en el orden de la pantalla (hoja 'Analítica RA')."""
    a = datos.get('analitica')
    if not a:
        return []
    g, p, ev, integ, ctx = a['logro_general'], a['participacion'], a['evaluaciones'], a['integridad'], a['contexto']
    return [
        ('Resumen de logro (métrica provisional)', ['Indicador', 'Valor'], [
            ['% de logro general', _v(g['porcentaje'], ' %')],
            ['RA evaluados / logrados', f"{g['ra_evaluados']} / {g['ra_logrados']}"],
            ['Respuestas analizadas', g['presentadas']],
            ['% de aprobación (niveles Suficiente o superior)', _v(a['niveles']['aprobacion'], ' %')],
            ['Alertas tempranas abiertas', a['alertas']['abiertas']],
        ]),
        ('Evaluaciones formales', ['Estado', 'Cantidad'], [
            ['Publicadas', ev['publicadas']], ['Con resultados', ev['presentadas']],
            ['Pendientes (sin resultados)', ev['pendientes']], ['Abiertas ahora', ev['abiertas']],
            ['Borradores', ev['borradores']],
        ]),
        ('Convocatoria, asistencia y participación', ['Indicador', 'Valor'], [
            ['Convocados', p['convocados']], ['Iniciaron', p['iniciaron']], ['Presentaron', p['presentaron']],
            ['% de participación', _v(p['porcentaje_participacion'], ' %')],
            ['Presentes en sala (evaluaciones con supervisor)', f"{p['presentes']} de {p['convocados_con_control']}"],
            ['Anulados por fraude', p['anulados']],
        ]),
        ('Integridad académica', ['Indicador', 'Valor'], [
            ['Suspensiones', integ['suspensiones']], ['Anulaciones por fraude', integ['anulaciones']],
            ['Reactivaciones', integ['reactivaciones']], ['Suspendidas ahora', integ['suspendidos_ahora']],
        ]),
        ('Niveles de desempeño (provisional)', ['Nivel', 'Desde', 'Cantidad', '%'],
         [[n['etiqueta'], n['minimo'], n['cantidad'], _v(n['porcentaje'], ' %')] for n in a['niveles']['niveles']]),
        ('Logro por resultado de aprendizaje', ['RA', 'Competencia', 'Asignatura', '% logro', 'Respuestas', 'Estudiantes'],
         [[r['descripcion'], r['competencia'], r['asignatura'], _v(r['porcentaje'], ' %'), r['presentadas'],
           r['estudiantes']] for r in a['logro_ra']]),
        ('Logro por competencia', ['Competencia', 'Tipo', 'Programa', '% logro', 'Respuestas'],
         [[c['nombre'], c['tipo'], c['programa'], _v(c['porcentaje'], ' %'), c['presentadas']]
          for c in a['logro_competencia']]),
        ('Cobertura de RA obligatorios por momento', ['Momento', 'Programa', 'Obligatorios', 'Evaluados', 'Sin evaluar'],
         [[c['nombre'], c['programa'], c['obligatorios'], c['evaluados'],
           '; '.join(r['descripcion'] for r in c['sin_evaluar']) or '—'] for c in a['cobertura']]),
        ('Preguntas con mayor % de error', ['Pregunta', 'Asignatura', 'RA', '% error', 'Respuestas'],
         [[q['enunciado'], q['asignatura'], q['resultado'], _v(q['porcentaje_error'], ' %'), q['presentadas']]
          for q in a['mapas']['preguntas_error']]),
        ('Participación por curso', ['Curso', 'Convocados', 'Presentaron', '%'],
         [[c['nombre'], c['convocados'], c['presentaron'], _v(c['porcentaje'], ' %')]
          for c in a['mapas']['participacion_curso']]),
        ('Contexto institucional', ['Indicador', 'Cantidad'], [
            ['Programas activos', ctx['programas']], ['Estudiantes', ctx['estudiantes']], ['Docentes', ctx['docentes']],
            ['Coordinadores', ctx['coordinadores']], ['Asignaturas activas', ctx['asignaturas']],
            ['Cursos', ctx['cursos']],
        ]),
    ]


def _catalogo():
    from .servicio_indicadores import catalogo
    return catalogo()


# --------------------------------------------------------------------- gráficos
# Una sola serie por gráfico (sin leyenda: el título la nombra), un solo eje,
# marcas delgadas, rótulos selectivos y el umbral como línea de referencia.

AZUL = '#2a78d6'
TINTA = '#0b0b0b'
TINTA_2 = '#52514e'
TENUE = '#898781'
REJILLA = '#e1e0d9'


def _figura(ancho, alto):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.edgecolor': REJILLA,
                         'axes.labelcolor': TINTA_2, 'xtick.color': TENUE, 'ytick.color': TENUE})
    fig, ax = plt.subplots(figsize=(ancho, alto), dpi=150)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    return plt, fig, ax


def _png(plt, fig) -> bytes:
    salida = io.BytesIO()
    fig.tight_layout()
    fig.savefig(salida, format='png', facecolor='white')
    plt.close(fig)
    return salida.getvalue()


def _corto(texto, n=48):
    texto = ' '.join(str(texto).split())
    return texto if len(texto) <= n else texto[:n - 1] + '…'


def grafico_logro_ra(a, maximo=12):
    filas = [r for r in a['logro_ra'] if r['porcentaje'] is not None][:maximo]
    if not filas:
        return None
    filas = sorted(filas, key=lambda r: r['porcentaje'])
    plt, fig, ax = _figura(9, 0.45 * len(filas) + 1.1)
    y = range(len(filas))
    ax.barh(list(y), [r['porcentaje'] for r in filas], height=0.55, color=AZUL)
    ax.set_yticks(list(y), [_corto(r['descripcion']) for r in filas], color=TINTA_2)
    umbral = a['metrica_provisional']['umbral_logro_porcentaje']
    ax.axvline(umbral, color=TINTA_2, linestyle='--', linewidth=1)
    ax.text(umbral, len(filas) - 0.4, f' Umbral {umbral} %', color=TINTA_2, fontsize=7, va='bottom')
    for i, r in enumerate(filas):
        ax.text(r['porcentaje'] + 1, i, f"{r['porcentaje']:.1f} % (n={r['presentadas']})".replace('.', ','),
                va='center', fontsize=7, color=TINTA)
    ax.set_xlim(0, 112)
    ax.set_xlabel('% de logro')
    ax.grid(axis='x', color=REJILLA, linewidth=0.6)
    return _png(plt, fig)


def grafico_evolucion(a):
    t = a['tendencia']
    if not t.get('disponible'):
        return None
    nombres = {m['id']: f"{m['nombre']} · {m['programa']}" for m in t['momentos']}
    puntos = [(nombres[p['momento']], p['porcentaje'], p['presentadas']) for p in t['general']]
    plt, fig, ax = _figura(9, 2.8)
    x = list(range(len(puntos)))
    ax.plot(x, [p[1] for p in puntos], color=AZUL, linewidth=2, marker='o', markersize=5)
    for i, (_n, valor, n) in enumerate(puntos):
        if valor is not None:
            ax.annotate(f'{valor:.1f} % (n={n})'.replace('.', ','), (i, valor), textcoords='offset points',
                        xytext=(0, 7), ha='center', fontsize=7, color=TINTA)
    umbral = a['metrica_provisional']['umbral_logro_porcentaje']
    ax.axhline(umbral, color=TINTA_2, linestyle='--', linewidth=1)
    ax.text(-0.1, umbral + 1.5, f'Umbral {umbral} %', color=TINTA_2, fontsize=7, ha='left')
    ax.set_xticks(x, [_corto(p[0], 26) for p in puntos])
    ax.set_ylim(0, 105)
    ax.set_ylabel('% de logro general')
    ax.grid(axis='y', color=REJILLA, linewidth=0.6)
    return _png(plt, fig)


def grafico_niveles(a):
    niveles = a['niveles']
    if not niveles['total']:
        return None
    plt, fig, ax = _figura(9, 2.4)
    etiquetas = [f"{n['etiqueta']}\n(≥ {n['minimo']})" for n in niveles['niveles']]
    valores = [n['cantidad'] for n in niveles['niveles']]
    ax.bar(range(len(valores)), valores, width=0.55, color=AZUL)
    for i, n in enumerate(niveles['niveles']):
        ax.text(i, n['cantidad'], f"{n['cantidad']} ({_pct(n['porcentaje'])})", ha='center', va='bottom',
                fontsize=7, color=TINTA)
    ax.set_xticks(range(len(valores)), etiquetas)
    ax.set_ylabel('Notas (cantidad)')
    ax.set_ylim(0, max(valores) * 1.25 + 0.5)
    ax.grid(axis='y', color=REJILLA, linewidth=0.6)
    return _png(plt, fig)


# -------------------------------------------------------------------------- PDF

def _registrar_fuentes():
    """DejaVu (incluida con matplotlib) cubre →, ≥, Σ y tildes; Helvetica no."""
    import os

    import matplotlib
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if 'DejaVu' in pdfmetrics.getRegisteredFontNames():
        return 'DejaVu', 'DejaVu-Bold'
    ruta = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', os.path.join(ruta, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', os.path.join(ruta, 'DejaVuSans-Bold.ttf')))
        return 'DejaVu', 'DejaVu-Bold'
    except Exception:  # sin la fuente, el PDF se genera igual con Helvetica
        return 'Helvetica', 'Helvetica-Bold'


def a_pdf(datos) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as canvas_rl
    from reportlab.platypus import (
        CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    normal, negrita = _registrar_fuentes()
    a = datos.get('analitica')
    titulo = _titulo(datos)
    corte = _corte(datos)
    tamano = landscape(A4)
    ancho_util = tamano[0] - 3 * cm

    base = getSampleStyleSheet()
    e = {
        'normal': ParagraphStyle('n', parent=base['Normal'], fontName=normal, fontSize=8.5, leading=11),
        'celda': ParagraphStyle('c', parent=base['Normal'], fontName=normal, fontSize=7.5, leading=9.5),
        'celda_b': ParagraphStyle('cb', parent=base['Normal'], fontName=negrita, fontSize=7.5, leading=9.5),
        'tenue': ParagraphStyle('t', parent=base['Normal'], fontName=normal, fontSize=7, leading=9,
                                textColor=colors.HexColor(TINTA_2)),
        'titulo': ParagraphStyle('ti', parent=base['Title'], fontName=negrita, fontSize=18, leading=22,
                                 alignment=TA_LEFT, spaceAfter=4),
        'inst': ParagraphStyle('in', parent=base['Normal'], fontName=negrita, fontSize=10,
                               textColor=colors.HexColor(AZUL)),
        'etapa': ParagraphStyle('et', parent=base['Normal'], fontName=negrita, fontSize=8,
                                textColor=colors.HexColor(AZUL), spaceBefore=6),
        'h1': ParagraphStyle('h1', parent=base['Heading1'], fontName=negrita, fontSize=15, leading=18, spaceAfter=2),
        'h2': ParagraphStyle('h2', parent=base['Heading2'], fontName=negrita, fontSize=10.5, leading=13,
                             spaceBefore=8, spaceAfter=3, keepWithNext=1),
        'kpi_v': ParagraphStyle('kv', parent=base['Normal'], fontName=negrita, fontSize=15, leading=18),
    }

    def p(texto, estilo='normal'):
        return Paragraph(escape(str(texto)), e[estilo])

    def tabla(encabezado, filas, anchos=None, fuente=None, unidad=None, vacio='Sin datos con los filtros aplicados.'):
        piezas = []
        if not filas:
            piezas.append(p(vacio, 'tenue'))
        else:
            cuerpo = [[p(c, 'celda') for c in f] for f in filas]
            t = Table([[p(c, 'celda_b') for c in encabezado]] + cuerpo, repeatRows=1, colWidths=anchos)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8EEF7')),
                ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.HexColor(AZUL)),
                ('LINEBELOW', (0, 1), (-1, -1), 0.3, colors.HexColor(REJILLA)),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F7F5')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            piezas.append(t)
        nota = ' · '.join(x for x in [f'Unidad: {unidad}' if unidad else None, f'Fuente: {fuente}' if fuente else None]
                          if x)
        if nota:
            piezas.append(p(nota, 'tenue'))
        return piezas

    def figura(png, alto_cm, fuente):
        if not png:
            return []
        from reportlab.lib.utils import ImageReader
        lector = ImageReader(io.BytesIO(png))
        w, h = lector.getSize()
        alto = alto_cm * cm
        ancho = min(ancho_util, alto * w / h)
        return [Image(io.BytesIO(png), width=ancho, height=ancho * h / w), p(f'Fuente: {fuente}', 'tenue')]

    def etapa(i, contenido):
        nombre, pregunta = ETAPAS[i]
        contenido += [CondPageBreak(6 * cm), p(f'PASO {i + 1} DE 6 · {nombre.upper()}', 'etapa'), p(pregunta, 'h1')]

    class Lienzo(canvas_rl.Canvas):
        """Numera 'Página x de y' (requiere conocer el total: se dibuja al final)."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self._marco(total)
                super().showPage()
            super().save()

        def _marco(self, total):
            ancho, alto = tamano
            self.setStrokeColor(colors.HexColor(REJILLA))
            self.setFillColor(colors.HexColor(TINTA_2))
            if self._pageNumber > 1:
                self.setFont(negrita, 7.5)
                self.drawString(1.5 * cm, alto - 1.0 * cm, INSTITUCION)
                self.setFont(normal, 7.5)
                self.drawRightString(ancho - 1.5 * cm, alto - 1.0 * cm, _corto(titulo, 95))
                self.line(1.5 * cm, alto - 1.15 * cm, ancho - 1.5 * cm, alto - 1.15 * cm)
            self.line(1.5 * cm, 1.25 * cm, ancho - 1.5 * cm, 1.25 * cm)
            self.setFont(normal, 7)
            self.drawString(1.5 * cm, 0.85 * cm,
                            f'{SISTEMA} · corte {corte:%Y-%m-%d %H:%M} (hora de Colombia) · {AVISO_DATOS}')
            self.drawRightString(ancho - 1.5 * cm, 0.85 * cm, f'Página {self._pageNumber} de {total}')

    c = []
    # ---- Portada
    c += [p(INSTITUCION, 'inst'), Spacer(1, 4), p(titulo, 'titulo'),
          p('Informe de resultados de aprendizaje', 'h2'),
          p(_filtros_texto(datos)), p(_periodo(datos)),
          p(f'Fecha de corte: {corte:%Y-%m-%d %H:%M} (hora de Colombia)')]
    if a:
        c.append(p(a['metrica_provisional']['aviso'] + ' Indicadores institucionales propios: no son '
                   'indicadores oficiales del MEN.', 'tenue'))
    c += [Spacer(1, 8), p('Cómo leer este informe', 'h2')]
    c += tabla(['Paso', 'Pregunta que responde'], [[f'{i + 1}. {n}', q] for i, (n, q) in enumerate(ETAPAS)],
               anchos=[6 * cm, ancho_util - 6 * cm])

    if not a:
        c += [Spacer(1, 10), p('Indicadores generales', 'h2')]
        c += tabla(['Indicador', 'Valor'], [list(f) for f in _filas_indicadores(datos['indicadores'])],
                   fuente=FUENTE_NOTAS)
        c += [p('Desglose', 'h2')] + tabla(_encabezado_desglose(datos), _filas_desglose(datos), fuente=FUENTE_NOTAS)
        salida = io.BytesIO()
        SimpleDocTemplate(salida, pagesize=tamano, title=titulo, author=INSTITUCION,
                          leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm,
                          bottomMargin=1.6 * cm).build(c, canvasmaker=Lienzo)
        return salida.getvalue()

    # ---- 1. Panorama
    c.append(PageBreak())
    etapa(0, c)
    kpis = _kpis(a)
    celdas = [[[p(k, 'tenue'), Paragraph(escape(v), e['kpi_v']), p(d, 'tenue')] for k, v, d in kpis[i:i + 4]]
              for i in (0, 4)]
    t = Table(celdas, colWidths=[ancho_util / 4] * 4)
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor(REJILLA)),
                           ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor(REJILLA)),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    c += [t, p(f'Fuente: {FUENTE_RA}; {FUENTE_PARTICIPACION}', 'tenue'), p('En resumen', 'h2')]
    c += [p(f'• {x}') for x in a['conclusiones']['puntos'][:3]]
    c += [p('Notas de evaluación (escala 0-5)', 'h2')]
    c += tabla(['Indicador', 'Valor'], [list(f) for f in _filas_indicadores(datos['indicadores'])],
               anchos=[9 * cm, 4 * cm], fuente=FUENTE_NOTAS, unidad='nota 0-5')

    # ---- 2. Hallazgos
    etapa(1, c)
    c.append(p('Situaciones detectadas con reglas explícitas y reproducibles, ordenadas por prioridad. '
               'Describen lo que muestran las cifras; no establecen causas.', 'tenue'))
    c += tabla(['Tipo', 'Hallazgo', 'Detalle', 'Evidencia'],
               [[TIPO_HALLAZGO.get(h['tipo'], h['tipo']), h['titulo'], h['detalle'],
                 f"{h['evidencia']['indicador'].replace('_', ' ')}"
                 + (f" = {h['evidencia']['valor']}" if h['evidencia']['valor'] is not None else '')
                 + (f" · n = {h['evidencia']['n']}" if h['evidencia'].get('n') is not None else '')]
                for h in a['hallazgos']],
               anchos=[3.2 * cm, 6 * cm, ancho_util - 14.2 * cm, 5 * cm], fuente=FUENTE_HALLAZGOS,
               vacio='No se detectaron situaciones relevantes con los filtros aplicados.')

    # ---- 3. Profundizar
    etapa(2, c)
    c += [p('Logro por resultado de aprendizaje', 'h2')]
    c += figura(grafico_logro_ra(a), 7.5, FUENTE_RA)
    c += tabla(['RA', 'Competencia', 'Asignatura', '% logro', 'Respuestas', 'Estudiantes', 'Estado'],
               [[r['descripcion'], r['competencia'], r['asignatura'], _pct(r['porcentaje']), r['presentadas'],
                 r['estudiantes'], 'Logrado' if r['logrado'] else 'No logrado' if r['logrado'] is False else '—']
                for r in a['logro_ra']],
               anchos=[ancho_util - 18.2 * cm, 4 * cm, 4 * cm, 2 * cm, 2.4 * cm, 2.4 * cm, 2.2 * cm],
               fuente=FUENTE_RA, unidad='% de preguntas acertadas')
    c += [p('Logro por competencia', 'h2')]
    c += tabla(['Competencia', 'Tipo', 'Programa', '% logro', 'Respuestas'],
               [[x['nombre'], x['tipo'], x['programa'], _pct(x['porcentaje']), x['presentadas']]
                for x in a['logro_competencia']], fuente=FUENTE_RA, unidad='%')
    c += [p('Desglose de notas por ' + ('programa' if datos['nivel'] == 'institucion' else 'materia'), 'h2')]
    c += tabla(_encabezado_desglose(datos), _filas_desglose(datos), fuente=FUENTE_NOTAS, unidad='nota 0-5',
               vacio='Aún no hay evaluaciones formales realizadas en este nivel.')
    c += [p('Preguntas con mayor % de error', 'h2')]
    c += tabla(['Pregunta', 'Asignatura', 'RA', '% error', 'Respuestas'],
               [[q['enunciado'], q['asignatura'], q['resultado'], _pct(q['porcentaje_error']), q['presentadas']]
                for q in a['mapas']['preguntas_error']],
               anchos=[ancho_util - 15.4 * cm, 4.5 * cm, 6.5 * cm, 2 * cm, 2.4 * cm], fuente=FUENTE_RA, unidad='%')

    # ---- 4. Comparar
    etapa(3, c)
    comp = a['comparacion']
    c.append(p(comp['advertencia'], 'tenue'))
    c += [p('Evolución del logro general por momento', 'h2')]
    graf = grafico_evolucion(a)
    c += figura(graf, 6, FUENTE_RA) if graf else [p(a['tendencia'].get('motivo', ''), 'tenue')]
    c += tabla(['Desde', 'Hasta', 'Antes', 'Después', 'Variación'],
               [[x['desde'], x['hasta'], _pct(x['antes']), _pct(x['despues']),
                 f"{x['variacion_pp']:+.1f} pp".replace('.', ',')] for x in comp['variaciones']],
               fuente=FUENTE_RA, unidad='% y puntos porcentuales (pp)',
               vacio='Sin variaciones: se necesitan resultados en al menos dos momentos.')
    for clave, nombre in (('por_programa', 'programa'), ('por_semestre', 'semestre'), ('por_momento', 'momento')):
        c += [p(f'Comparación por {nombre}', 'h2')]
        c += tabla([nombre.capitalize(), '% logro', 'Respuestas', 'Estudiantes'],
                   [[x['nombre'], _pct(x['porcentaje']), x['presentadas'], x['estudiantes']] for x in comp[clave]],
                   anchos=[ancho_util - 9 * cm, 3 * cm, 3 * cm, 3 * cm], fuente=FUENTE_RA, unidad='%')
    c += [p('Distribución de desempeño (notas 0-5 por nivel)', 'h2')]
    c += figura(grafico_niveles(a), 5.5, FUENTE_NOTAS)
    c += tabla(['Nivel', 'Desde', 'Cantidad', '%'],
               [[n['etiqueta'], n['minimo'], n['cantidad'], _pct(n['porcentaje'])] for n in a['niveles']['niveles']],
               anchos=[6 * cm, 3 * cm, 3 * cm, 3 * cm], fuente=FUENTE_NOTAS, unidad='notas y %')
    c += [p('Cobertura de RA obligatorios por momento', 'h2')]
    c += tabla(['Momento', 'Programa', 'Obligatorios', 'Evaluados', 'Sin evaluar'],
               [[x['nombre'], x['programa'], x['obligatorios'], x['evaluados'],
                 '; '.join(r['descripcion'] for r in x['sin_evaluar']) or '—'] for x in a['cobertura']],
               anchos=[5 * cm, 3.5 * cm, 2.5 * cm, 2.5 * cm, ancho_util - 13.5 * cm], fuente=FUENTE_COBERTURA)

    # ---- 5. Conclusiones
    etapa(4, c)
    c += [p('Conclusiones descriptivas', 'h2')] + [p(f'• {x}') for x in a['conclusiones']['puntos']]
    prioridades = [h for h in a['hallazgos'] if h['tipo'] == 'atencion'][:3]
    if prioridades:
        c += [p('Prioridades que se derivan de los hallazgos', 'h2')]
        c += [p(f"{i + 1}. {h['titulo']}: {h['detalle']}") for i, h in enumerate(prioridades)]
    c += [p('Limitaciones de este análisis', 'h2')] + [p(f'• {x}') for x in a['conclusiones']['limitaciones']]

    # ---- 6. Evidencia y metodología
    c.append(PageBreak())
    etapa(5, c)
    pa = a['participacion']
    c += [p('Convocatoria, asistencia y participación', 'h2')]
    c += tabla(['Indicador', 'Valor'], [
        ['Convocados', pa['convocados']], ['Iniciaron', pa['iniciaron']], ['Presentaron', pa['presentaron']],
        ['% de participación', _pct(pa['porcentaje_participacion'])],
        ['Presentes en sala (evaluaciones con supervisor)', f"{pa['presentes']} de {pa['convocados_con_control']}"],
        ['Anulados por fraude', pa['anulados']]], anchos=[9 * cm, 4 * cm], fuente=FUENTE_PARTICIPACION)
    c += [p('Participación por curso', 'h2')]
    c += tabla(['Curso', 'Convocados', 'Presentaron', '%'],
               [[x['nombre'], x['convocados'], x['presentaron'], _pct(x['porcentaje'])]
                for x in a['mapas']['participacion_curso']], fuente=FUENTE_PARTICIPACION)
    ig = a['integridad']
    c += [p('Integridad académica', 'h2')]
    c += tabla(['Indicador', 'Valor'], [['Suspensiones', ig['suspensiones']], ['Anulaciones por fraude', ig['anulaciones']],
                                        ['Reactivaciones', ig['reactivaciones']],
                                        ['Suspendidas ahora', ig['suspendidos_ahora']]],
               anchos=[9 * cm, 4 * cm], fuente=FUENTE_INTEGRIDAD)
    c += [p('Calidad y suficiencia de los datos', 'h2'),
          p('Vacíos que limitan el análisis. Un vacío no es un resultado académico.', 'tenue')]
    c += tabla(['Aspecto', 'Casos', 'Impacto en el análisis'],
               [[x['titulo'], f"{x['valor']} / {x['total']}", x['impacto']] for x in a['calidad_datos']],
               anchos=[8 * cm, 2.5 * cm, ancho_util - 10.5 * cm], fuente=FUENTE_CALIDAD)
    ctx = a['contexto']
    c += [p('Contexto institucional', 'h2')]
    c += tabla(['Indicador', 'Cantidad'], [
        ['Programas activos', ctx['programas']], ['Estudiantes', ctx['estudiantes']], ['Docentes', ctx['docentes']],
        ['Coordinadores', ctx['coordinadores']], ['Asignaturas activas', ctx['asignaturas']], ['Cursos', ctx['cursos']]],
        anchos=[9 * cm, 4 * cm], fuente=SISTEMA)

    c += [PageBreak(), p('Metodología', 'h1')]
    mp = a['metrica_provisional']
    c += [p(f"• Un RA se considera logrado con un % de logro ≥ {mp['umbral_logro_porcentaje']} %."),
          p('• Las preguntas sin responder cuentan como no acertadas.' if mp['sin_responder_es_fallo'] else
            '• Las preguntas sin responder no se cuentan.'),
          p('• Se excluyen los intentos anulados por fraude. El logro se pondera por pregunta, no por estudiante.'),
          p('• ' + TEXTO_ESCALA),
          p('• ' + mp['aviso'])]
    c += [p('Referentes', 'h2')] + [p(f'• {r}') for r in REFERENTES]
    c += [p('Indicadores oficiales que no se pueden calcular', 'h2')]
    c += tabla(['Indicador', 'Referente', 'Dato que falta'],
               [[x['nombre'], x['referente'], x['falta']] for x in a['indicadores_no_disponibles']],
               anchos=[6 * cm, 5 * cm, ancho_util - 11 * cm])
    c += [p('Fichas técnicas de los indicadores', 'h2')]
    for f in _catalogo():
        filas = [['Objetivo', f['objetivo']], ['Fórmula', f['formula']], ['Numerador', f['numerador']],
                 ['Denominador', f['denominador']], ['Unidad · periodicidad', f"{f['unidad']} · {f['periodicidad']}"],
                 ['Desagregación', f['desagregacion']], ['Fuente', f['fuente']],
                 ['Interpretación', f['interpretacion']], ['Limitaciones', f['limitaciones']]]
        cab = f"{f['nombre']} — {f['tipo']}" + (' · métrica provisional' if f['provisional'] else '')
        c.append(KeepTogether(tabla(['', cab], filas, anchos=[4 * cm, ancho_util - 4 * cm]) + [Spacer(1, 4)]))

    salida = io.BytesIO()
    SimpleDocTemplate(salida, pagesize=tamano, title=titulo, author=INSTITUCION, subject='Resultados de aprendizaje',
                      leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm,
                      bottomMargin=1.6 * cm).build(c, canvasmaker=Lienzo)
    return salida.getvalue()


# ------------------------------------------------------------------------ Excel

def a_excel(datos) -> bytes:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    a = datos.get('analitica')
    titulo = _titulo(datos)
    corte = _corte(datos)
    cab_fill = PatternFill('solid', fgColor='1F4E8C')
    cab_font = Font(bold=True, color='FFFFFF')
    borde = Border(bottom=Side(style='thin', color='E1E0D9'))
    envolver = Alignment(wrap_text=True, vertical='top')
    PCT, NUM = '0.0%', '0'

    libro = Workbook()

    def encabezar(hoja, subtitulo, fuente=None):
        hoja['A1'] = INSTITUCION
        hoja['A1'].font = Font(bold=True, size=12, color='1F4E8C')
        hoja['A2'] = f'{titulo} — {subtitulo}'
        hoja['A2'].font = Font(bold=True, size=13)
        hoja['A3'] = f'{_filtros_texto(datos)} · {_periodo(datos)} · corte {corte:%Y-%m-%d %H:%M} (hora de Colombia)'
        hoja['A4'] = ' · '.join(x for x in [f'Fuente: {fuente}' if fuente else None, AVISO_DATOS] if x)
        for celda in ('A3', 'A4'):
            hoja[celda].font = Font(size=9, color='52514E')

    def tabla(hoja, encabezados, filas, anchos, formatos=None, fila_inicio=6, filtro=True):
        """Escribe una tabla con encabezado fijo y autofiltro. Devuelve (primera, última) fila de datos."""
        formatos = formatos or {}
        for j, texto in enumerate(encabezados, start=1):
            c = hoja.cell(row=fila_inicio, column=j, value=texto)
            c.fill, c.font, c.alignment = cab_fill, cab_font, Alignment(wrap_text=True, vertical='center')
        for i, fila in enumerate(filas, start=fila_inicio + 1):
            for j, valor in enumerate(fila, start=1):
                c = hoja.cell(row=i, column=j, value=valor)
                c.alignment, c.border = envolver, borde
                if j in formatos and isinstance(valor, (int, float)):
                    c.number_format = formatos[j]
        for j, ancho in enumerate(anchos, start=1):
            hoja.column_dimensions[get_column_letter(j)].width = ancho
        ultima = fila_inicio + max(len(filas), 0)
        if filtro and filas:
            hoja.auto_filter.ref = f'A{fila_inicio}:{get_column_letter(len(encabezados))}{ultima}'
        if filtro:
            hoja.freeze_panes = f'A{fila_inicio + 1}'
        if not filas:
            hoja.cell(row=fila_inicio + 1, column=1, value='Sin datos con los filtros aplicados.')
        return fila_inicio + 1, ultima

    def fr(valor):
        """Porcentaje 0-100 → fracción para el formato 0.0 % de Excel; None queda vacío."""
        return None if valor is None else round(valor / 100, 4)

    # ---- Resumen (panorama + conclusiones)
    hoja = libro.active
    hoja.title = 'Resumen'
    encabezar(hoja, 'Resumen ejecutivo', FUENTE_RA if a else FUENTE_NOTAS)
    if a:
        hoja['A5'] = a['metrica_provisional']['aviso'] + ' Indicadores institucionales propios: no son oficiales del MEN.'
        hoja['A5'].font = Font(italic=True, size=9, color='9A6700')
        _p, ultima = tabla(hoja, ['Paso 1 · Panorama: indicador', 'Valor', 'Detalle'],
                           [list(k) for k in _kpis(a)], [44, 16, 50], filtro=False, fila_inicio=7)
        fila = ultima + 2
        for titulo_bloque, lineas in (('Paso 5 · Conclusiones descriptivas', a['conclusiones']['puntos']),
                                      ('Limitaciones de este análisis', a['conclusiones']['limitaciones'])):
            hoja.cell(row=fila, column=1, value=titulo_bloque).font = Font(bold=True, size=11)
            for linea in lineas:
                fila += 1
                c = hoja.cell(row=fila, column=1, value=f'• {linea}')
                c.alignment = Alignment(wrap_text=False)
            fila += 2
        hoja.cell(row=fila, column=1, value='Cómo leer este libro').font = Font(bold=True, size=11)
        for i, (n, q) in enumerate(ETAPAS):
            hoja.cell(row=fila + 1 + i, column=1, value=f'{i + 1}. {n}')
            hoja.cell(row=fila + 1 + i, column=2, value=q)

    # ---- Indicadores (notas 0-5; se conserva el nombre de la hoja de HU-11.3)
    ind = libro.create_sheet('Indicadores')
    for i, linea in enumerate(_cabecera(datos)):
        ind.cell(row=i + 1, column=1, value=linea).font = Font(bold=i < 2, size=14 if i == 1 else 11)
    inicio = len(_cabecera(datos)) + 2
    _p, ultima = tabla(ind, ['Indicador (notas 0-5)', 'Valor'], [list(f) for f in _filas_indicadores(datos['indicadores'])],
                       [48, 18], fila_inicio=inicio, filtro=False)
    tabla(ind, ['Distribución de puntajes', 'Cantidad'],
          [[r['rango'], r['cantidad']] for r in datos['indicadores']['distribucion']], [48, 18],
          fila_inicio=ultima + 2, filtro=False)

    if a:
        # ---- Hallazgos
        h = libro.create_sheet('Hallazgos')
        encabezar(h, 'Paso 2 · Hallazgos (¿qué requiere atención y qué va bien?)', FUENTE_HALLAZGOS)
        tabla(h, ['Prioridad', 'Tipo', 'Hallazgo', 'Detalle', 'Indicador', 'Valor', 'n'],
              [[x['prioridad'], TIPO_HALLAZGO.get(x['tipo'], x['tipo']), x['titulo'], x['detalle'],
                x['evidencia']['indicador'].replace('_', ' '), x['evidencia']['valor'], x['evidencia'].get('n')]
               for x in a['hallazgos']], [10, 20, 40, 70, 22, 10, 8])

        # ---- Logro por RA (+ gráfico nativo)
        r = libro.create_sheet('Logro por RA')
        encabezar(r, 'Paso 3 · Logro por resultado de aprendizaje (%)', FUENTE_RA)
        p1, u = tabla(r, ['RA', 'Competencia', 'Tipo', 'Asignatura', 'Programa', '% logro', 'Aciertos', 'Respuestas',
                          'Estudiantes', 'Estado'],
                      [[x['descripcion'], x['competencia'], x['tipo'], x['asignatura'], x['programa'],
                        fr(x['porcentaje']), x['aciertos'], x['presentadas'], x['estudiantes'],
                        'Logrado' if x['logrado'] else 'No logrado' if x['logrado'] is False else 'Sin datos']
                       for x in a['logro_ra']], [60, 30, 14, 30, 24, 10, 10, 11, 11, 12], {6: PCT})
        if a['logro_ra']:
            g = BarChart()
            g.type, g.title, g.style = 'bar', '% de logro por RA', 10
            g.y_axis.title, g.y_axis.number_format = '% de logro', '0%'
            g.y_axis.scaling.min, g.y_axis.scaling.max = 0, 1
            g.legend = None
            g.add_data(Reference(r, min_col=6, min_row=p1 - 1, max_row=u), titles_from_data=True)
            g.set_categories(Reference(r, min_col=1, min_row=p1, max_row=u))
            g.height, g.width = max(6, 0.9 * len(a['logro_ra']) + 3), 22
            r.add_chart(g, f'L{p1}')

        c = libro.create_sheet('Competencias')
        encabezar(c, 'Paso 3 · Logro por competencia (%)', FUENTE_RA)
        tabla(c, ['Competencia', 'Tipo', 'Programa', '% logro', 'Aciertos', 'Respuestas', 'Estudiantes'],
              [[x['nombre'], x['tipo'], x['programa'], fr(x['porcentaje']), x['aciertos'], x['presentadas'],
                x['estudiantes']] for x in a['logro_competencia']], [40, 14, 26, 10, 10, 11, 11], {4: PCT})

        q = libro.create_sheet('Preguntas')
        encabezar(q, 'Paso 3 · Preguntas con mayor % de error', FUENTE_RA)
        tabla(q, ['Pregunta', 'Asignatura', 'RA', '% error', 'Errores', 'Respuestas'],
              [[x['enunciado'], x['asignatura'], x['resultado'], fr(x['porcentaje_error']), x['errores'],
                x['presentadas']] for x in a['mapas']['preguntas_error']], [60, 28, 50, 10, 10, 11], {4: PCT})

        # ---- Comparación (+ evolución con gráfico de líneas)
        comp = a['comparacion']
        cm_ = libro.create_sheet('Comparación')
        encabezar(cm_, 'Paso 4 · Comparación por programa, semestre y momento (%)', FUENTE_RA)
        cm_['A5'] = comp['advertencia']
        cm_['A5'].font = Font(italic=True, size=9, color='9A6700')
        filas = [[d, x['nombre'], fr(x['porcentaje']), x['presentadas'], x['estudiantes']]
                 for clave, d in (('por_programa', 'Programa'), ('por_semestre', 'Semestre'), ('por_momento', 'Momento'))
                 for x in comp[clave]]
        tabla(cm_, ['Dimensión', 'Nombre', '% logro', 'Respuestas', 'Estudiantes'], filas, [14, 40, 10, 11, 11],
              {3: PCT}, fila_inicio=7)

        ev = libro.create_sheet('Evolución')
        encabezar(ev, 'Paso 4 · Evolución del logro general entre momentos (%)', FUENTE_RA)
        t = a['tendencia']
        if t.get('disponible'):
            nombres = {m['id']: f"{m['nombre']} · {m['programa']}" for m in t['momentos']}
            p1, u = tabla(ev, ['Momento', '% logro general', 'Respuestas', 'Estudiantes'],
                          [[nombres[x['momento']], fr(x['porcentaje']), x['presentadas'], x['estudiantes']]
                           for x in t['general']], [34, 16, 11, 11], {2: PCT}, filtro=False)
            linea = LineChart()
            linea.title, linea.legend, linea.style = '% de logro general por momento', None, 12
            linea.y_axis.number_format, linea.y_axis.scaling.min, linea.y_axis.scaling.max = '0%', 0, 1
            linea.add_data(Reference(ev, min_col=2, min_row=p1 - 1, max_row=u), titles_from_data=True)
            linea.set_categories(Reference(ev, min_col=1, min_row=p1, max_row=u))
            linea.height, linea.width = 8, 18
            ev.add_chart(linea, f'F{p1}')
            tabla(ev, ['Desde', 'Hasta', 'Antes', 'Después', 'Variación (pp)'],
                  [[x['desde'], x['hasta'], fr(x['antes']), fr(x['despues']), x['variacion_pp']]
                   for x in comp['variaciones']], [34, 16, 11, 11, 14], {3: PCT, 4: PCT, 5: '+0.0;-0.0;0.0'},
                  fila_inicio=u + 3, filtro=False)
        else:
            ev['A6'] = t.get('motivo', '')

        n = libro.create_sheet('Niveles')
        encabezar(n, 'Paso 4 · Distribución de desempeño (notas 0-5)', FUENTE_NOTAS)
        p1, u = tabla(n, ['Nivel', 'Desde', 'Cantidad', '%'],
                      [[x['etiqueta'], x['minimo'], x['cantidad'], fr(x['porcentaje'])] for x in a['niveles']['niveles']],
                      [20, 8, 10, 10], {4: PCT}, filtro=False)
        if a['niveles']['total']:
            b = BarChart()
            b.title, b.legend, b.style = 'Notas por nivel de desempeño', None, 10
            b.add_data(Reference(n, min_col=3, min_row=p1 - 1, max_row=u), titles_from_data=True)
            b.set_categories(Reference(n, min_col=1, min_row=p1, max_row=u))
            b.height, b.width = 7, 16
            n.add_chart(b, 'G6')

        co = libro.create_sheet('Cobertura')
        encabezar(co, 'Paso 4 · Cobertura de RA obligatorios por momento', FUENTE_COBERTURA)
        tabla(co, ['Momento', 'Programa', 'Semestre', 'Obligatorios', 'Evaluados', '% cobertura', 'Sin evaluar'],
              [[x['nombre'], x['programa'], x['semestre'], x['obligatorios'], x['evaluados'], fr(x['porcentaje']),
                '; '.join(s['descripcion'] for s in x['sin_evaluar']) or '—'] for x in a['cobertura']],
              [30, 16, 10, 12, 11, 12, 70], {6: PCT})

        # ---- Evidencia
        pa = libro.create_sheet('Participación')
        encabezar(pa, 'Paso 6 · Participación por curso', FUENTE_PARTICIPACION)
        tabla(pa, ['Curso', 'Código', 'Convocados', 'Presentaron', '% participación'],
              [[x['nombre'], x['codigo'], x['convocados'], x['presentaron'], fr(x['porcentaje'])]
               for x in a['mapas']['participacion_curso']], [40, 14, 12, 12, 15], {5: PCT})

        ca = libro.create_sheet('Calidad de datos')
        encabezar(ca, 'Paso 6 · Calidad y suficiencia de los datos', FUENTE_CALIDAD)
        tabla(ca, ['Aspecto', 'Casos', 'Total', '%', 'Impacto en el análisis'],
              [[x['titulo'], x['valor'], x['total'], fr(x['porcentaje']), x['impacto']] for x in a['calidad_datos']],
              [50, 8, 8, 9, 80], {4: PCT})

    # ---- Desglose (HU-11.3)
    desglose = libro.create_sheet('Desglose')
    encabezar(desglose, 'Desglose de notas (0-5)', FUENTE_NOTAS)
    tabla(desglose, _encabezado_desglose(datos), _filas_desglose(datos), [12, 40, 12, 12, 10, 11, 14, 13])

    if a:
        # ---- Analítica RA: todas las secciones en una hoja (compatibilidad con HU-11.3/ADR-011)
        ra = libro.create_sheet('Analítica RA')
        for titulo_s, encabezado, filas in _secciones(datos):
            ra.append([titulo_s])
            ra.cell(row=ra.max_row, column=1).font = Font(bold=True, size=12)
            ra.append(encabezado)
            for celda in ra[ra.max_row]:
                celda.fill, celda.font = cab_fill, cab_font
            for fila in filas or [['Sin datos con los filtros aplicados.']]:
                ra.append(fila)
            ra.append([])
        ra.column_dimensions['A'].width = 60
        ra.column_dimensions['B'].width = 28

        # ---- Metodología y fichas técnicas
        me = libro.create_sheet('Metodología')
        encabezar(me, 'Paso 6 · Metodología, referentes e indicadores no disponibles')
        mp = a['metrica_provisional']
        lineas = [
            f"Un RA se considera logrado con un % de logro ≥ {mp['umbral_logro_porcentaje']} %.",
            'Las preguntas sin responder cuentan como no acertadas.' if mp['sin_responder_es_fallo']
            else 'Las preguntas sin responder no se cuentan.',
            'Se excluyen los intentos anulados por fraude. El logro se pondera por pregunta, no por estudiante.',
            TEXTO_ESCALA,
            mp['aviso'],
            '', 'Referentes:', *REFERENTES,
        ]
        for i, linea in enumerate(lineas, start=6):
            me.cell(row=i, column=1, value=linea)
        tabla(me, ['Indicador oficial no calculable', 'Referente', 'Dato que falta'],
              [[x['nombre'], x['referente'], x['falta']] for x in a['indicadores_no_disponibles']],
              [60, 30, 70], fila_inicio=6 + len(lineas) + 1, filtro=False)

        fi = libro.create_sheet('Fichas técnicas')
        encabezar(fi, 'Fichas técnicas de los indicadores')
        campos = [('nombre', 'Indicador'), ('nivel', 'Nivel'), ('tipo', 'Tipo'), ('provisional', 'Provisional'),
                  ('objetivo', 'Objetivo'), ('definicion', 'Definición'), ('formula', 'Fórmula'),
                  ('numerador', 'Numerador'), ('denominador', 'Denominador'), ('unidad', 'Unidad'),
                  ('periodicidad', 'Periodicidad'), ('desagregacion', 'Desagregación'), ('fuente', 'Fuente'),
                  ('interpretacion', 'Interpretación'), ('limitaciones', 'Limitaciones'), ('referente', 'Referente')]
        tabla(fi, [t for _k, t in campos],
              [[('Sí' if f[k] else 'No') if k == 'provisional' else f[k] for k, _t in campos] for f in _catalogo()],
              [28, 12, 18, 11, 40, 40, 34, 34, 34, 14, 22, 34, 40, 34, 40, 50])

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
