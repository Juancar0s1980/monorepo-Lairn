"""
Tests de validación y de los tres renderers SVG de
`services/agente_problema_visual.py`. Sin mock: son funciones puras, no
llaman a ninguna IA — mismo criterio que `test_agente_pronunciacion.py` y
`test_vista_responder.py` (`_validar_pregunta`).
"""

from django.test import SimpleTestCase

from apps.laboratorios.services.agente_problema_visual import (
    _generar_svg_circuito,
    _generar_svg_fluidos_compuerta,
    _generar_svg_ruta,
    _validar_texto_variantes,
    _validar_variante_circuito,
    _validar_variante_fluidos,
    _validar_variante_ruta,
)


def _variante_ruta(**overrides) -> dict:
    base = {
        'puntos': ['A', 'B', 'C'],
        'segmentos': [
            {'longitud': '120 m', 'giro_grados': 0},
            {'longitud': '80 m', 'giro_grados': 45},
        ],
        'opciones': ['10', '20', '30', '40'],
        'respuesta_correcta': 1,
    }
    base.update(overrides)
    return base


def _variante_circuito(**overrides) -> dict:
    base = {
        'elementos': [
            {'tipo': 'bateria', 'etiqueta': '12 V'},
            {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
            {'tipo': 'resistencia', 'etiqueta': 'R2 = 220 Ω'},
        ],
        'opciones': ['0.1 A', '0.2 A', '0.3 A', '0.4 A'],
        'respuesta_correcta': 0,
    }
    base.update(overrides)
    return base


def _variante_fluidos(**overrides) -> dict:
    base = {
        'nivel_agua': 'H = 5 m',
        'profundidad_compuerta': 'h = 1.5 m',
        'dato_compuerta': 'A = 0.3 m²',
        'opciones': ['1 m/s', '2 m/s', '3 m/s', '4 m/s'],
        'respuesta_correcta': 2,
    }
    base.update(overrides)
    return base


class ValidarVarianteRutaTests(SimpleTestCase):
    def test_variante_valida_no_lanza_error(self):
        _validar_variante_ruta(_variante_ruta())  # no debe lanzar

    def test_menos_de_3_puntos_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_ruta(_variante_ruta(puntos=['A', 'B']))

    def test_segmentos_no_coincide_con_puntos_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_ruta(_variante_ruta(segmentos=[{'longitud': '1 m', 'giro_grados': 0}]))

    def test_segmento_sin_giro_grados_numerico_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_ruta(_variante_ruta(segmentos=[
                {'longitud': '120 m', 'giro_grados': 'recto'},
                {'longitud': '80 m', 'giro_grados': 45},
            ]))


class ValidarVarianteCircuitoTests(SimpleTestCase):
    def test_variante_valida_no_lanza_error(self):
        _validar_variante_circuito(_variante_circuito())  # no debe lanzar

    def test_sin_bateria_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_circuito(_variante_circuito(elementos=[
                {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
                {'tipo': 'resistencia', 'etiqueta': 'R2 = 220 Ω'},
                {'tipo': 'capacitor', 'etiqueta': '10 µF'},
            ]))

    def test_dos_baterias_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_circuito(_variante_circuito(elementos=[
                {'tipo': 'bateria', 'etiqueta': '12 V'},
                {'tipo': 'bateria', 'etiqueta': '9 V'},
                {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
            ]))

    def test_tipo_de_elemento_desconocido_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_circuito(_variante_circuito(elementos=[
                {'tipo': 'bateria', 'etiqueta': '12 V'},
                {'tipo': 'bobina', 'etiqueta': 'L1'},
                {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
            ]))

    def test_menos_de_3_elementos_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_circuito(_variante_circuito(elementos=[
                {'tipo': 'bateria', 'etiqueta': '12 V'},
                {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
            ]))


class ValidarVarianteFluidosTests(SimpleTestCase):
    def test_variante_valida_no_lanza_error(self):
        _validar_variante_fluidos(_variante_fluidos())  # no debe lanzar

    def test_falta_nivel_agua_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_fluidos(_variante_fluidos(nivel_agua=''))

    def test_falta_profundidad_compuerta_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_variante_fluidos(_variante_fluidos(profundidad_compuerta='   '))

    def test_falta_dato_compuerta_lanza_error(self):
        datos = _variante_fluidos()
        del datos['dato_compuerta']
        with self.assertRaises(ValueError):
            _validar_variante_fluidos(datos)


class ValidarTextoVariantesTests(SimpleTestCase):
    def test_despacha_a_validador_de_ruta(self):
        datos = {'tipo_diagrama': 'ruta', 'enunciado': 'x', 'variantes': [_variante_ruta()]}
        _validar_texto_variantes(datos, cantidad=1)  # no debe lanzar

    def test_despacha_a_validador_de_circuito(self):
        datos = {'tipo_diagrama': 'circuito', 'enunciado': 'x', 'variantes': [_variante_circuito()]}
        _validar_texto_variantes(datos, cantidad=1)  # no debe lanzar

    def test_despacha_a_validador_de_fluidos(self):
        datos = {'tipo_diagrama': 'fluidos_compuerta', 'enunciado': 'x', 'variantes': [_variante_fluidos()]}
        _validar_texto_variantes(datos, cantidad=1)  # no debe lanzar

    def test_tipo_diagrama_desconocido_lanza_error(self):
        datos = {'tipo_diagrama': 'mapa_mental', 'enunciado': 'x', 'variantes': [_variante_ruta()]}
        with self.assertRaises(ValueError):
            _validar_texto_variantes(datos, cantidad=1)

    def test_cantidad_de_variantes_no_coincide_lanza_error(self):
        datos = {'tipo_diagrama': 'ruta', 'enunciado': 'x', 'variantes': [_variante_ruta()]}
        with self.assertRaises(ValueError):
            _validar_texto_variantes(datos, cantidad=2)

    def test_opciones_repetidas_lanza_error(self):
        datos = {
            'tipo_diagrama': 'ruta', 'enunciado': 'x',
            'variantes': [_variante_ruta(opciones=['10', '10', '20', '30'])],
        }
        with self.assertRaises(ValueError):
            _validar_texto_variantes(datos, cantidad=1)

    def test_respuesta_correcta_fuera_de_rango_lanza_error(self):
        datos = {'tipo_diagrama': 'ruta', 'enunciado': 'x', 'variantes': [_variante_ruta(respuesta_correcta=4)]}
        with self.assertRaises(ValueError):
            _validar_texto_variantes(datos, cantidad=1)


class GenerarSvgRutaTests(SimpleTestCase):
    def test_produce_svg_bien_formado_con_etiquetas(self):
        svg = _generar_svg_ruta(['A', 'B', 'C'], [
            {'longitud': '120 m', 'giro_grados': 0},
            {'longitud': '80 m', 'giro_grados': 90},
        ])
        texto = svg.decode('utf-8')
        self.assertTrue(texto.startswith('<svg'))
        self.assertTrue(texto.endswith('</svg>'))
        self.assertIn('120 m', texto)
        self.assertIn('>A<', texto)
        self.assertIn('>C<', texto)


class GenerarSvgCircuitoTests(SimpleTestCase):
    def test_produce_svg_bien_formado_con_etiquetas(self):
        svg = _generar_svg_circuito([
            {'tipo': 'bateria', 'etiqueta': '12 V'},
            {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
            {'tipo': 'interruptor', 'etiqueta': 'S1'},
        ])
        texto = svg.decode('utf-8')
        self.assertTrue(texto.startswith('<svg'))
        self.assertTrue(texto.endswith('</svg>'))
        self.assertIn('12 V', texto)
        self.assertIn('R1 = 100 Ω', texto)
        self.assertIn('S1', texto)

    def test_funciona_con_capacitor(self):
        svg = _generar_svg_circuito([
            {'tipo': 'bateria', 'etiqueta': '9 V'},
            {'tipo': 'capacitor', 'etiqueta': '10 µF'},
            {'tipo': 'resistencia', 'etiqueta': 'R1 = 1 kΩ'},
        ])
        self.assertIn('10 µF', svg.decode('utf-8'))

    def test_sin_bateria_lanza_error(self):
        # _generar_svg_circuito asume que ya pasó _validar_variante_circuito
        # (que exige exactamente una batería); sin ella debe fallar, no
        # dibujar un circuito incompleto en silencio.
        with self.assertRaises(StopIteration):
            _generar_svg_circuito([
                {'tipo': 'resistencia', 'etiqueta': 'R1 = 100 Ω'},
                {'tipo': 'resistencia', 'etiqueta': 'R2 = 220 Ω'},
            ])


class GenerarSvgFluidosCompuertaTests(SimpleTestCase):
    def test_produce_svg_bien_formado_con_etiquetas(self):
        svg = _generar_svg_fluidos_compuerta('H = 5 m', 'h = 1.5 m', 'A = 0.3 m²')
        texto = svg.decode('utf-8')
        self.assertTrue(texto.startswith('<svg'))
        self.assertTrue(texto.endswith('</svg>'))
        self.assertIn('H = 5 m', texto)
        self.assertIn('h = 1.5 m', texto)
        self.assertIn('A = 0.3 m²', texto)
