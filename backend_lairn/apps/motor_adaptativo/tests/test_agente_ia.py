"""
Tests de `_validar_pregunta()` en `services/agente_ia.py` — la última línea
de defensa antes de mostrarle una pregunta al estudiante. Sin mock: es
validación pura, no llama a ninguna IA.
"""

from django.test import SimpleTestCase

from apps.motor_adaptativo.services.agente_ia import _validar_pregunta


def _pregunta_valida(**overrides) -> dict:
    base = {
        'concepto': 'regla de la cadena',
        'pregunta': '¿Cuál es la derivada de sin(x^2)?',
        'opciones': ['2x cos(x^2)', 'cos(x^2)', '2x sin(x^2)', 'x^2 cos(x)'],
        'respuesta_correcta': '2x cos(x^2)',
    }
    base.update(overrides)
    return base


class ValidarPreguntaTests(SimpleTestCase):
    def test_pregunta_valida_no_lanza_error(self):
        _validar_pregunta(_pregunta_valida(), guiado=False)  # no debe lanzar

    def test_pregunta_guiada_valida_no_lanza_error(self):
        datos = _pregunta_valida(explicacion='La regla de la cadena dice que...')
        _validar_pregunta(datos, guiado=True)  # no debe lanzar

    def test_guiado_sin_explicacion_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_pregunta(_pregunta_valida(), guiado=True)

    def test_falta_clave_concepto_lanza_error(self):
        datos = _pregunta_valida()
        del datos['concepto']
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_clave_vacia_lanza_error(self):
        datos = _pregunta_valida(pregunta='')
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_menos_de_4_opciones_lanza_error(self):
        datos = _pregunta_valida(opciones=['a', 'b', 'c'])
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_mas_de_4_opciones_lanza_error(self):
        datos = _pregunta_valida(opciones=['a', 'b', 'c', 'd', 'e'])
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_opciones_repetidas_lanza_error(self):
        datos = _pregunta_valida(opciones=['a', 'a', 'b', 'c'], respuesta_correcta='a')
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_opcion_vacia_lanza_error(self):
        datos = _pregunta_valida(opciones=['a', '', 'b', 'c'])
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_respuesta_correcta_no_coincide_con_ninguna_opcion(self):
        """El bug real que se busca atrapar: si esto no calza, la pregunta
        queda imposible de responder correctamente (la vista compara por
        igualdad exacta contra las opciones)."""
        datos = _pregunta_valida(respuesta_correcta='no está en la lista')
        with self.assertRaises(ValueError):
            _validar_pregunta(datos, guiado=False)

    def test_datos_no_son_diccionario_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_pregunta('no es un dict', guiado=False)
