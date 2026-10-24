"""
Tests de `calcular_puntaje_laboratorio()` en `services/calculador_nota.py`
— decide si un estudiante ya puede "finalizar" un laboratorio como práctica
de examen. Usa el ORM (crea Laboratorio/Pregunta/Entrega reales), así que
corre como `TestCase` normal (con base de datos de test).
"""

from django.test import TestCase

from apps.laboratorios.models import Laboratorio, Pregunta, Entrega
from apps.laboratorios.services.calculador_nota import calcular_puntaje_laboratorio
from core.tests.utils import crear_curso, crear_docente, crear_estudiante


class CalcularPuntajeLaboratorioTests(TestCase):
    def setUp(self):
        docente = crear_docente()
        self.estudiante = crear_estudiante()
        curso = crear_curso(docente)
        self.laboratorio = Laboratorio.objects.create(curso=curso, titulo='Lab de prueba')

    def _crear_pregunta(self, **kwargs):
        defaults = {'laboratorio': self.laboratorio, 'tipo': 'codigo', 'enunciado': 'Enunciado de prueba'}
        defaults.update(kwargs)
        return Pregunta.objects.create(**defaults)

    def _entregar(self, pregunta, puntaje, intento=1):
        return Entrega.objects.create(
            pregunta=pregunta, estudiante=self.estudiante, puntaje=puntaje, intento=intento
        )

    def test_laboratorio_sin_preguntas_da_none(self):
        self.assertIsNone(calcular_puntaje_laboratorio(self.laboratorio, self.estudiante))

    def test_falta_una_pregunta_por_responder_da_none(self):
        p1 = self._crear_pregunta(orden=0)
        self._crear_pregunta(orden=1)  # p2, sin entrega
        self._entregar(p1, puntaje=100.0)
        self.assertIsNone(calcular_puntaje_laboratorio(self.laboratorio, self.estudiante))

    def test_todas_respondidas_devuelve_el_promedio(self):
        p1 = self._crear_pregunta(orden=0)
        p2 = self._crear_pregunta(orden=1)
        self._entregar(p1, puntaje=100.0)
        self._entregar(p2, puntaje=50.0)
        self.assertEqual(calcular_puntaje_laboratorio(self.laboratorio, self.estudiante), 75.0)

    def test_usa_la_mejor_entrega_no_la_ultima(self):
        """Un reintento que mejora no debe verse penalizado por el intento
        fallido anterior — se toma el máximo por pregunta, no el más reciente."""
        p1 = self._crear_pregunta(orden=0)
        self._entregar(p1, puntaje=20.0, intento=1)
        self._entregar(p1, puntaje=90.0, intento=2)
        self.assertEqual(calcular_puntaje_laboratorio(self.laboratorio, self.estudiante), 90.0)

    def test_entrega_de_otro_estudiante_no_cuenta(self):
        p1 = self._crear_pregunta(orden=0)
        self._entregar(p1, puntaje=100.0)
        otro_estudiante = crear_estudiante(email='otro@test.com')
        self.assertIsNone(calcular_puntaje_laboratorio(self.laboratorio, otro_estudiante))
