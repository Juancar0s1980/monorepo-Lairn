"""
Pruebas de la presentación de la evaluación formal por el estudiante (HU-07).
El paso del tiempo se simula moviendo el reloj con `mock.patch`.
"""

from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    MomentoEvaluacion,
    PreguntaBanco,
    ProgramaAcademico,
    ResultadoAprendizaje,
)
from apps.examenes.models import Curso, Inscripcion
from apps.users.models import Role, User

EST = '/api/evaluacion/estudiante/evaluaciones'
RELOJ = 'django.utils.timezone.now'


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name='N', first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class PruebasPresentacion(TestCase):
    def setUp(self):
        self.ahora = timezone.now()
        docente = _usuario('doc@t.co', 'Docente')
        self.estudiante = _usuario('est@t.co', 'Estudiante')
        self.no_convocado = _usuario('otro@t.co', 'Estudiante')
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        curso = Curso.objects.create(nombre='Curso', docente=docente)
        Inscripcion.objects.create(estudiante=self.estudiante, curso=curso)
        asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=programa, curso_vinculado=curso)
        comp = Competencia.objects.create(programa=programa, nombre='C', tipo='especifica')
        ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asignatura, descripcion='RA')
        momento = MomentoEvaluacion.objects.create(programa=programa, semestre_referencia=4, nombre='M1')
        self.evaluacion = EvaluacionFormal.objects.create(
            momento=momento, nombre='Eval', fecha_inicio=self.ahora - timedelta(minutes=5),
            fecha_fin=self.ahora + timedelta(hours=2), duracion_minutos=30, estado='publicada',
        )
        self.preguntas = []
        for i, correcta in enumerate([0, 2]):
            p = PreguntaBanco.objects.create(
                asignatura=asignatura, resultado=ra, enunciado=f'P{i}', opciones=['a', 'b', 'c'],
                respuesta_correcta=correcta, retroalimentacion='secreta', estado='aprobada',
            )
            EvaluacionPregunta.objects.create(evaluacion=self.evaluacion, pregunta=p, orden=i)
            self.preguntas.append(p)
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.estudiante)
        self.url = f'{EST}/{self.evaluacion.id}'

    def test_solo_convocado_y_activa(self):
        self.assertEqual([e['id'] for e in self.cliente.get(f'{EST}/').data], [self.evaluacion.id])  # HU-07.1
        self.cliente.force_authenticate(self.no_convocado)
        self.assertEqual(self.cliente.get(f'{EST}/').data, [])
        self.assertEqual(self.cliente.post(f'{self.url}/iniciar/').status_code, 404)
        self.cliente.force_authenticate(self.estudiante)
        EvaluacionFormal.objects.filter(pk=self.evaluacion.pk).update(fecha_inicio=self.ahora + timedelta(days=1),
                                                                      fecha_fin=self.ahora + timedelta(days=2))
        self.assertEqual(self.cliente.get(f'{EST}/').data, [])
        self.assertEqual(self.cliente.post(f'{self.url}/iniciar/').status_code, 400)

    def test_iniciar_no_revela_respuestas_y_es_unico(self):
        r = self.cliente.post(f'{self.url}/iniciar/')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.data['preguntas']), 2)
        for p in r.data['preguntas']:
            self.assertNotIn('respuesta_correcta', p)
            self.assertNotIn('retroalimentacion', p)
        self.cliente.post(f'{self.url}/iniciar/')
        self.assertEqual(IntentoEvaluacion.objects.count(), 1)
        # El vencimiento respeta la duración (30 min) dentro de la ventana.
        intento = IntentoEvaluacion.objects.get()
        self.assertAlmostEqual((intento.vence_en - intento.iniciado_en).total_seconds(), 1800, delta=2)

    def test_guardar_en_tiempo_real_y_enviar(self):
        self.cliente.post(f'{self.url}/iniciar/')
        p0, p1 = self.preguntas
        self.assertEqual(self.cliente.put(f'{self.url}/respuestas/', {'pregunta': p0.id, 'opcion': 0}, format='json').data['respondidas'], 1)
        self.cliente.put(f'{self.url}/respuestas/', {'pregunta': p1.id, 'opcion': 1}, format='json')
        self.cliente.put(f'{self.url}/respuestas/', {'pregunta': p1.id, 'opcion': 2}, format='json')  # cambia de opinión
        self.assertEqual(self.cliente.get(self.url + '/').data['respuestas'], {str(p0.id): 0, str(p1.id): 2})  # HU-07.2
        self.assertEqual(self.cliente.put(f'{self.url}/respuestas/', {'pregunta': 999, 'opcion': 0}, format='json').status_code, 400)
        self.assertEqual(self.cliente.put(f'{self.url}/respuestas/', {'pregunta': p0.id, 'opcion': 7}, format='json').status_code, 400)
        r = self.cliente.post(f'{self.url}/enviar/')
        self.assertEqual(r.data['intento']['estado'], 'enviado')
        intento = IntentoEvaluacion.objects.get()
        self.assertEqual((intento.aciertos, intento.total, str(intento.nota), intento.envio_automatico), (2, 2, '5.00', False))
        self.assertEqual(self.cliente.put(f'{self.url}/respuestas/', {'pregunta': p0.id, 'opcion': 1}, format='json').status_code, 409)

    def test_envio_automatico_al_vencer(self):
        self.cliente.post(f'{self.url}/iniciar/')
        self.cliente.put(f'{self.url}/respuestas/', {'pregunta': self.preguntas[0].id, 'opcion': 0}, format='json')
        intento = IntentoEvaluacion.objects.get()
        despues = intento.vence_en + timedelta(minutes=1)
        with mock.patch(RELOJ, return_value=despues):
            tardia = self.cliente.put(f'{self.url}/respuestas/', {'pregunta': self.preguntas[1].id, 'opcion': 2}, format='json')
            self.assertEqual(tardia.status_code, 409)  # ya no se registran respuestas
            resumen = self.cliente.get(self.url + '/').data
        intento.refresh_from_db()
        self.assertEqual(resumen['intento']['estado'], 'enviado')  # HU-07.3
        self.assertTrue(intento.envio_automatico)
        self.assertEqual(intento.enviado_en, intento.vence_en)
        self.assertEqual((intento.aciertos, intento.total), (1, 2))  # solo lo registrado a tiempo
        self.assertNotIn('preguntas', resumen)

    def test_envio_del_temporizador_dentro_del_margen_es_automatico(self):
        self.cliente.post(f'{self.url}/iniciar/')
        intento = IntentoEvaluacion.objects.get()
        with mock.patch(RELOJ, return_value=intento.vence_en + timedelta(seconds=1)):
            self.cliente.post(f'{self.url}/enviar/')
        intento.refresh_from_db()
        self.assertTrue(intento.envio_automatico)
        self.assertEqual(intento.enviado_en, intento.vence_en)

    def test_vencimiento_no_supera_cierre_de_ventana(self):
        EvaluacionFormal.objects.filter(pk=self.evaluacion.pk).update(fecha_fin=self.ahora + timedelta(minutes=10))
        self.cliente.post(f'{self.url}/iniciar/')
        intento = IntentoEvaluacion.objects.get()
        self.assertEqual(intento.vence_en, EvaluacionFormal.objects.get().fecha_fin)

    def test_solo_estudiantes(self):
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))
        self.assertEqual(self.cliente.get(f'{EST}/').status_code, 403)
