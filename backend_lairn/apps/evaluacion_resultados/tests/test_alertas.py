"""
Pruebas del sistema de alerta temprana (HU-10.1 a 10.3).

Escenario: 3 evaluaciones formales de 1 pregunta y 1 tarea en el programa.
- Ana: falla las 3 evaluaciones (0 %) y saca 2.0 en la tarea (40 %) -> 4 actividades bajas.
- Beto: acierta todo y saca 5.0 -> 0 bajas.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AlertaDesempeno,
    AsignaturaMalla,
    Competencia,
    EntregaTarea,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    MomentoEvaluacion,
    PreguntaBanco,
    ProgramaAcademico,
    ReglaAlerta,
    ResultadoAprendizaje,
    TareaPractica,
)
from apps.users.models import Role, User


def _usuario(email, rol, nombre='N'):
    return User.objects.create_user(
        email=email, password='x', first_name=nombre, first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class PruebasAlertas(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        self.asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=self.programa)
        comp = Competencia.objects.create(programa=self.programa, nombre='C', tipo='especifica')
        ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=self.asignatura, descripcion='RA')
        momento = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=4, nombre='M1')
        self.ana = _usuario('ana@t.co', 'Estudiante', 'Ana')
        self.beto = _usuario('beto@t.co', 'Estudiante', 'Beto')
        for i in range(3):
            ev = EvaluacionFormal.objects.create(momento=momento, nombre=f'E{i}', fecha_inicio=ahora, fecha_fin=ahora,
                                                 duracion_minutos=10, estado='publicada')
            p = PreguntaBanco.objects.create(asignatura=self.asignatura, resultado=ra, enunciado=f'p{i}',
                                             opciones=['a', 'b'], respuesta_correcta=0, estado='aprobada')
            EvaluacionPregunta.objects.create(evaluacion=ev, pregunta=p)
            IntentoEvaluacion.objects.create(evaluacion=ev, estudiante=self.ana, vence_en=ahora, enviado_en=ahora,
                                             respuestas={str(p.id): 1})
            IntentoEvaluacion.objects.create(evaluacion=ev, estudiante=self.beto, vence_en=ahora, enviado_en=ahora,
                                             respuestas={str(p.id): 0})
        self.tarea = TareaPractica.objects.create(asignatura=self.asignatura, resultado=ra, titulo='Informe',
                                                  descripcion='x', fecha_limite=ahora + timedelta(days=1), estado='publicada')
        EntregaTarea.objects.create(tarea=self.tarea, estudiante=self.ana, archivo='a.pdf', nombre_original='a.pdf',
                                    tamano=1, nota=Decimal('2.00'))
        EntregaTarea.objects.create(tarea=self.tarea, estudiante=self.beto, archivo='b.pdf', nombre_original='b.pdf',
                                    tamano=1, nota=Decimal('5.00'))
        self.cliente = APIClient()
        self.admin = _usuario('admin@t.co', 'Administrador')
        self.coord = _usuario('coord@t.co', 'Coordinador')
        self.cliente.force_authenticate(self.coord)
        self.url = f'/api/evaluacion/programas/{self.programa.id}/alertas/'

    def _alertas_estudiante(self):
        return AlertaDesempeno.objects.filter(tipo='estudiante')

    def test_regla_solo_admin_y_valida(self):
        self.assertEqual(self.cliente.put('/api/evaluacion/alertas/regla/', {'porcentaje_minimo': 50}, format='json').status_code, 403)
        self.cliente.force_authenticate(self.admin)
        self.assertEqual(self.cliente.put('/api/evaluacion/alertas/regla/', {'porcentaje_minimo': 0}, format='json').status_code, 400)
        r = self.cliente.put('/api/evaluacion/alertas/regla/', {'porcentaje_minimo': 60, 'actividades_minimas': 3}, format='json')
        self.assertEqual((r.status_code, r.data['actividades_minimas']), (200, 3))  # HU-10.1
        self.assertEqual(r.data['resumen']['creadas'], 2)  # se reevalúa al guardar: Ana y el curso A1

    def test_alerta_de_estudiante_y_de_curso(self):
        datos = self.cliente.get(self.url).data  # HU-10.2: visible para el Coordinador
        por_tipo = {(a['tipo'], a['estudiante']['nombre'] if a['estudiante'] else a['asignatura']['codigo']): a
                    for a in datos['alertas']}
        self.assertIn(('estudiante', 'Ana A'), por_tipo)
        self.assertNotIn(('estudiante', 'Beto A'), por_tipo)
        self.assertEqual(por_tipo[('estudiante', 'Ana A')]['actividades_bajas'], 4)
        # Curso: promedios por actividad = 50 % en cada evaluación y 70 % en la tarea -> 3 bajas.
        self.assertEqual(por_tipo[('curso', 'A1')]['actividades_bajas'], 3)

    def test_no_duplica_resuelve_y_respeta_atendidas(self):
        self.cliente.get(self.url)
        self.cliente.get(self.url)
        self.assertEqual(self._alertas_estudiante().count(), 1)  # no duplica
        alerta = self._alertas_estudiante().get()
        self.assertEqual(self.cliente.post(f'/api/evaluacion/alertas/{alerta.id}/atender/', {}, format='json').status_code, 400)
        r = self.cliente.post(f'/api/evaluacion/alertas/{alerta.id}/atender/', {'nota': 'Tutoría agendada'}, format='json')
        self.assertEqual(r.data['estado'], 'atendida')
        self.cliente.get(self.url)
        self.assertEqual(self._alertas_estudiante().count(), 1)  # atendida y sin empeorar: no se reabre
        # Si la regla se vuelve más laxa, la condición desaparece; una abierta pasaría a resuelta.
        AlertaDesempeno.objects.update(estado='abierta')
        regla = ReglaAlerta.vigente()
        regla.actividades_minimas = 10
        regla.save()
        self.cliente.get(self.url)
        self.assertEqual(set(AlertaDesempeno.objects.values_list('estado', flat=True)), {'resuelta'})

    def test_exportar_csv_solo_admin(self):
        self.assertEqual(self.cliente.get(self.url + 'exportar/').status_code, 403)
        self.cliente.force_authenticate(self.admin)
        r = self.cliente.get(self.url + 'exportar/')
        self.assertEqual(r.status_code, 200)  # HU-10.3
        self.assertIn('attachment', r['Content-Disposition'])
        contenido = r.content.decode('utf-8-sig')
        self.assertIn('ana@t.co', contenido)
        self.assertIn('Informe (40.0%)', contenido)

    def test_docente_y_estudiante_sin_acceso(self):
        for rol in ('Docente', 'Estudiante'):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
                self.assertEqual(self.cliente.get(self.url).status_code, 403)
