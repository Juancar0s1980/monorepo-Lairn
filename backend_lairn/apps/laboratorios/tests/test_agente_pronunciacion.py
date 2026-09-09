"""
Tests de `calcular_similitud()` y `_normalizar()` en
`services/agente_pronunciacion.py` — el algoritmo que decide si un
estudiante pronunció correctamente comparando lo que Whisper transcribió
contra `pregunta.texto_pronunciar`. Puro, sin mock, sin base de datos: el
más barato y de mayor valor de todo el lote.
"""

from django.test import SimpleTestCase

from apps.laboratorios.services.agente_pronunciacion import _normalizar, calcular_similitud


class NormalizarTests(SimpleTestCase):
    def test_baja_a_minusculas(self):
        self.assertEqual(_normalizar('Network Architecture'), 'network architecture')

    def test_quita_puntuacion(self):
        self.assertEqual(_normalizar("It's a test!"), 'its a test')

    def test_colapsa_espacios_multiples(self):
        self.assertEqual(_normalizar('hello    world'), 'hello world')

    def test_quita_espacios_en_los_extremos(self):
        self.assertEqual(_normalizar('  hello world  '), 'hello world')


class CalcularSimilitudTests(SimpleTestCase):
    def test_transcripcion_identica_da_100(self):
        self.assertEqual(calcular_similitud('Network Architecture', 'Network Architecture'), 100.0)

    def test_diferencia_de_mayusculas_y_puntuacion_no_afecta(self):
        self.assertEqual(calcular_similitud('Network Architecture', "network architecture!"), 100.0)

    def test_frase_totalmente_distinta_da_puntaje_bajo(self):
        similitud = calcular_similitud('Network Architecture', 'completely unrelated banana sandwich')
        self.assertLess(similitud, 40.0)

    def test_esperado_vacio_da_cero(self):
        self.assertEqual(calcular_similitud('', 'algo'), 0.0)

    def test_transcripcion_vacia_da_cero(self):
        self.assertEqual(calcular_similitud('algo', ''), 0.0)

    def test_similitud_parcial_queda_entre_extremos(self):
        similitud = calcular_similitud('Good morning everyone', 'Good morning')
        self.assertGreater(similitud, 40.0)
        self.assertLess(similitud, 100.0)
