"""
Pruebas del banco de preguntas (HU-04 / HU-05).

La IA se simula: se prueba el contrato (validación de lo que devuelve el
proveedor) y las reglas de negocio, no el proveedor real.
"""

import json
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    PreguntaBanco,
    ProgramaAcademico,
    ResultadoAprendizaje,
)
from apps.evaluacion_resultados.services.agente_preguntas_banco import _validar
from apps.examenes.models import Curso
from apps.users.models import Role, User

BASE = '/api/evaluacion/docente'
PREGUNTA_IA = {
    'contexto': 'Una empresa necesita...', 'enunciado': '¿Qué patrón aplica?',
    'opciones': ['Observer', 'Singleton', 'Factory', 'Adapter'], 'respuesta_correcta': 2,
    'retroalimentacion': 'Factory porque...',
}


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name='N', first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


def _respuesta_ia(preguntas):
    mensaje = mock.Mock(content=json.dumps({'preguntas': preguntas}))
    cliente = mock.Mock()
    cliente.chat.completions.create.return_value = mock.Mock(choices=[mock.Mock(message=mensaje)])
    return mock.patch(
        'apps.evaluacion_resultados.services.agente_preguntas_banco.obtener_cliente_ia',
        return_value=(cliente, 'modelo-prueba', 'max_tokens'),
    )


class PruebasBancoPreguntas(TestCase):
    def setUp(self):
        self.docente = _usuario('doc@t.co', 'Docente')
        self.otro_docente = _usuario('otro@t.co', 'Docente')
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ingeniería')
        self.curso = Curso.objects.create(nombre='Diseño', docente=self.docente)
        self.asignatura = AsignaturaMalla.objects.create(
            codigo='A1', nombre='Diseño de software', programa=programa, curso_vinculado=self.curso,
        )
        especifica = Competencia.objects.create(programa=programa, nombre='Diseño', tipo='especifica')
        self.transversal = Competencia.objects.create(programa=programa, nombre='Pensamiento crítico', tipo='transversal')
        self.ra = ResultadoAprendizaje.objects.create(
            competencia=especifica, asignatura=self.asignatura, descripcion='Aplicar patrones de diseño',
        )
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.docente)

    def _generar(self, preguntas=None, **extra):
        cuerpo = {'asignatura': self.asignatura.id, 'resultado': self.ra.id,
                  'competencia_transversal': self.transversal.id, 'cantidad': 2, **extra}
        with _respuesta_ia(preguntas if preguntas is not None else [PREGUNTA_IA, PREGUNTA_IA]):
            return self.cliente.post(f'{BASE}/banco/generar/', cuerpo, format='json')

    def test_generar_crea_pendientes_con_competencia_asociada(self):
        r = self._generar()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(r.data), 2)
        for p in r.data:
            self.assertEqual(p['estado'], 'pendiente')
            self.assertEqual(p['competencia_transversal']['nombre'], 'Pensamiento crítico')  # HU-04.3

    def test_generar_rechaza_competencia_no_transversal_y_ra_ajeno(self):
        especifica = self.ra.competencia
        self.assertEqual(self._generar(competencia_transversal=especifica.id).status_code, 400)
        otra = AsignaturaMalla.objects.create(codigo='A2', nombre='Otra', programa=self.asignatura.programa)
        ra_ajeno = ResultadoAprendizaje.objects.create(competencia=especifica, asignatura=otra, descripcion='X')
        self.assertEqual(self._generar(resultado=ra_ajeno.id).status_code, 400)

    def test_respuesta_invalida_de_ia_no_crea_nada(self):
        mala = {**PREGUNTA_IA, 'opciones': ['a', 'a', 'b', 'c']}
        r = self._generar(preguntas=[mala, {**PREGUNTA_IA, 'respuesta_correcta': 9}])
        self.assertEqual(r.status_code, 502)
        self.assertEqual(PreguntaBanco.objects.count(), 0)

    def test_validador_de_contrato(self):
        self.assertIsNotNone(_validar(PREGUNTA_IA))
        self.assertIsNone(_validar({**PREGUNTA_IA, 'opciones': ['a', 'b', 'c']}))
        self.assertIsNone(_validar({**PREGUNTA_IA, 'respuesta_correcta': True}))
        self.assertIsNone(_validar({**PREGUNTA_IA, 'enunciado': ' '}))

    def test_ciclo_editar_aprobar_y_filtros(self):
        ids = [p['id'] for p in self._generar().data]
        editada = self.cliente.patch(f'{BASE}/banco/{ids[0]}/', {'enunciado': 'Nuevo enunciado'}, format='json')
        self.assertEqual(editada.data['enunciado'], 'Nuevo enunciado')  # HU-05.2
        self.assertEqual(self.cliente.post(f'{BASE}/banco/{ids[0]}/aprobar/').data['estado'], 'aprobada')  # HU-05.3
        descartada = self.cliente.post(f'{BASE}/banco/{ids[1]}/descartar/', {'motivo': 'Ambigua'}, format='json')
        self.assertEqual((descartada.data['estado'], descartada.data['motivo_descarte']), ('descartada', 'Ambigua'))
        # Una revisada ya no se edita ni se vuelve a revisar.
        self.assertEqual(self.cliente.patch(f'{BASE}/banco/{ids[0]}/', {'enunciado': 'x'}, format='json').status_code, 409)
        self.assertEqual(self.cliente.post(f'{BASE}/banco/{ids[1]}/aprobar/').status_code, 409)
        # HU-05.1 panel de pendientes y HU-04.5 filtro por competencia transversal.
        self.assertEqual(len(self.cliente.get(f'{BASE}/banco/?estado=pendiente').data), 0)
        filtro = self.cliente.get(f'{BASE}/banco/?estado=aprobada&competencia_transversal={self.transversal.id}')
        self.assertEqual([p['id'] for p in filtro.data], [ids[0]])

    def test_edicion_valida_opciones(self):
        pid = self._generar().data[0]['id']
        r = self.cliente.patch(f'{BASE}/banco/{pid}/', {'opciones': ['Sí'], 'respuesta_correcta': 0}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.cliente.patch(f'{BASE}/banco/{pid}/', {'respuesta_correcta': 7}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_otro_docente_no_ve_ni_modifica(self):
        pid = self._generar().data[0]['id']
        self.cliente.force_authenticate(self.otro_docente)
        self.assertEqual(self.cliente.get(f'{BASE}/asignaturas/').data, [])
        self.assertEqual(self.cliente.get(f'{BASE}/banco/').data, [])
        self.assertEqual(self.cliente.post(f'{BASE}/banco/{pid}/aprobar/').status_code, 404)
        self.assertEqual(self._generar().status_code, 404)

    def test_estudiante_y_coordinador_sin_acceso(self):
        for rol in ('Estudiante', 'Coordinador'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
                self.assertEqual(self.cliente.get(f'{BASE}/banco/').status_code, 403)

    def test_mis_asignaturas_incluye_ra_y_transversales(self):
        datos = self.cliente.get(f'{BASE}/asignaturas/').data
        self.assertEqual(len(datos), 1)
        self.assertEqual([r['id'] for r in datos[0]['resultados']], [self.ra.id])
        self.assertEqual([c['id'] for c in datos[0]['competencias_transversales']], [self.transversal.id])

    def test_coordinador_lista_cursos_vinculables(self):
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))
        cursos = self.cliente.get('/api/evaluacion/cursos/').data
        self.assertEqual(cursos[0]['docente_email'], 'doc@t.co')
