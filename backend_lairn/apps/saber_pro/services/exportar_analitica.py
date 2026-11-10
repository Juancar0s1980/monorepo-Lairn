"""
Exportación en Excel de la analítica Saber Pro (HU-24.5/24.6).

Convierte en un libro `.xlsx` exactamente los datos que ya calculó
`construir_analitica_curso` o `construir_analitica_institucional`: no
recalcula nada, solo los presenta con la identidad visual institucional.

- La exportación del docente incluye los resultados individuales de su curso.
- La exportación institucional es agregada y no expone datos personales.
- Ambas conservan los filtros aplicados y una hoja de metodología para que el
  archivo se interprete sin depender de la pantalla.
"""

import io

from django.utils import timezone

INSTITUCION = 'Corporación Universitaria Autónoma del Cauca'
SISTEMA = 'LAIRN'

AZUL = '1E3A5F'
GOLD = 'C89B14'
TEXTO = '2C3E50'
MUTED = '6B7A8D'
BEIGE_ALT = 'EDE6D8'
BORDE = 'D9D2C4'

AVISO_AGREGADO = (
    'Información agregada de uso institucional. No incluye datos personales '
    'de estudiantes (Ley 1581 de 2012).'
)
AVISO_DOCENTE = (
    'Incluye resultados individuales de los estudiantes del curso. Uso '
    'académico interno del docente propietario.'
)


def _fraccion(valor):
    """Porcentaje 0-100 -> fracción para el formato porcentual de Excel."""
    return None if valor is None else round(valor / 100, 4)


def _fecha(valor):
    if not valor:
        return ''
    try:
        return timezone.localtime(valor).strftime('%Y-%m-%d %H:%M')
    except (ValueError, OverflowError):
        return valor.strftime('%Y-%m-%d %H:%M')


def _nombre(referencia):
    return (referencia or {}).get('nombre') or 'Sin nombre'


def _filtros_texto(payload):
    """Filtros efectivamente aplicados, en el mismo orden de la pantalla."""
    filtro = payload.get('filtro') or {}
    partes = []

    if filtro.get('curso'):
        partes.append(f"Curso: {_nombre(filtro['curso'])}")
    if filtro.get('programa'):
        partes.append(f"Carrera: {_nombre(filtro['programa'])}")
    if filtro.get('area'):
        partes.append(f"Área: {_nombre(filtro['area'])}")
    if filtro.get('competencia'):
        partes.append(f"Competencia: {_nombre(filtro['competencia'])}")
    if filtro.get('afirmacion'):
        partes.append(f"Afirmación: {_nombre(filtro['afirmacion'])}")
    if filtro.get('parte'):
        partes.append(f"Parte: {_nombre(filtro['parte'])}")
    if filtro.get('simulacro'):
        partes.append(f"Simulacro: {filtro['simulacro']['titulo']}")
    partes.append(f"Periodo: {filtro.get('periodo') or 'todos los periodos'}")

    return ' · '.join(partes)


def _cabecera(hoja, subtitulo, payload, nota):
    """Cabecera institucional común; devuelve la fila donde inicia el contenido."""
    from openpyxl.styles import Font

    hoja['A1'] = INSTITUCION
    hoja['A1'].font = Font(bold=True, size=12, color=AZUL)
    hoja['A2'] = f'Saber Pro · {subtitulo}'
    hoja['A2'].font = Font(bold=True, size=14, color=TEXTO)
    hoja['A3'] = _filtros_texto(payload)
    hoja['A3'].font = Font(size=9, color=MUTED)
    hoja['A4'] = (
        f'Generado: {timezone.localtime():%Y-%m-%d %H:%M} · {SISTEMA}'
    )
    hoja['A4'].font = Font(size=9, color=MUTED)
    hoja['A5'] = nota
    hoja['A5'].font = Font(italic=True, size=9, color=GOLD)
    return 7


def _tabla(hoja, fila, encabezados, filas, anchos, formatos=None):
    """Escribe una tabla con encabezado azul; devuelve la fila siguiente libre."""
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    formatos = formatos or {}
    for columna, texto in enumerate(encabezados, start=1):
        celda = hoja.cell(row=fila, column=columna, value=texto)
        celda.fill = PatternFill('solid', fgColor=AZUL)
        celda.font = Font(bold=True, color='FFFFFF', size=10)
        celda.alignment = Alignment(wrap_text=True, vertical='center')

    for indice, valores in enumerate(filas, start=fila + 1):
        for columna, valor in enumerate(valores, start=1):
            celda = hoja.cell(row=indice, column=columna, value=valor)
            celda.alignment = Alignment(wrap_text=True, vertical='top')
            celda.border = Border(bottom=Side(style='thin', color=BORDE))
            if indice % 2 == 0:
                celda.fill = PatternFill('solid', fgColor=BEIGE_ALT)
            if columna in formatos and valor is not None:
                celda.number_format = formatos[columna]

    for columna, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(columna)].width = ancho

    if filas:
        ultima = fila + len(filas)
        hoja.auto_filter.ref = (
            f'A{fila}:{get_column_letter(len(encabezados))}{ultima}'
        )
        hoja.freeze_panes = f'A{fila + 1}'
    else:
        celda = hoja.cell(
            row=fila + 1,
            column=1,
            value='Sin datos con los filtros aplicados.',
        )
        celda.font = Font(italic=True, color=MUTED)

    return fila + max(len(filas), 1) + 2


def _seccion(hoja, fila, titulo, encabezados, filas, anchos, formatos=None):
    from openpyxl.styles import Font

    celda = hoja.cell(row=fila, column=1, value=titulo)
    celda.font = Font(bold=True, size=11, color=AZUL)
    return _tabla(hoja, fila + 1, encabezados, filas, anchos, formatos)


def _hoja_resumen(hoja, payload, subtitulo, nota):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    fila = _cabecera(hoja, subtitulo, payload, nota)
    resumen = payload['resumen']
    hoja.cell(row=fila, column=1, value='Indicadores generales').font = Font(
        bold=True, size=11, color=AZUL
    )
    fila += 1

    for columna, texto in enumerate(
        ['Indicador', 'Valor', 'Detalle'], start=1
    ):
        celda = hoja.cell(row=fila, column=columna, value=texto)
        celda.fill = PatternFill('solid', fgColor=AZUL)
        celda.font = Font(bold=True, color='FFFFFF', size=10)
        celda.alignment = Alignment(wrap_text=True, vertical='center')

    filas = [
        ('Estudiantes', resumen['total_estudiantes'], '0',
         'Personas distintas con intentos elegibles'),
        ('Intentos elegibles', resumen['total_intentos'], '0',
         'Finalizados y calificados'),
        ('Cursos', resumen['total_cursos'], '0',
         'Cursos representados en la consulta'),
        ('Carreras', resumen['total_programas'], '0',
         'Estudiantes con perfil académico'),
        ('Ítems evaluados', resumen['total_preguntas'], '0',
         'Incluye bloques no respondidos e intentos anulados'),
        ('Aciertos', resumen['aciertos'], '0',
         'Respuestas correctas de los intentos elegibles'),
        ('% de acierto', _fraccion(resumen['porcentaje_acierto']), '0.00%',
         'Aciertos sobre el total de ítems evaluados'),
        ('Promedio de puntaje', _fraccion(resumen['promedio_puntaje']), '0.00%',
         'Puntaje promedio de los intentos'),
        ('Promedio de calificación', resumen['promedio_calificacion'], '0.00',
         'Escala institucional 0.0-5.0'),
        ('Aprobados', resumen['aprobados'], '0',
         'Intentos con calificación mayor o igual a 3.0'),
        ('Tasa de aprobación', _fraccion(resumen['tasa_aprobacion']), '0.00%',
         'Aprobados sobre intentos elegibles'),
    ]

    for indice, (etiqueta, valor, formato, detalle) in enumerate(
        filas, start=fila + 1
    ):
        for columna, contenido in enumerate(
            (etiqueta, valor, detalle), start=1
        ):
            celda = hoja.cell(row=indice, column=columna, value=contenido)
            celda.alignment = Alignment(wrap_text=True, vertical='top')
            celda.border = Border(bottom=Side(style='thin', color=BORDE))
            if indice % 2 == 0:
                celda.fill = PatternFill('solid', fgColor=BEIGE_ALT)
        hoja.cell(row=indice, column=2).number_format = formato
        hoja.cell(row=indice, column=2).font = Font(bold=True, color=TEXTO)

    for columna, ancho in enumerate([38, 16, 58], start=1):
        hoja.column_dimensions[
            {1: 'A', 2: 'B', 3: 'C'}[columna]
        ].width = ancho


def _hoja_distribucion(libro, payload):
    hoja = libro.create_sheet('Distribución')
    fila = _cabecera(
        hoja,
        'Distribución de calificaciones',
        payload,
        'Rangos sobre la calificación 0.0-5.0 de los intentos elegibles.',
    )
    return _seccion(
        hoja,
        fila,
        'Calificaciones por rango',
        ['Rango', 'Cantidad', '% del total'],
        [
            [item['rango'], item['cantidad'], _fraccion(item['porcentaje'])]
            for item in payload['distribucion_calificaciones']
        ],
        [24, 14, 14],
        {3: '0.00%'},
    )


def _hoja_por_area(libro, payload):
    hoja = libro.create_sheet('Por área')
    fila = _cabecera(
        hoja,
        'Desempeño por área',
        payload,
        'Ordenado de menor a mayor porcentaje de acierto.',
    )
    return _seccion(
        hoja,
        fila,
        'Resultados por área',
        ['Área', 'Estudiantes', 'Aciertos', 'Ítems', '% de acierto'],
        [
            [
                _nombre(item['area']),
                item['total_estudiantes'],
                item['aciertos'],
                item['total_preguntas'],
                _fraccion(item['porcentaje_acierto']),
            ]
            for item in payload['por_area']
        ],
        [34, 14, 12, 12, 14],
        {5: '0.00%'},
    )


def _hoja_por_competencia(libro, payload):
    hoja = libro.create_sheet('Por competencia')
    fila = _cabecera(
        hoja,
        'Desempeño por competencia',
        payload,
        'Las áreas sin competencias (Inglés, Comunicación Escrita) no generan filas.',
    )
    return _seccion(
        hoja,
        fila,
        'Resultados por competencia',
        ['Competencia', 'Área', 'Estudiantes', 'Aciertos', 'Ítems', '% de acierto'],
        [
            [
                _nombre(item['competencia']),
                _nombre(item['area']),
                item['total_estudiantes'],
                item['aciertos'],
                item['total_preguntas'],
                _fraccion(item['porcentaje_acierto']),
            ]
            for item in payload['por_competencia']
        ],
        [38, 28, 14, 12, 12, 14],
        {6: '0.00%'},
    )


def _hoja_por_afirmacion(libro, payload):
    hoja = libro.create_sheet('Por afirmación')
    fila = _cabecera(
        hoja,
        'Desempeño por afirmación',
        payload,
        'Las áreas sin afirmaciones no generan filas.',
    )
    return _seccion(
        hoja,
        fila,
        'Resultados por afirmación',
        [
            'Afirmación',
            'Competencia',
            'Área',
            'Estudiantes',
            'Aciertos',
            'Ítems',
            '% de acierto',
        ],
        [
            [
                _nombre(item['afirmacion']),
                _nombre(item['competencia']),
                _nombre(item['area']),
                item['total_estudiantes'],
                item['aciertos'],
                item['total_preguntas'],
                _fraccion(item['porcentaje_acierto']),
            ]
            for item in payload['por_afirmacion']
        ],
        [40, 32, 26, 14, 12, 12, 14],
        {7: '0.00%'},
    )


def _hoja_por_parte(libro, payload):
    hoja = libro.create_sheet('Por parte')
    fila = _cabecera(
        hoja,
        'Desempeño por parte de Inglés',
        payload,
        'Cada parte del examen de Inglés se evalúa como bloque completo; las demás áreas no generan filas.',
    )
    return _seccion(
        hoja,
        fila,
        'Resultados por parte',
        ['Parte', 'Estudiantes', 'Aciertos', 'Ítems', '% de acierto'],
        [
            [
                _nombre(item['parte']),
                item['total_estudiantes'],
                item['aciertos'],
                item['total_preguntas'],
                _fraccion(item['porcentaje_acierto']),
            ]
            for item in payload['por_parte']
        ],
        [46, 14, 12, 12, 14],
        {5: '0.00%'},
    )


def _hoja_focos(libro, payload):
    hoja = libro.create_sheet('Focos de refuerzo')
    fila = _cabecera(
        hoja,
        'Focos de refuerzo',
        payload,
        'Criterios con menor porcentaje de acierto (máximo 5).',
    )
    return _seccion(
        hoja,
        fila,
        'Prioridades académicas',
        ['Tipo', 'Criterio', '% de acierto', 'Ítems'],
        [
            [
                item['tipo'].capitalize(),
                item['nombre'],
                _fraccion(item['porcentaje_acierto']),
                item['total_preguntas'],
            ]
            for item in payload['focos_bajos']
        ],
        [18, 52, 16, 12],
        {3: '0.00%'},
    )


def _hoja_individuales(libro, payload):
    hoja = libro.create_sheet('Resultados individuales')
    fila = _cabecera(
        hoja,
        'Resultados individuales del curso',
        payload,
        AVISO_DOCENTE,
    )
    return _seccion(
        hoja,
        fila,
        'Intentos elegibles',
        [
            'Estudiante',
            'Correo',
            'Simulacro',
            'Intento',
            'Puntaje',
            'Calificación',
            'Aciertos',
            'Ítems',
            '% de acierto',
            'Estado',
            'Finalizada en',
        ],
        [
            [
                item['estudiante']['nombre_completo'] or 'Estudiante sin nombre',
                item['estudiante']['email'],
                item['simulacro']['titulo'] if item['simulacro'] else '',
                item['intento'],
                _fraccion(item['puntaje']),
                item['calificacion'],
                item['aciertos'],
                item['total_evaluables'],
                _fraccion(item['porcentaje_acierto']),
                'Anulada' if item['anulada'] else (
                    'Aprobado' if item['aprobado'] else 'Reprobado'
                ),
                _fecha(item['finalizada_en']),
            ]
            for item in payload['resultados_individuales']
        ],
        [28, 30, 26, 9, 12, 12, 10, 10, 13, 12, 17],
        {5: '0.00%', 6: '0.00', 9: '0.00%'},
    )


def _hoja_comparativa(libro, titulo_hoja, titulo, payload, clave_datos,
                      campo_referencia, etiqueta, etiquetas_columnas):
    hoja = libro.create_sheet(titulo_hoja)
    fila = _cabecera(
        hoja,
        titulo,
        payload,
        'Comparativa agregada de la institución; no incluye datos personales.',
    )

    filas = []
    for item in payload[clave_datos]:
        if campo_referencia == 'periodo':
            nombre = item['periodo']
        else:
            nombre = _nombre(item[campo_referencia])
        filas.append([
            nombre,
            item['total_estudiantes'],
            item['total_intentos'],
            _fraccion(item['promedio_puntaje']),
            item['promedio_calificacion'],
            _fraccion(item['porcentaje_acierto']),
            item['aprobados'],
            _fraccion(item['tasa_aprobacion']),
        ])

    return _seccion(
        hoja,
        fila,
        etiqueta,
        etiquetas_columnas,
        filas,
        [30, 14, 12, 16, 18, 14, 12, 16],
        {4: '0.00%', 5: '0.00', 6: '0.00%', 8: '0.00%'},
    )


def _hoja_metodologia(libro, nota):
    from openpyxl.styles import Alignment, Font

    hoja = libro.create_sheet('Metodología')
    hoja['A1'] = f'{INSTITUCION} · Saber Pro'
    hoja['A1'].font = Font(bold=True, size=12, color=AZUL)
    hoja['A2'] = 'Cómo leer este archivo'
    hoja['A2'].font = Font(bold=True, size=14, color=TEXTO)
    hoja['A3'] = nota
    hoja['A3'].font = Font(italic=True, size=9, color=GOLD)

    lineas = [
        'Solo se consideran intentos finalizados y calificados. Un intento con '
        'consignas abiertas pendientes no contamina los promedios.',
        'Los intentos anulados cuentan 0 aciertos, pero conservan sus ítems en '
        'el denominador.',
        'Los bloques no respondidos también cuentan en el denominador, igual '
        'que en el puntaje del intento.',
        'El periodo académico se deriva de la fecha de finalización: AAAA-1 '
        '(enero-junio) o AAAA-2 (julio-diciembre).',
        'Los desgloses por competencia y afirmación usan los criterios del '
        'contenido; Inglés y Comunicación Escrita no tienen esos criterios.',
        'En Inglés el desglose y el filtro propios son las 7 partes del examen; '
        'cada parte se evalúa como bloque completo.',
        'Los filtros de competencia y afirmación refinan los desgloses; el '
        'resumen conserva el alcance del curso, carrera, área y periodo.',
        'El filtro por parte de Inglés también refina solo el desglose por '
        'parte y los focos de refuerzo.',
        'Los desgloses se ordenan de menor a mayor porcentaje de acierto.',
        'Los focos de refuerzo muestran hasta cinco criterios con menor '
        'porcentaje de acierto.',
    ]
    fila = 5
    for linea in lineas:
        celda = hoja.cell(row=fila, column=1, value=f'• {linea}')
        celda.alignment = Alignment(wrap_text=True, vertical='top')
        fila += 1

    hoja.column_dimensions['A'].width = 110
    return fila


def _guardar(libro):
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def a_excel_analitica_curso(payload):
    """Libro Excel de la analítica de un curso, con resultados individuales."""
    from openpyxl import Workbook

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Resumen'
    _hoja_resumen(
        hoja,
        payload,
        f"Analítica del curso {payload['curso']['nombre']}",
        AVISO_DOCENTE,
    )
    _hoja_distribucion(libro, payload)
    _hoja_por_area(libro, payload)
    _hoja_por_competencia(libro, payload)
    _hoja_por_afirmacion(libro, payload)
    _hoja_por_parte(libro, payload)
    _hoja_focos(libro, payload)
    _hoja_individuales(libro, payload)
    _hoja_metodologia(libro, AVISO_DOCENTE)
    return _guardar(libro)


def a_excel_analitica_institucional(payload):
    """Libro Excel de la analítica institucional, solo con datos agregados."""
    from openpyxl import Workbook

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Resumen'
    _hoja_resumen(
        hoja,
        payload,
        'Analítica académica institucional',
        AVISO_AGREGADO,
    )
    _hoja_distribucion(libro, payload)
    _hoja_por_area(libro, payload)
    _hoja_por_competencia(libro, payload)
    _hoja_por_afirmacion(libro, payload)
    _hoja_por_parte(libro, payload)
    _hoja_focos(libro, payload)
    _hoja_comparativa(
        libro,
        'Por curso',
        'Comparativa por curso',
        payload,
        'por_curso',
        'curso',
        'Cursos',
        [
            'Curso',
            'Estudiantes',
            'Intentos',
            'Promedio de puntaje',
            'Promedio de calificación',
            '% de acierto',
            'Aprobados',
            'Tasa de aprobación',
        ],
    )
    _hoja_comparativa(
        libro,
        'Por carrera',
        'Comparativa por carrera',
        payload,
        'por_programa',
        'programa',
        'Carreras',
        [
            'Carrera',
            'Estudiantes',
            'Intentos',
            'Promedio de puntaje',
            'Promedio de calificación',
            '% de acierto',
            'Aprobados',
            'Tasa de aprobación',
        ],
    )
    _hoja_comparativa(
        libro,
        'Por periodo',
        'Comparativa por periodo académico',
        payload,
        'por_periodo',
        'periodo',
        'Periodos',
        [
            'Periodo',
            'Estudiantes',
            'Intentos',
            'Promedio de puntaje',
            'Promedio de calificación',
            '% de acierto',
            'Aprobados',
            'Tasa de aprobación',
        ],
    )
    _hoja_metodologia(libro, AVISO_AGREGADO)
    return _guardar(libro)
