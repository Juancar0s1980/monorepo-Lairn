"""
Tests de `_ajustar_dificultad()` y `_debe_terminar()` en `views/vista_responder.py`
— la lógica que decide qué tan difícil es la siguiente pregunta y cuándo el
examen termina. Son funciones puras (no tocan la base de datos), así que se
las alimenta con objetos livianos (`SimpleNamespace`) en vez de crear un
`Examen`/`SesionExamen` real — más rápido y más claro sobre qué se testea.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.motor_adaptativo.views.vista_responder import _ajustar_dificultad, _debe_terminar


class AjustarDificultadTests(SimpleTestCase):
    def test_acierto_sube_un_escalon(self):
        sesion = SimpleNamespace(dificultad_actual=2)
        _ajustar_dificultad(sesion, es_correcta=True)
        self.assertEqual(sesion.dificultad_actual, 3)

    def test_fallo_baja_un_escalon(self):
        sesion = SimpleNamespace(dificultad_actual=2)
        _ajustar_dificultad(sesion, es_correcta=False)
        self.assertEqual(sesion.dificultad_actual, 1)

    def test_acierto_no_supera_el_maximo(self):
        sesion = SimpleNamespace(dificultad_actual=3)
        _ajustar_dificultad(sesion, es_correcta=True)
        self.assertEqual(sesion.dificultad_actual, 3)

    def test_fallo_no_baja_del_minimo(self):
        sesion = SimpleNamespace(dificultad_actual=1)
        _ajustar_dificultad(sesion, es_correcta=False)
        self.assertEqual(sesion.dificultad_actual, 1)


def _sesion(preguntas_respondidas, modo='fijo', num_preguntas=5, max_preguntas=20):
    examen = SimpleNamespace(modo=modo, num_preguntas=num_preguntas, max_preguntas=max_preguntas)
    return SimpleNamespace(preguntas_respondidas=preguntas_respondidas, examen=examen)


class DebeTerminarTests(SimpleTestCase):
    def test_modo_fijo_no_termina_antes_de_num_preguntas(self):
        terminar, razon = _debe_terminar(_sesion(4, modo='fijo', num_preguntas=5), {})
        self.assertFalse(terminar)
        self.assertEqual(razon, '')

    def test_modo_fijo_termina_exactamente_en_num_preguntas(self):
        terminar, razon = _debe_terminar(_sesion(5, modo='fijo', num_preguntas=5), {})
        self.assertTrue(terminar)
        self.assertEqual(razon, 'preguntas_completadas')

    def test_maestria_no_termina_sin_minimo_cumplido(self):
        conceptos = {'derivadas': {'nivel': 3}}
        terminar, razon = _debe_terminar(_sesion(2, modo='maestria', num_preguntas=5, max_preguntas=20), conceptos)
        self.assertFalse(terminar)

    def test_maestria_no_termina_con_minimo_cumplido_pero_conceptos_debiles(self):
        conceptos = {'derivadas': {'nivel': 1}, 'integrales': {'nivel': 3}}
        terminar, razon = _debe_terminar(_sesion(5, modo='maestria', num_preguntas=5, max_preguntas=20), conceptos)
        self.assertFalse(terminar)

    def test_maestria_termina_cuando_minimo_cumplido_y_todo_dominado(self):
        conceptos = {'derivadas': {'nivel': 3}, 'integrales': {'nivel': 3}}
        terminar, razon = _debe_terminar(_sesion(5, modo='maestria', num_preguntas=5, max_preguntas=20), conceptos)
        self.assertTrue(terminar)
        self.assertEqual(razon, 'conceptos_dominados')

    def test_maestria_termina_por_limite_maximo_aunque_no_este_dominado(self):
        conceptos = {'derivadas': {'nivel': 1}}
        terminar, razon = _debe_terminar(_sesion(20, modo='maestria', num_preguntas=5, max_preguntas=20), conceptos)
        self.assertTrue(terminar)
        self.assertEqual(razon, 'limite_alcanzado')

    def test_maestria_sin_modelo_de_conocimiento_no_termina_por_dominio(self):
        """Si el estudiante todavía no tiene ningún concepto registrado
        (modelo vacío), `all(...)` sobre un dict vacío daría True por
        vacuidad — la guarda `bool(modelo_conceptos)` evita ese falso
        positivo de "todo dominado" cuando en realidad no hay nada evaluado."""
        terminar, razon = _debe_terminar(_sesion(5, modo='maestria', num_preguntas=5, max_preguntas=20), {})
        self.assertFalse(terminar)
