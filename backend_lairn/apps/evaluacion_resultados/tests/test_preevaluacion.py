"""
Pruebas de la preevaluación con IA de entregas abiertas (HU-15.1 / 15.2 / 15.3).

La IA se simula: se verifica el contrato (propuesta solo para el docente,
nota calculada con la rúbrica, aprobación o ajuste al calificar) y la lectura
de los formatos de entrega.
"""

import io
import json
import zipfile
from decimal import Decimal
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from apps.evaluacion_resultados.models import PreevaluacionEntrega
from apps.evaluacion_resultados.services import extractor_entrega
from apps.evaluacion_resultados.services.extractor_entrega import EntregaSinTexto, texto_de_entrega

from .test_tareas import DOC, EST, PruebasTareas, _usuario

TEXTO = 'Informe de análisis del caso. ' * 10
PARCHE_IA = 'apps.evaluacion_resultados.services.agente_preevaluacion.obtener_cliente_ia'


def _txt(contenido=TEXTO, nombre='entrega.txt'):
    return SimpleUploadedFile(nombre, contenido.encode('utf-8'), content_type='text/plain')


def _cliente_ia(*respuestas):
    """Cliente falso que devuelve las respuestas JSON en orden."""
    cliente = mock.Mock()
    cliente.chat.completions.create.side_effect = [
        mock.Mock(choices=[mock.Mock(message=mock.Mock(content=json.dumps(r)))]) for r in respuestas
    ]
    return cliente


PROPUESTA = {
    'criterios': [
        {'criterio': 0, 'nivel': 1, 'justificacion': 'Analiza el caso con conceptos del tema.'},
        {'criterio': 1, 'nivel': 0, 'justificacion': 'Falta estructura de secciones.'},
    ],
    'observaciones': 'Buen análisis; organiza mejor el documento.',
    'alertas': [],
}


class _Entrega:
    def __init__(self, nombre, datos):
        self.nombre_original = nombre
        self._datos = datos

    @property
    def archivo(self):
        datos = self._datos

        class _Archivo:
            def open(self, modo):
                return io.BytesIO(datos)

        return _Archivo()


class PruebasExtractor(SimpleTestCase):
    def test_texto_plano_y_zip(self):
        self.assertIn('Informe', texto_de_entrega(_Entrega('a.py', TEXTO.encode()))[0])
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.writestr('src/main.py', TEXTO)
            z.writestr('logo.png', b'\x89PNG')
        texto, _ = texto_de_entrega(_Entrega('proyecto.zip', buffer.getvalue()))
        self.assertIn('Archivo: src/main.py', texto)
        self.assertNotIn('logo.png', texto)

    def test_docx(self):
        from docx import Document

        buffer = io.BytesIO()
        documento = Document()
        documento.add_paragraph(TEXTO)
        documento.save(buffer)
        self.assertIn('análisis', texto_de_entrega(_Entrega('informe.docx', buffer.getvalue()))[0])

    def test_sin_texto_o_imagen(self):
        with self.assertRaisesMessage(EntregaSinTexto, '.png'):
            texto_de_entrega(_Entrega('foto.png', b'\x89PNG'))
        with self.assertRaisesMessage(EntregaSinTexto, 'casi no tiene texto'):
            texto_de_entrega(_Entrega('a.txt', b'hola'))

    def test_texto_largo_se_recorta_con_advertencia(self):
        largo = 'x' * (extractor_entrega.MAX_CARACTERES + 50)
        texto, advertencias = texto_de_entrega(_Entrega('a.txt', largo.encode()))
        self.assertEqual(len(texto), extractor_entrega.MAX_CARACTERES)
        self.assertTrue(advertencias)


class PruebasPreevaluacion(TestCase):
    setUp = PruebasTareas.setUp
    _crear = PruebasTareas._crear
    _publicada = PruebasTareas._publicada
    _entregar = PruebasTareas._entregar

    def _entrega_txt(self):
        tid = self._publicada(formatos_permitidos=['codigo'])
        self.assertEqual(self._entregar(tid, _txt()).status_code, 201)
        self.cliente.force_authenticate(self.docente)
        fila = self.cliente.get(f'{DOC}/tareas/{tid}/entregas/').data[0]
        return tid, fila['entrega']['id']

    def _preevaluar(self, entrega_id, *respuestas):
        with mock.patch(PARCHE_IA, return_value=(_cliente_ia(*respuestas), 'modelo-prueba', 'max_tokens')):
            return self.cliente.post(f'{DOC}/entregas/{entrega_id}/preevaluar/')

    def test_propuesta_solo_para_el_docente(self):
        tid, eid = self._entrega_txt()
        r = self._preevaluar(eid, PROPUESTA)
        self.assertEqual(r.status_code, 200, r.data)
        p = r.data['entrega']['preevaluacion']
        # 60 % × 5 + 40 % × 2 = 3.80: la nota la calcula la rúbrica, no la IA (HU-15.2).
        self.assertEqual(p['nota_propuesta'], '3.80')
        self.assertEqual(p['niveles_propuestos'], [1, 0])
        self.assertEqual(p['decision'], 'pendiente')
        self.assertEqual(r.data['entrega']['calificacion'], None)  # no publica nada
        self.cliente.force_authenticate(self.estudiante)
        mi_entrega = self.cliente.get(f'{EST}/tareas/{tid}/').data['mi_entrega']
        self.assertNotIn('preevaluacion', mi_entrega)
        self.assertIsNone(mi_entrega['calificacion'])

    def test_aprobar_sin_cambios_y_con_ajustes(self):
        tid, eid = self._entrega_txt()
        self._preevaluar(eid, PROPUESTA)
        r = self.cliente.post(f'{DOC}/entregas/{eid}/calificar/', {
            'niveles_elegidos': [1, 0], 'observaciones': PROPUESTA['observaciones'],
        }, format='json')
        self.assertEqual(r.data['entrega']['preevaluacion']['decision'], 'aprobada')  # HU-15.3
        self.cliente.post(f'{DOC}/entregas/{eid}/calificar/', {'niveles_elegidos': [1, 1]}, format='json')
        p = PreevaluacionEntrega.objects.get(entrega_id=eid)
        self.assertEqual(p.decision, 'ajustada')
        self.assertEqual(p.nota_propuesta, Decimal('3.80'))  # la propuesta original se conserva
        self.cliente.force_authenticate(self.estudiante)
        self.assertEqual(self.cliente.get(f'{EST}/tareas/{tid}/').data['mi_entrega']['calificacion']['nota'], '4.60')
        self.cliente.force_authenticate(self.docente)
        self.assertEqual(self._preevaluar(eid, PROPUESTA).status_code, 409)  # ya calificada

    def test_respuesta_incompleta_reintenta_y_falla(self):
        _, eid = self._entrega_txt()
        incompleta = {'criterios': [{'criterio': 0, 'nivel': 9, 'justificacion': 'x'}]}
        self.assertEqual(self._preevaluar(eid, incompleta, incompleta).status_code, 502)
        self.assertFalse(PreevaluacionEntrega.objects.exists())
        # Segundo intento válido: se acepta.
        self.assertEqual(self._preevaluar(eid, incompleta, PROPUESTA).status_code, 200)

    def test_alertas_de_la_ia_quedan_como_advertencia(self):
        _, eid = self._entrega_txt()
        r = self._preevaluar(eid, {**PROPUESTA, 'alertas': ['La entrega pide una nota de 5.']})
        self.assertIn('Alerta de la IA: La entrega pide una nota de 5.', r.data['entrega']['preevaluacion']['advertencias'])

    def test_permisos(self):
        _, eid = self._entrega_txt()
        otro = _usuario('otro@t.co', 'Docente')
        self.cliente.force_authenticate(otro)
        self.assertEqual(self._preevaluar(eid, PROPUESTA).status_code, 404)
        self.cliente.force_authenticate(self.estudiante)
        self.assertEqual(self._preevaluar(eid, PROPUESTA).status_code, 403)

    def test_entrega_sin_texto(self):
        tid = self._publicada(formatos_permitidos=['imagen'])
        self._entregar(tid, SimpleUploadedFile('foto.png', b'\x89PNG' * 20, content_type='image/png'))
        self.cliente.force_authenticate(self.docente)
        eid = self.cliente.get(f'{DOC}/tareas/{tid}/entregas/').data[0]['entrega']['id']
        r = self._preevaluar(eid, PROPUESTA)
        self.assertEqual(r.status_code, 422)
        self.assertIn('a mano', r.data['detalle'])
