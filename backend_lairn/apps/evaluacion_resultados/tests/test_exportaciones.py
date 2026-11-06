"""
Pruebas de las exportaciones profesionales del informe (ADR-016).
Mismo escenario que la analítica (ver test_analitica_ra / test_hallazgos).
"""

from io import BytesIO

from apps.evaluacion_resultados.tests.test_analitica_ra import URL, BaseAnalitica, _usuario

HOJAS = ['Resumen', 'Indicadores', 'Hallazgos', 'Logro por RA', 'Competencias', 'Preguntas', 'Comparación',
         'Evolución', 'Niveles', 'Cobertura', 'Participación', 'Calidad de datos', 'Desglose', 'Analítica RA',
         'Metodología', 'Fichas técnicas']


class PruebasExportaciones(BaseAnalitica):
    def _libro(self, **params):
        from openpyxl import load_workbook

        r = self.cliente.get(URL + 'exportar/', {'formato': 'xlsx', **params})
        self.assertEqual(r.status_code, 200)
        return load_workbook(BytesIO(r.content))

    def _pdf_texto(self, **params):
        from pypdf import PdfReader

        r = self.cliente.get(URL + 'exportar/', {'formato': 'pdf', **params})
        self.assertEqual(r.status_code, 200)
        lector = PdfReader(BytesIO(r.content))
        return lector, '\n'.join(p.extract_text() for p in lector.pages)

    def test_excel_secuencia_formatos_y_mismas_cifras(self):
        libro = self._libro()
        self.assertEqual(libro.sheetnames, HOJAS)
        a = self.datos()
        # Hallazgos: una fila por hallazgo, encabezado fijo y autofiltro.
        h = libro['Hallazgos']
        self.assertEqual(h.freeze_panes, 'A7')
        self.assertTrue(h.auto_filter.ref.startswith('A6:'))
        self.assertEqual(h.max_row - 6, len(a['hallazgos']))
        self.assertEqual(h['C7'].value, a['hallazgos'][0]['titulo'])
        # Logro por RA: porcentaje numérico con formato %, igual al de la pantalla.
        r = libro['Logro por RA']
        fila = {r.cell(row=i, column=1).value: r.cell(row=i, column=6) for i in range(7, r.max_row + 1)}
        ra2 = next(x for x in a['logro_ra'] if x['id'] == self.ra2.id)
        self.assertAlmostEqual(fila[ra2['descripcion']].value, ra2['porcentaje'] / 100, places=4)
        self.assertEqual(fila[ra2['descripcion']].number_format, '0.0%')
        self.assertEqual(len(r._charts), 1)
        # Evolución con gráfico (hay 2 momentos) y fichas completas.
        self.assertEqual(len(libro['Evolución']._charts), 1)
        self.assertEqual(libro['Fichas técnicas'].max_row - 6, len(self.cliente.get(URL + 'indicadores/').data['indicadores']))
        # Encabezado institucional y aviso de datos personales.
        self.assertIn('Autónoma del Cauca', libro['Resumen']['A1'].value)
        self.assertIn('Ley 1581', libro['Resumen']['A4'].value)

    def test_excel_respeta_filtros(self):
        libro = self._libro(competencia=self.ctra.id)
        r = libro['Logro por RA']
        ras = [r.cell(row=i, column=1).value for i in range(7, r.max_row + 1)]
        self.assertEqual(ras, ['RA2'])
        self.assertIn('Competencia', libro['Resumen']['A3'].value)

    def test_pdf_en_seis_pasos_con_paginacion(self):
        lector, texto = self._pdf_texto()
        total = len(lector.pages)
        self.assertGreater(total, 3)
        for i, paso in enumerate(['PANORAMA', 'HALLAZGOS', 'PROFUNDIZAR', 'COMPARAR', 'CONCLUSIONES',
                                  'EVIDENCIA Y METODOLOGÍA'], start=1):
            self.assertIn(f'PASO {i} DE 6 · {paso}', texto)
        self.assertIn(f'Página {total} de {total}', texto)
        self.assertIn('RA por debajo del umbral: 50.0 %', texto)
        self.assertIn('Fichas técnicas de los indicadores', texto)
        self.assertIn('no establecen causas', texto)
        self.assertIn('Ley 1581', texto)

    def test_pdf_sin_resultados(self):
        from apps.evaluacion_resultados.models import ProgramaAcademico

        vacio = ProgramaAcademico.objects.create(codigo='P9', nombre='Vacío')
        _lector, texto = self._pdf_texto(programa=vacio.id)
        self.assertIn('Sin datos con los filtros aplicados.', texto)

    def test_permisos(self):
        self.cliente.force_authenticate(_usuario('coord-exp@x.co', 'Coordinador'))
        self.assertEqual(self.cliente.get(URL + 'exportar/', {'formato': 'pdf'}).status_code, 200)
        for rol in ('Docente', 'Estudiante'):
            self.cliente.force_authenticate(_usuario(f'{rol}-exp@x.co', rol))
            self.assertEqual(self.cliente.get(URL + 'exportar/', {'formato': 'xlsx'}).status_code, 403)
