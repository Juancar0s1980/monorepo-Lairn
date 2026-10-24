"""
Tests de `SerializadorSugerirLaboratorioLibre` — el contrato de entrada del
endpoint "generar laboratorio con IA a partir de un enunciado libre". Cubre
el bug real que se reportó y arregló en esta misma sesión: el frontend
dejaba escribir `cantidad_preguntas` fuera de 1-8 y el error no explicaba
por qué. Sin base de datos, sin mock — es validación pura de un serializer.
"""

from django.test import SimpleTestCase

from apps.laboratorios.serializers import SerializadorSugerirLaboratorioLibre


def _datos(**overrides):
    base = {'enunciado': 'un laboratorio de prueba', 'lenguaje': 'python'}
    base.update(overrides)
    return base


class CantidadPreguntasTests(SimpleTestCase):
    def test_acepta_el_minimo(self):
        s = SerializadorSugerirLaboratorioLibre(data=_datos(cantidad_preguntas=1))
        self.assertTrue(s.is_valid(), s.errors)

    def test_acepta_el_maximo(self):
        s = SerializadorSugerirLaboratorioLibre(data=_datos(cantidad_preguntas=8))
        self.assertTrue(s.is_valid(), s.errors)

    def test_rechaza_cero(self):
        s = SerializadorSugerirLaboratorioLibre(data=_datos(cantidad_preguntas=0))
        self.assertFalse(s.is_valid())
        self.assertIn('cantidad_preguntas', s.errors)

    def test_rechaza_mas_de_8(self):
        """El bug real reportado: el docente pidió 10 y el backend lo rechazó
        con un 400 que el frontend no explicaba bien."""
        s = SerializadorSugerirLaboratorioLibre(data=_datos(cantidad_preguntas=10))
        self.assertFalse(s.is_valid())
        self.assertIn('cantidad_preguntas', s.errors)

    def test_default_es_3_si_no_se_manda(self):
        s = SerializadorSugerirLaboratorioLibre(data=_datos())
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['cantidad_preguntas'], 3)


class TipoYLenguajeTests(SimpleTestCase):
    def test_tipo_codigo_sin_lenguaje_es_invalido(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'tipo': 'codigo'})
        self.assertFalse(s.is_valid())
        self.assertIn('lenguaje', s.errors)

    def test_tipo_codigo_con_lenguaje_es_valido(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'tipo': 'codigo', 'lenguaje': 'python'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_tipo_pronunciacion_no_requiere_lenguaje(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'tipo': 'pronunciacion'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_tipo_respuesta_libre_no_requiere_lenguaje(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'tipo': 'respuesta_libre'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_tipo_problema_visual_no_requiere_lenguaje(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'tipo': 'problema_visual'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_tipo_por_defecto_es_codigo(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': 'x', 'lenguaje': 'python'})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['tipo'], 'codigo')

    def test_enunciado_vacio_es_invalido(self):
        s = SerializadorSugerirLaboratorioLibre(data={'enunciado': '', 'tipo': 'pronunciacion'})
        self.assertFalse(s.is_valid())
        self.assertIn('enunciado', s.errors)
