"""
Pruebas del catálogo de indicadores y de la capa interpretativa (ADR-015).
Escenario de la analítica: RA1 66,7 % (n=3), RA2 50 % (n=2), RA3 obligatorio
sin evaluar en M1; M1 (E1) 75 % → M2 (E2) 0 %; 3 estudiantes.
"""

from apps.evaluacion_resultados.models import ProgramaAcademico
from apps.evaluacion_resultados.tests.test_analitica_ra import URL, BaseAnalitica, _usuario

CAMPOS_FICHA = {'id', 'nombre', 'objetivo', 'definicion', 'formula', 'numerador', 'denominador', 'unidad',
                'periodicidad', 'desagregacion', 'fuente', 'interpretacion', 'limitaciones', 'nivel', 'tipo',
                'referente', 'provisional'}


class PruebasCatalogo(BaseAnalitica):
    def test_fichas_completas_y_no_oficiales(self):
        r = self.cliente.get(URL + 'indicadores/')
        self.assertEqual(r.status_code, 200)
        for ficha in r.data['indicadores']:
            with self.subTest(ficha=ficha['id']):
                self.assertTrue(CAMPOS_FICHA <= set(ficha))
                self.assertEqual(ficha['tipo'], 'Institucional propio')
                self.assertIn(ficha['nivel'], {'operativo', 'estrategico', 'rendicion'})
        self.assertIn('60 %', next(f for f in r.data['indicadores'] if f['id'] == 'logro_general')['interpretacion'])
        no_disp = {x['referente'] for x in r.data['no_disponibles']}
        self.assertIn('SPADIES (MEN)', no_disp)


class PruebasHallazgos(BaseAnalitica):
    def test_hallazgos_con_evidencia_y_filtro(self):
        a = self.datos()
        titulos = [h['titulo'] for h in a['hallazgos']]
        ra2 = next(h for h in a['hallazgos'] if h['titulo'] == 'RA por debajo del umbral: 50.0 %')
        self.assertEqual((ra2['tipo'], ra2['evidencia']['n'], ra2['filtro']), ('atencion', 2, {'resultado': self.ra2.id}))
        self.assertTrue(any('M1: 1 RA obligatorio(s) sin evaluar' == t for t in titulos))
        self.assertTrue(any(t.startswith('Muestra pequeña') for t in titulos))
        descenso = next(h for h in a['hallazgos'] if h['titulo'].startswith('Descenso'))
        self.assertEqual(descenso['evidencia']['valor'], -75.0)
        self.assertIn('RA comparables', descenso['detalle'])
        self.assertEqual(a['hallazgos'], sorted(a['hallazgos'], key=lambda h: h['prioridad']))

    def test_conclusiones_y_limitaciones(self):
        c = self.datos()['conclusiones']
        self.assertIn('Se analizaron 5 respuestas de 2 estudiante(s)', c['puntos'][0])
        self.assertIn('Cobertura de RA obligatorios: 2 de 3', ' '.join(c['puntos']))
        self.assertIn('Conclusiones descriptivas: no establecen causas.', c['limitaciones'])
        self.assertTrue(any('no son indicadores oficiales del MEN' in x for x in c['limitaciones']))

    def test_comparacion_y_calidad(self):
        a = self.datos()
        comp = a['comparacion']
        self.assertEqual({s['nombre']: s['porcentaje'] for s in comp['por_semestre']}, {'Semestre 1': 66.7, 'Semestre 2': 50.0})
        self.assertEqual([v['variacion_pp'] for v in comp['variaciones']], [-75.0])
        calidad = {c['clave']: (c['valor'], c['total']) for c in a['calidad_datos']}
        self.assertEqual(calidad['asignaturas_sin_curso'], (1, 2))
        self.assertEqual(calidad['estudiantes_sin_perfil'], (3, 3))

    def test_sin_resultados(self):
        otro = ProgramaAcademico.objects.create(codigo='P9', nombre='Vacío')
        a = self.datos(programa=otro.id)
        self.assertEqual(a['hallazgos'][0]['titulo'], 'No hay resultados con estos filtros')
        self.assertEqual(a['conclusiones']['limitaciones'], [])

    def test_coordinador_lee_y_docente_no(self):
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))
        self.assertEqual(self.cliente.get(URL).status_code, 200)
        self.assertEqual(self.cliente.get(URL + 'indicadores/').status_code, 200)
        self.assertEqual(self.cliente.post(URL, {}).status_code, 403)  # solo lectura
        self.cliente.force_authenticate(_usuario('doc2@t.co', 'Docente'))
        self.assertEqual(self.cliente.get(URL + 'indicadores/').status_code, 403)
