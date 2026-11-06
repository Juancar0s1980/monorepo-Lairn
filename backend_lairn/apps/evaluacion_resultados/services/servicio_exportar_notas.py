"""
Excel de notas del momento (ADR-019). Mismos datos que la pantalla (`notas_del_momento`).

Hojas: Resultados individuales · Resumen estadístico · Detalle del examen · Metodología · Convenciones.
Celdas sin calificación quedan VACÍAS (nunca 0) y su estado explica por qué.
"""

import io

from django.utils import timezone

from .escala_institucional import ETIQUETA_NIVEL, rangos

RANGO = {c: f'{mn}-{mx}'.replace('.', ',') for c, _e, mn, mx in rangos()}
from .servicio_exportar_reporte import INSTITUCION, TEXTO_ESCALA

AVISO = ('Contiene datos personales de estudiantes: uso institucional exclusivo (Ley 1581 de 2012). '
         'No reenviar ni publicar.')


def a_excel(datos, usuario=None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    m, esq, res = datos['momento'], datos['esquema'], datos['resumen']
    corte = timezone.localtime(datos['generado_en'])
    azul = PatternFill('solid', fgColor='1F4E8C')
    gris = PatternFill('solid', fgColor='EEF2F7')
    blanco = Font(bold=True, color='FFFFFF')
    linea = Border(bottom=Side(style='thin', color='D9DEE7'))
    libro = Workbook()

    def encabezar(hoja, titulo):
        hoja['A1'] = INSTITUCION
        hoja['A1'].font = Font(bold=True, size=12, color='1F4E8C')
        hoja['A2'] = f"Notas del momento — {m['nombre']} · {titulo}"
        hoja['A2'].font = Font(bold=True, size=13)
        hoja['A3'] = (f"Programa {m['programa']} · periodo {m['periodo'] or 'sin periodo'} · corte "
                      f"{corte:%Y-%m-%d %H:%M} (hora de Colombia)"
                      + (' · PROVISIONAL: hay evaluaciones abiertas o pendientes' if datos['provisional'] else ''))
        hoja['A4'] = AVISO
        hoja['A3'].font = Font(size=9, color='52514E', bold=datos['provisional'])
        hoja['A4'].font = Font(size=9, italic=True, color='9A3412')

    def tabla(hoja, encabezados, filas, anchos, fila=6, formatos=None, filtro=True):
        formatos = formatos or {}
        for j, texto in enumerate(encabezados, start=1):
            c = hoja.cell(row=fila, column=j, value=texto)
            c.fill, c.font = azul, blanco
            c.alignment = Alignment(wrap_text=True, vertical='center')
        for i, valores in enumerate(filas, start=fila + 1):
            for j, valor in enumerate(valores, start=1):
                c = hoja.cell(row=i, column=j, value=valor)
                c.border = linea
                c.alignment = Alignment(vertical='top', wrap_text=isinstance(valor, str) and len(valor) > 30)
                if j in formatos and isinstance(valor, (int, float)):
                    c.number_format = formatos[j]
        for j, ancho in enumerate(anchos, start=1):
            hoja.column_dimensions[get_column_letter(j)].width = ancho
        ultima = fila + len(filas)
        if filtro:
            hoja.freeze_panes = f'C{fila + 1}' if len(encabezados) > 6 else f'A{fila + 1}'
            if filas:
                hoja.auto_filter.ref = f'A{fila}:{get_column_letter(len(encabezados))}{ultima}'
        hoja.row_dimensions[fila].height = 42
        return ultima

    nivel_txt = lambda c: ETIQUETA_NIVEL.get(c) if c else None  # noqa: E731
    si_no = lambda v: None if v is None else ('Sí' if v else 'No')  # noqa: E731

    # ---- Hoja 1: resultados individuales
    h = libro.active
    h.title = 'Resultados individuales'
    encabezar(h, 'Resultados individuales')
    cab = ['Código', 'Estudiante', 'Correo',
           'Examen: nota', 'Correctas', 'Incorrectas', 'Sin responder', 'Total preguntas', '% aciertos',
           'Desempeño examen', 'Estado examen']
    if datos['tiene_trabajo']:
        cab += ['Trabajo: nota', 'Desempeño trabajo', 'Estado trabajo']
    cab += ['Consolidado del momento', 'Desempeño del momento', 'Aprueba (≥ 3,0)', 'Estado del consolidado',
            'Nota reglamentaria a reportar', 'Aporte al tercer corte', 'Aporte a la definitiva']
    filas = []
    for f in datos['filas']:
        ex, tr, mo = f['examen'], f['trabajo'], f['momento']
        v = [f['codigo'] or None, f['nombre'], f['correo'],
             ex['nota'], ex['correctas'], ex['incorrectas'], ex['sin_responder'], ex['total'],
             None if ex['porcentaje'] is None else ex['porcentaje'] / 100, nivel_txt(ex['nivel']), ex['estado_texto']]
        if datos['tiene_trabajo']:
            v += [tr['nota'], nivel_txt(tr['nivel']), tr['estado_texto']]
        v += [mo['nota'], nivel_txt(mo['nivel']), si_no(mo['aprueba']), mo['estado_texto'],
              mo['nota_reglamentaria'], mo['aporte_tercer_corte'], mo['aporte_definitiva']]
        filas.append(v)
    n = len(cab)
    formatos = {4: '0.0', 9: '0.0%', n - 6: '0.0', n - 2: '0.0', n - 1: '0.00', n: '0.00'}
    if datos['tiene_trabajo']:
        formatos[12] = '0.0'
    anchos = [12, 30, 30, 11, 10, 11, 11, 11, 10, 15, 30] + ([11, 15, 30] if datos['tiene_trabajo'] else []) \
        + [13, 15, 11, 30, 14, 12, 12]
    ultima = tabla(h, cab, filas, anchos, formatos=formatos)
    if not filas:
        h.cell(row=7, column=1, value='No hay estudiantes convocados a las evaluaciones publicadas de este momento.')
    h.cell(row=ultima + 2, column=1, value=(
        'Celdas vacías = sin calificación (ver la columna de estado). La "nota reglamentaria a reportar" aplica 0,0 '
        'solo a lo no presentado sin excusa (Acuerdo 005 de 2025). Los aportes NO son la nota del tercer corte.'
    )).font = Font(size=9, italic=True)

    # ---- Hoja 2: resumen estadístico
    r = libro.create_sheet('Resumen estadístico')
    encabezar(r, 'Resumen estadístico')
    e, mo = res['examen'], res['momento']
    pct = lambda v: None if v is None else v / 100  # noqa: E731
    filas_r = [
        ['Convocados', res['convocados'], '', 'Estudiantes convocados a alguna evaluación publicada del momento'],
        ['Presentaron el examen', e['presentaron'], pct(e['pct_presentaron']), f"Sobre {e['convocados']} convocados al examen"],
        ['Ausentes o no presentaron', e['ausentes'], pct(e['pct_ausentes']), 'Sin intento; sin excusa'],
        ['Con excusa (supletorio pendiente)', e['con_excusa'], '', 'No entran en promedios'],
        ['Anulados por fraude', e['anulados'], '', 'No entran en promedios'],
        ['Presentaron parcialmente', e['incompletos'], '', 'No entran en promedios del examen'],
        ['En curso, suspendidos o pendientes', e['en_curso_o_pendientes'], '', 'Aún sin calificación'],
        ['Promedio del examen', e['promedio'], '', 'Solo estudiantes con nota de examen'],
        ['Promedio del trabajo', res['trabajo']['promedio'], '', 'Solo trabajos calificados'],
        ['Estudiantes con nota del momento', mo['con_nota'], '', 'Base de los indicadores siguientes'],
        ['Promedio del momento', mo['promedio'], '', f"Meta institucional ≥ {mo['meta_promedio']}"],
        ['Aprobados (≥ 3,0)', mo['aprobados'], pct(mo['pct_aprobacion']), f"Meta institucional ≥ {mo['meta_aprobacion']} %"],
    ]
    u = tabla(r, ['Indicador', 'Cantidad / valor', '%', 'Base de cálculo'], filas_r, [36, 16, 10, 60], filtro=False,
              formatos={2: '0.00', 3: '0.0%'})
    for fila in range(7, u + 1):
        if isinstance(r.cell(row=fila, column=2).value, int):
            r.cell(row=fila, column=2).number_format = '0'
    u2 = tabla(r, ['Nivel de desempeño (momento)', 'Cantidad', '%', 'Rango'],
               [[nv['etiqueta'], nv['cantidad'], pct(nv['porcentaje']),
                 RANGO[nv['clave']]]
                for nv in mo['niveles']], [36, 16, 10, 60], fila=u + 3, filtro=False, formatos={3: '0.0%'})
    for fila in range(7, u2 + 1):
        r.cell(row=fila, column=1).fill = gris if fila % 2 else PatternFill()

    # ---- Hoja 3: detalle del examen
    d = libro.create_sheet('Detalle del examen')
    encabezar(d, 'Detalle por cuestionario')
    tabla(d, ['Estudiante', 'Correo', 'Cuestionario', 'Estado', 'Correctas', 'Incorrectas', 'Sin responder',
              'Total', 'Nota sin redondear', 'Enviado', 'Envío automático'],
          [[x['estudiante'], x['correo'], x['evaluacion'], x['estado'], x['correctas'], x['incorrectas'],
            x['sin_responder'], x['total'], x['nota_sin_redondear'],
            timezone.localtime(x['enviado_en']).strftime('%Y-%m-%d %H:%M') if x['enviado_en'] else None,
            'Sí' if x['envio_automatico'] else 'No']
           for x in datos['detalle']], [30, 30, 34, 26, 10, 11, 11, 9, 12, 17, 12], formatos={9: '0.00'})

    # ---- Hoja 4: metodología
    me = libro.create_sheet('Metodología')
    encabezar(me, 'Metodología')
    pe, pt = esq.get('peso_examen'), esq.get('peso_trabajo')
    lineas = [
        ('Examen', 'Todos los cuestionarios publicados del momento son partes de un mismo examen. '
                   'Nota = 5 × correctas / total de preguntas (las sin responder cuentan como no acertadas). '
                   'Correctas, incorrectas y sin responder se cuentan desde las respuestas guardadas.'),
        ('Trabajo', 'Evaluaciones tipo tarea del momento (opcional). Nota por rúbrica; si hay varias, promedio simple.'),
        ('Consolidado del momento', 'Sin trabajo: igual al examen. Con trabajo: '
         + (f'{pe} % examen + {pt} % trabajo (origen: {esq.get("origen_peso_examen")}).' if pe is not None and pt is not None
            else 'ponderación examen/trabajo SIN DEFINIR: el consolidado queda pendiente.')),
        ('Redondeo', 'Un decimal, una sola vez al final; centésima ≥ 5 por exceso (Acuerdo 005 de 2025, Art. 45).'),
        ('Escala', TEXTO_ESCALA),
        ('Aprobación', 'Nota ≥ 3,0 (Acuerdo 005 de 2025, Art. 46).'),
        ('Aporte al tercer corte', f"Consolidado × {esq.get('peso_momento_en_corte')} % "
                                   f"({datos['fuentes']['peso_momento']}). No es la nota del tercer corte: "
                                   'las demás actividades las define el profesor y no están en la plataforma.'),
        ('Aporte a la definitiva', f"Aporte al tercer corte × {esq.get('peso_corte_en_definitiva')} % "
                                   f"({datos['fuentes']['peso_corte']})."),
        ('Sin calificación', 'Ausente, no presentó, con excusa, anulado, suspendido o pendiente: la nota queda vacía y '
                             'no entra en ningún promedio ni indicador.'),
        ('Nota reglamentaria', 'Columna aparte: aplica 0,0 solo a lo no presentado sin excusa (Acuerdo 005 de 2025). '
                               'Con excusa, anulación o pendientes, no se determina.'),
        ('Indicadores', 'Promedio y % de aprobación solo sobre estudiantes con nota del momento. '
                        'Metas: ≥ 70 % de aprobación y promedio ≥ 3,0 (Res. 0238/2024 según la propuesta, por verificar).'),
        ('Exportado por', f"{getattr(usuario, 'email', '')} el {timezone.localtime():%Y-%m-%d %H:%M}"),
    ]
    tabla(me, ['Concepto', 'Regla aplicada'], [list(x) for x in lineas], [26, 120], filtro=False)

    # ---- Hoja 5: convenciones
    cv = libro.create_sheet('Convenciones')
    encabezar(cv, 'Convenciones de estados')
    from .servicio_notas_momento import ESTADOS_CONSOLIDADO, ESTADOS_EXAMEN, ESTADOS_TRABAJO
    filas_c = [['Examen', v] for v in ESTADOS_EXAMEN.values()] + [['Trabajo', v] for v in ESTADOS_TRABAJO.values()] \
        + [['Consolidado', v] for v in ESTADOS_CONSOLIDADO.values()]
    tabla(cv, ['Componente', 'Estado'], filas_c, [16, 60], filtro=False)

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
