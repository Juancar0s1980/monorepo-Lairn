"""
Test de integración del ciclo completo iniciar → responder del motor
adaptativo, con el cliente de IA mockeado (nunca toca Groq/OpenAI/Grok de
verdad). Verifica lo que de verdad importa: que acertar sube la dificultad,
que fallar la baja, y que el examen termina en el momento correcto con un
`Resultado` calculado bien.

No se mockea `cliente_ml.py` (BKT) a propósito: es un microservicio local
que corre en el mismo docker-compose, con un fallback heurístico resiliente
si no responde (ver `test_agente_pronunciacion.py` no depende de esto). No
hay llamada de red externa involucrada.
"""

from rest_framework.test import APITestCase

from apps.examenes.models import Examen
from core.tests.utils import crear_curso, crear_docente, crear_estudiante, inscribir, mock_cliente_ia

_MODULO_AGENTE_IA = 'apps.motor_adaptativo.services.agente_ia'

_PREGUNTA_MOCK = {
    'concepto': 'regla de la cadena',
    'pregunta': '¿Cuál es la derivada de sin(x^2)?',
    'opciones': ['2x cos(x^2)', 'cos(x^2)', '2x sin(x^2)', 'x^2 cos(x)'],
    'respuesta_correcta': '2x cos(x^2)',
}


class FlujoExamenModoFijoTests(APITestCase):
    def setUp(self):
        docente = crear_docente()
        self.estudiante = crear_estudiante()
        curso = crear_curso(docente)
        self.examen = Examen.objects.create(
            curso=curso, titulo='Examen de prueba', tema='Cálculo',
            tiempo=30, num_preguntas=2, dificultad_inicial=2, modo='fijo',
        )
        inscribir(self.estudiante, curso)
        self.client.force_authenticate(user=self.estudiante)

    def _iniciar(self):
        with mock_cliente_ia(_MODULO_AGENTE_IA, _PREGUNTA_MOCK):
            return self.client.post('/api/motor-adaptativo/iniciar/', {'examen_id': self.examen.id})

    def _responder(self, sesion_id, correcta: bool):
        respuesta = _PREGUNTA_MOCK['respuesta_correcta'] if correcta else 'una respuesta incorrecta'
        with mock_cliente_ia(_MODULO_AGENTE_IA, _PREGUNTA_MOCK):
            return self.client.post(
                f'/api/motor-adaptativo/{sesion_id}/responder/',
                {'respuesta': respuesta, 'tiempo_segundos': 10},
            )

    def test_iniciar_examen_genera_la_primera_pregunta(self):
        resp = self._iniciar()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['dificultad_actual'], 2)
        self.assertEqual(resp.data['pregunta'], _PREGUNTA_MOCK['pregunta'])
        self.assertEqual(resp.data['opciones'], _PREGUNTA_MOCK['opciones'])

    def test_acertar_sube_la_dificultad(self):
        sesion_id = self._iniciar().data['sesion_id']
        resp = self._responder(sesion_id, correcta=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['es_correcta'])
        self.assertEqual(resp.data['dificultad_actual'], 3)

    def test_fallar_baja_la_dificultad(self):
        sesion_id = self._iniciar().data['sesion_id']
        resp = self._responder(sesion_id, correcta=False)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['es_correcta'])
        self.assertEqual(resp.data['dificultad_actual'], 1)

    def test_examen_termina_al_completar_num_preguntas_con_resultado_correcto(self):
        sesion_id = self._iniciar().data['sesion_id']
        primera = self._responder(sesion_id, correcta=True)
        self.assertFalse(primera.data['completado'])

        segunda = self._responder(sesion_id, correcta=True)
        self.assertTrue(segunda.data['completado'])
        self.assertEqual(segunda.data['razon_fin'], 'preguntas_completadas')
        self.assertEqual(segunda.data['correctas'], 2)
        self.assertEqual(segunda.data['puntaje'], 100.0)
        # nota = 1.0 + (correctas/total)*4.0 -> con 100% de aciertos, nota = 5.0
        self.assertEqual(segunda.data['nota'], 5.0)

    def test_no_se_puede_responder_un_examen_ya_completado(self):
        sesion_id = self._iniciar().data['sesion_id']
        self._responder(sesion_id, correcta=True)
        self._responder(sesion_id, correcta=True)  # completa el examen (num_preguntas=2)

        resp = self._responder(sesion_id, correcta=True)
        self.assertEqual(resp.status_code, 400)

    def test_estudiante_no_inscrito_no_puede_iniciar(self):
        otro_estudiante = crear_estudiante(email='no-inscrito@test.com')
        self.client.force_authenticate(user=otro_estudiante)
        resp = self._iniciar()
        self.assertEqual(resp.status_code, 403)
