"""
Pruebas del porcentaje de acierto por RA (HU-09.1, métrica provisional).

Escenario: 2 RA, 3 preguntas (RA1: p1, p2; RA2: p3), 2 estudiantes.
- Ana: p1 bien, p2 mal, p3 bien      -> RA1 50 %, RA2 100 %
- Beto: p1 bien, p2 sin responder, p3 mal -> RA1 50 %, RA2 0 %
Grupal: RA1 2/4 = 50 %, RA2 1/2 = 50 %.
"""

from datetime import timedelta

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
from apps.users.models import Role, User


def _usuario(email, rol, nombre='N'):
    return User.objects.create_user(
        email=email, password='x', first_name=nombre, first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class PruebasDesempenoRA(TestCase):
    def setUp(self):
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=self.programa)
        comp = Competencia.objects.create(programa=self.programa, nombre='C', tipo='especifica')
        self.ra1 = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asignatura, descripcion='RA uno')
        self.ra2 = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asignatura, descripcion='RA dos')
        momento = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=4, nombre='M1')
        ahora = timezone.now()
        self.evaluacion = EvaluacionFormal.objects.create(
            momento=momento, nombre='E', fecha_inicio=ahora, fecha_fin=ahora, duracion_minutos=10, estado='publicada',
        )
        self.p = []
        for i, ra in enumerate([self.ra1, self.ra1, self.ra2]):
            p = PreguntaBanco.objects.create(asignatura=asignatura, resultado=ra, enunciado=f'p{i}',
                                             opciones=['a', 'b'], respuesta_correcta=0, estado='aprobada')
            EvaluacionPregunta.objects.create(evaluacion=self.evaluacion, pregunta=p, orden=i)
            self.p.append(p)
        ana, beto = _usuario('ana@t.co', 'Estudiante', 'Ana'), _usuario('beto@t.co', 'Estudiante', 'Beto')
        p1, p2, p3 = (str(x.id) for x in self.p)
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=ana, vence_en=ahora, enviado_en=ahora,
                                         respuestas={p1: 0, p2: 1, p3: 0})
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=beto, vence_en=ahora, enviado_en=ahora,
                                         respuestas={p1: 0, p3: 1})
        # Intento en curso (aún no vence): no cuenta.
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=_usuario('c@t.co', 'Estudiante'),
                                         vence_en=ahora + timedelta(hours=1), respuestas={p1: 0, p2: 0, p3: 0})
        self.cliente = APIClient()
        self.cliente.force_authenticate(_usuario('admin@t.co', 'Administrador'))
        self.url = f'/api/evaluacion/programas/{self.programa.id}/desempeno-ra/'

    def test_porcentaje_grupal_e_individual(self):
        datos = self.cliente.get(self.url).data
        self.assertEqual(datos['resumen'], {'evaluaciones': 1, 'intentos': 2, 'estudiantes': 2, 'anulados_fraude': 0})
        grupal = {f['resultado_id']: (f['aciertos'], f['presentadas'], f['porcentaje']) for f in datos['grupal']}
        self.assertEqual(grupal, {self.ra1.id: (2, 4, 50.0), self.ra2.id: (1, 2, 50.0)})
        individual = {f['estudiante']['nombre']: f for f in datos['individual']}
        ana, beto = individual['Ana A'], individual['Beto A']
        self.assertEqual(ana['por_ra'][str(self.ra1.id)]['porcentaje'], 50.0)
        self.assertEqual(ana['por_ra'][str(self.ra2.id)]['porcentaje'], 100.0)
        self.assertEqual(beto['por_ra'][str(self.ra2.id)]['porcentaje'], 0.0)
        self.assertEqual(beto['porcentaje_total'], 33.3)  # 1 de 3; sin responder cuenta como fallo

    def test_intento_vencido_sin_abrir_se_cierra_y_cuenta(self):
        p1 = str(self.p[0].id)
        IntentoEvaluacion.objects.create(
            evaluacion=self.evaluacion, estudiante=_usuario('d@t.co', 'Estudiante', 'Dora'),
            vence_en=timezone.now() - timedelta(minutes=10), respuestas={p1: 0},
        )
        datos = self.cliente.get(self.url).data
        self.assertEqual(datos['resumen']['intentos'], 3)
        dora = next(f for f in datos['individual'] if f['estudiante']['nombre'] == 'Dora A')
        self.assertEqual(dora['porcentaje_total'], 33.3)  # 1 acierto de 3 presentadas
        self.assertTrue(IntentoEvaluacion.objects.get(estudiante__email='d@t.co').envio_automatico)

    def test_filtros_y_sin_datos(self):
        datos = self.cliente.get(self.url, {'evaluacion': 999}).data
        self.assertEqual((datos['grupal'], datos['individual']), ([], []))
        self.assertEqual([e['id'] for e in datos['filtros']['evaluaciones']], [self.evaluacion.id])

    def test_solo_administrador(self):
        for rol in ('Coordinador', 'Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
                self.assertEqual(self.cliente.get(self.url).status_code, 403)
