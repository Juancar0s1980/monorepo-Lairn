"""
Pruebas del ensamblado de la evaluación formal (HU-06.1 a 06.4).
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    MomentoEvaluacion,
    MomentoResultado,
    PreguntaBanco,
    ProgramaAcademico,
    ResultadoAprendizaje,
)
from apps.examenes.models import Curso
from apps.laboratorios.models import Laboratorio, Pregunta as PreguntaLaboratorio
from apps.users.models import Role, User

BASE = '/api/evaluacion'


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name='N', first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


def _pregunta(asignatura, ra, enunciado, estado='aprobada'):
    return PreguntaBanco.objects.create(
        asignatura=asignatura, resultado=ra, enunciado=enunciado,
        opciones=['a', 'b', 'c', 'd'], respuesta_correcta=0, estado=estado,
    )


class PruebasEvaluacionFormal(TestCase):
    def setUp(self):
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ingeniería')
        docente = _usuario('doc@t.co', 'Docente')
        curso = Curso.objects.create(nombre='Curso', docente=docente)
        self.asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=programa, curso_vinculado=curso)
        competencia = Competencia.objects.create(programa=programa, nombre='C', tipo='especifica')
        self.ra_oblig = ResultadoAprendizaje.objects.create(competencia=competencia, asignatura=self.asignatura, descripcion='RA 1')
        self.ra_opc = ResultadoAprendizaje.objects.create(competencia=competencia, asignatura=self.asignatura, descripcion='RA 2')
        ra_fuera = ResultadoAprendizaje.objects.create(competencia=competencia, asignatura=self.asignatura, descripcion='RA fuera')
        self.momento = MomentoEvaluacion.objects.create(programa=programa, semestre_referencia=4, nombre='Momento 1')
        MomentoResultado.objects.create(momento=self.momento, resultado=self.ra_oblig, obligatorio=True)
        MomentoResultado.objects.create(momento=self.momento, resultado=self.ra_opc, obligatorio=False)

        self.p1 = _pregunta(self.asignatura, self.ra_oblig, 'Pregunta uno')
        self.p2 = _pregunta(self.asignatura, self.ra_opc, 'Pregunta dos')
        self.pendiente = _pregunta(self.asignatura, self.ra_oblig, 'Pendiente', estado='pendiente')
        self.de_otro_ra = _pregunta(self.asignatura, ra_fuera, 'Otro RA')
        # Ya practicada en el laboratorio (mismo enunciado con otro formato): se excluye.
        self.en_lab = _pregunta(self.asignatura, self.ra_oblig, 'Pregunta  PRACTICADA')
        laboratorio = Laboratorio.objects.create(curso=curso, titulo='Lab')
        PreguntaLaboratorio.objects.create(laboratorio=laboratorio, enunciado='pregunta practicada')

        self.cliente = APIClient()
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))
        ahora = timezone.now()
        self.datos = {
            'nombre': 'Evaluación M1', 'tipo': 'cuestionario',
            'fecha_inicio': (ahora + timedelta(days=1)).isoformat(),
            'fecha_fin': (ahora + timedelta(days=2)).isoformat(), 'duracion_minutos': 60,
        }

    def _crear(self, **extra):
        return self.cliente.post(f'{BASE}/momentos/{self.momento.id}/evaluaciones/', {**self.datos, **extra}, format='json')

    def test_banco_elegible_muestra_ra_y_excluye_no_aprobadas_ajenas_y_de_laboratorio(self):
        r = self.cliente.get(f'{BASE}/momentos/{self.momento.id}/banco-elegible/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x['resultado']['id'] for x in r.data['resultados']], [self.ra_oblig.id, self.ra_opc.id])  # HU-06.1
        ids = {p['id'] for x in r.data['resultados'] for p in x['preguntas']}
        self.assertEqual(ids, {self.p1.id, self.p2.id})  # HU-06.2
        self.assertEqual(r.data['excluidas_por_laboratorio'], 1)

    def test_crear_valida_fechas_duracion_y_tipo(self):
        self.assertEqual(self._crear().status_code, 201)  # HU-06.3
        self.assertEqual(self._crear(fecha_fin=self.datos['fecha_inicio']).status_code, 400)
        self.assertEqual(self._crear(duracion_minutos=3000).status_code, 400)
        self.assertEqual(self._crear(tipo='tarea').status_code, 400)  # HU-06.4 aún sin tareas

    def test_seleccion_solo_preguntas_elegibles_y_cobertura(self):
        eid = self._crear().data['id']
        url = f'{BASE}/evaluaciones/{eid}/preguntas/'
        for invalida in (self.pendiente.id, self.de_otro_ra.id, self.en_lab.id):
            with self.subTest(pregunta=invalida):
                self.assertEqual(self.cliente.put(url, {'preguntas': [invalida]}, format='json').status_code, 400)
        r = self.cliente.put(url, {'preguntas': [self.p2.id, self.p1.id]}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['total_preguntas'], 2)
        cobertura = {c['resultado_id']: (c['obligatorio'], c['preguntas']) for c in r.data['cobertura']}
        self.assertEqual(cobertura, {self.ra_oblig.id: (True, 1), self.ra_opc.id: (False, 1)})
        orden = [p['id'] for p in self.cliente.get(url).data]
        self.assertEqual(orden, [self.p2.id, self.p1.id])

    def test_publicar_congela_la_evaluacion(self):
        eid = self._crear().data['id']
        self.assertEqual(self.cliente.post(f'{BASE}/evaluaciones/{eid}/publicar/').status_code, 400)  # sin preguntas
        self.cliente.put(f'{BASE}/evaluaciones/{eid}/preguntas/', {'preguntas': [self.p1.id]}, format='json')
        r = self.cliente.post(f'{BASE}/evaluaciones/{eid}/publicar/')
        self.assertEqual(r.data['estado'], 'publicada')
        self.assertEqual(self.cliente.patch(f'{BASE}/evaluaciones/{eid}/', {'nombre': 'X'}, format='json').status_code, 409)
        self.assertEqual(self.cliente.put(f'{BASE}/evaluaciones/{eid}/preguntas/', {'preguntas': []}, format='json').status_code, 409)
        self.assertEqual(self.cliente.delete(f'{BASE}/evaluaciones/{eid}/').status_code, 409)

    def test_solo_gestores(self):
        for rol in ('Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
                self.assertEqual(self._crear().status_code, 403)
                self.assertEqual(self.cliente.get(f'{BASE}/momentos/{self.momento.id}/banco-elegible/').status_code, 403)
        self.cliente.force_authenticate(_usuario('admin@t.co', 'Administrador'))
        self.assertEqual(self._crear().status_code, 201)
