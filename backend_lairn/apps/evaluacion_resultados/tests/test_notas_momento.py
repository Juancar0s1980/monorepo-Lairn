"""
Pruebas de las notas del momento (ADR-019).

Escenario (momento M1, ya cerrado):
  - Cuestionario E1 (2 preguntas) y E2 (3 preguntas) = un solo examen de 5 preguntas.
  - Tarea T (trabajo del momento), con rúbrica.
  - Estudiantes:
      ana   E1 1/2 (responde 2) y E2 3/3 → 4/5 = 4,0 · trabajo 4,5
      beto  E1 2/2 y no presentó E2 (sin excusa) → incompleto; reglamentaria 5×2/5 = 2,0
      caro  ausente en E1 y E2
      dani  con excusa en E1 y E2
      eli   E1 anulado por fraude, E2 2/3 (deja una sin responder)
      fer   no inició nada
"""

from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    AsistenciaEvaluacion,
    Competencia,
    EntregaTarea,
    EsquemaCalificacion,
    EvaluacionFormal,
    EvaluacionPregunta,
    IntentoEvaluacion,
    MomentoEvaluacion,
    PreguntaBanco,
    ProgramaAcademico,
    RegistroSincronizacion,
    ResultadoAprendizaje,
    TareaPractica,
)
from apps.evaluacion_resultados.services.escala_institucional import aprueba, nivel, redondear
from apps.examenes.models import Curso, Inscripcion
from apps.users.models import Role, User

URL = '/api/evaluacion/notas-momento/'
RUBRICA = [{'criterio': 'C', 'descripcion': '', 'peso': 100,
            'niveles': [{'nombre': 'B', 'descripcion': '', 'valor': 1}, {'nombre': 'A', 'descripcion': '', 'valor': 5}]}]


def _u(email, rol, apellido='A'):
    return User.objects.create_user(email=email, password='x', first_name=email.split('@')[0],
                                    first_last_name=apellido, role=Role.objects.get_or_create(name=rol)[0])


class PruebasEscala(TestCase):
    def test_redondeo_reglamentario_y_niveles(self):
        self.assertEqual([redondear(v) for v in (2.15, 2.149, 3.75, 4.55, 4.549)],
                         [Decimal('2.2'), Decimal('2.1'), Decimal('3.8'), Decimal('4.6'), Decimal('4.5')])
        self.assertEqual([nivel(v) for v in (5, 4.55, 4.54, 3.8, 3.75, 3.74, 3.0, 2.95, 2.2, 2.15, 0)],
                         ['superior', 'superior', 'alto', 'alto', 'alto', 'suficiente', 'suficiente', 'suficiente',
                          'insuficiente', 'insuficiente', 'muy_insuficiente'])
        self.assertEqual((aprueba(2.95), aprueba(2.94), aprueba(None)), (True, False, None))


class BaseNotas(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        self.docente = _u('doc@t.co', 'Docente')
        curso = Curso.objects.create(nombre='Curso', docente=self.docente)
        asig = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=self.programa, curso_vinculado=curso)
        comp = Competencia.objects.create(programa=self.programa, nombre='C', tipo='especifica')
        ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asig, descripcion='RA')
        self.momento = MomentoEvaluacion.objects.create(programa=self.programa, semestre_referencia=4, nombre='M1')
        nombres = ['ana', 'beto', 'caro', 'dani', 'eli', 'fer']
        self.e = {n: _u(f'{n}@t.co', 'Estudiante', apellido=chr(65 + i)) for i, n in enumerate(nombres)}
        for u in self.e.values():
            Inscripcion.objects.create(estudiante=u, curso=curso)
        pasado = dict(fecha_inicio=ahora - timedelta(days=2), fecha_fin=ahora - timedelta(days=1), duracion_minutos=30,
                      estado='publicada')
        self.e1 = EvaluacionFormal.objects.create(momento=self.momento, nombre='E1', **pasado)
        self.e2 = EvaluacionFormal.objects.create(momento=self.momento, nombre='E2', **pasado)
        self.q = {}
        for ev, n in ((self.e1, 2), (self.e2, 3)):
            for i in range(n):
                q = PreguntaBanco.objects.create(asignatura=asig, resultado=ra, enunciado=f'{ev.nombre}{i}',
                                                 opciones=['a', 'b'], respuesta_correcta=0, estado='aprobada')
                EvaluacionPregunta.objects.create(evaluacion=ev, pregunta=q, orden=i)
                self.q.setdefault(ev.id, []).append(q)
        self.tarea = TareaPractica.objects.create(
            asignatura=asig, resultado=ra, titulo='T', descripcion='d', formatos_permitidos=['pdf'],
            fecha_limite=ahora - timedelta(days=1), rubrica=RUBRICA, estado='publicada')
        EvaluacionFormal.objects.create(momento=self.momento, nombre='Trabajo', tipo='tarea', tarea=self.tarea, **pasado)

        def intento(est, ev, marcadas, **extra):
            respuestas = {str(q.id): m for q, m in zip(self.q[ev.id], marcadas) if m is not None}
            aciertos = sum(1 for q, m in zip(self.q[ev.id], marcadas) if m == 0)
            total = len(self.q[ev.id])
            return IntentoEvaluacion.objects.create(
                evaluacion=ev, estudiante=est, vence_en=ahora - timedelta(days=1), respuestas=respuestas,
                enviado_en=ahora - timedelta(days=1), aciertos=aciertos, total=total,
                nota=(Decimal(5) * aciertos / total).quantize(Decimal('0.01')), **extra)

        intento(self.e['ana'], self.e1, [0, 1])
        intento(self.e['ana'], self.e2, [0, 0, 0])
        intento(self.e['beto'], self.e1, [0, 0])
        intento(self.e['eli'], self.e1, [0, 0], integridad='anulado_fraude')
        intento(self.e['eli'], self.e2, [0, 0, None])
        for ev in (self.e1, self.e2):
            AsistenciaEvaluacion.objects.create(evaluacion=ev, estudiante=self.e['caro'], estado='ausente')
            AsistenciaEvaluacion.objects.create(evaluacion=ev, estudiante=self.e['dani'], estado='excusa',
                                                tipo_excusa='permiso_medico')
        EntregaTarea.objects.create(tarea=self.tarea, estudiante=self.e['ana'], archivo='x.pdf', nombre_original='x.pdf',
                                    tamano=1, nota=Decimal('4.50'))
        self.cliente = APIClient()
        self.coord = _u('coord@t.co', 'Coordinador')
        self.cliente.force_authenticate(self.coord)

    def datos(self):
        r = self.cliente.get(f'{URL}{self.momento.id}/')
        self.assertEqual(r.status_code, 200)
        return {f['correo'].split('@')[0]: f for f in r.data['filas']}, r.data

    def ponderar(self, pe, pt):
        return self.cliente.put(f'{URL}{self.momento.id}/esquema/', {'peso_examen': pe, 'peso_trabajo': pt}, format='json')


class PruebasCalculo(BaseNotas):
    def test_examen_desde_respuestas_reales(self):
        f, d = self.datos()
        ana = f['ana']['examen']
        self.assertEqual((ana['nota'], ana['correctas'], ana['incorrectas'], ana['sin_responder'], ana['total'],
                          ana['porcentaje'], ana['nivel']), (4.0, 4, 1, 0, 5, 80.0, 'alto'))
        eli = f['eli']['examen']  # E1 anulado: el examen queda anulado, sin nota
        self.assertEqual((eli['estado'], eli['nota']), ('anulado', None))
        self.assertEqual(d['evaluaciones'][0]['preguntas'], 2)

    def test_estados_sin_nota_ficticia(self):
        f, _d = self.datos()
        esperado = {'beto': 'incompleto', 'caro': 'ausente', 'dani': 'excusa', 'fer': 'no_presento'}
        for n, estado in esperado.items():
            with self.subTest(n=n):
                self.assertEqual(f[n]['examen']['estado'], estado)
                self.assertIsNone(f[n]['examen']['nota'])
                self.assertIsNone(f[n]['momento']['nota'])
        self.assertEqual(f['beto']['examen']['estado_texto'], 'Presentó parcialmente (1 de 2 partes)')
        self.assertEqual(f['dani']['examen']['tipo_excusa'], 'permiso_medico')

    def test_nota_reglamentaria_solo_sin_excusa(self):
        self.ponderar(70, 30)
        f, _d = self.datos()
        # beto: examen 2/5 → 2,0 (falta E2 sin excusa = 0); trabajo no entregado = 0 → 0,7×2,0 = 1,4
        self.assertEqual(f['beto']['momento']['nota_reglamentaria'], 1.4)
        self.assertEqual(f['caro']['momento']['nota_reglamentaria'], 0.0)
        self.assertEqual(f['fer']['momento']['nota_reglamentaria'], 0.0)
        self.assertIsNone(f['dani']['momento']['nota_reglamentaria'])  # con excusa: no se determina
        self.assertIsNone(f['eli']['momento']['nota_reglamentaria'])   # anulado: no se determina

    def test_consolidado_sin_ponderacion_queda_pendiente(self):
        f, d = self.datos()
        self.assertTrue(d['tiene_trabajo'])
        self.assertEqual(f['ana']['momento']['estado'], 'ponderacion_sin_definir')
        self.assertIsNone(f['ana']['momento']['nota'])
        self.assertTrue(d['provisional'])

    def test_consolidado_ponderado_y_aportes(self):
        self.assertEqual(self.ponderar(70, 30).status_code, 200)
        f, d = self.datos()
        mo = f['ana']['momento']
        # 0,7×4,0 + 0,3×4,5 = 4,15 → 4,2 (redondeo único) · Alto
        self.assertEqual((mo['nota'], mo['nivel'], mo['aprueba']), (4.2, 'alto', True))
        self.assertEqual((mo['aporte_tercer_corte'], mo['aporte_definitiva']), (1.26, 0.5))
        self.assertEqual((f['ana']['trabajo']['nota'], f['ana']['trabajo']['nivel']), (4.5, 'alto'))
        self.assertEqual(f['caro']['trabajo']['estado'], 'no_entrego')
        r = d['resumen']
        self.assertEqual((r['convocados'], r['examen']['presentaron'], r['examen']['con_excusa'],
                          r['examen']['anulados'], r['examen']['incompletos'], r['examen']['ausentes']),
                         (6, 1, 1, 1, 1, 2))
        # Indicadores solo con quien tiene nota del momento (ana): no se mezclan ausentes con ceros.
        self.assertEqual((r['momento']['con_nota'], r['momento']['promedio'], r['momento']['pct_aprobacion']),
                         (1, 4.2, 100.0))
        self.assertEqual(r['examen']['promedio'], 4.0)

    def test_sin_trabajo_el_momento_es_el_examen(self):
        EvaluacionFormal.objects.filter(tipo='tarea').delete()
        f, d = self.datos()
        self.assertFalse(d['tiene_trabajo'])
        self.assertEqual((f['ana']['momento']['nota'], f['ana']['trabajo']['estado']), (4.0, 'no_aplica'))

    def test_no_modifica_la_nota_de_los_intentos(self):
        antes = list(IntentoEvaluacion.objects.order_by('id').values_list('nota', flat=True))
        self.ponderar(70, 30)
        self.datos()
        self.cliente.get(f'{URL}{self.momento.id}/exportar/')
        self.assertEqual(list(IntentoEvaluacion.objects.order_by('id').values_list('nota', flat=True)), antes)


class PruebasEsquemaExcelPermisos(BaseNotas):
    def test_validacion_del_esquema(self):
        self.assertEqual(self.ponderar(70, 20).status_code, 400)
        self.assertEqual(self.ponderar(70, None).status_code, 400)
        self.assertEqual(self.ponderar(120, -20).status_code, 400)
        self.assertEqual(self.ponderar(60, 40).data['origen_peso_examen'], 'momento')
        inst = self.cliente.get(f'{URL}esquema-institucional/').data
        self.assertEqual((inst['peso_momento_en_corte'], inst['peso_corte_en_definitiva']), (30.0, 40.0))

    def test_excel_individual_igual_a_la_pantalla(self):
        from openpyxl import load_workbook

        self.ponderar(70, 30)
        f, _d = self.datos()
        r = self.cliente.get(f'{URL}{self.momento.id}/exportar/')
        self.assertEqual(r.status_code, 200)
        libro = load_workbook(BytesIO(r.content))
        self.assertEqual(libro.sheetnames, ['Resultados individuales', 'Resumen estadístico', 'Detalle del examen',
                                            'Metodología', 'Convenciones'])
        h = libro['Resultados individuales']
        cab = [c.value for c in h[6]]
        filas = {h.cell(row=i, column=3).value.split('@')[0]: [c.value for c in h[i]] for i in range(7, 13)}
        col = {n: cab.index(n) for n in cab}
        self.assertEqual(filas['ana'][col['Examen: nota']], 4.0)
        self.assertEqual(filas['ana'][col['Correctas']], 4)
        self.assertEqual(filas['ana'][col['Consolidado del momento']], f['ana']['momento']['nota'])
        self.assertIsNone(filas['caro'][col['Examen: nota']])  # vacía, nunca 0
        self.assertEqual(filas['caro'][col['Estado examen']], 'Ausente')
        self.assertEqual(filas['caro'][col['Nota reglamentaria a reportar']], 0.0)
        self.assertEqual(h.freeze_panes, 'C7')
        self.assertTrue(h.auto_filter.ref.startswith('A6:'))
        self.assertIn('Ley 1581', h['A4'].value)
        self.assertEqual(len(libro['Detalle del examen']['A']) - 6, 12)  # 6 estudiantes × 2 cuestionarios
        self.assertTrue(RegistroSincronizacion.objects.filter(entidad='exportacion_notas', ejecutado_por=self.coord).exists())

    def test_permisos(self):
        for rol, lectura, esquema in (('Vicerrector', 200, 403), ('Administrador', 200, 200),
                                      ('Docente', 403, 403), ('Estudiante', 403, 403)):
            with self.subTest(rol=rol):
                self.cliente.force_authenticate(_u(f'{rol}@x.co', rol))
                self.assertEqual(self.cliente.get(f'{URL}{self.momento.id}/').status_code, lectura)
                self.assertEqual(self.cliente.get(f'{URL}{self.momento.id}/exportar/').status_code, lectura)
                self.assertEqual(self.cliente.get(f'{URL}momentos/').status_code, lectura)
                self.assertEqual(self.ponderar(50, 50).status_code, esquema)
        self.cliente.force_authenticate(self.coord)
        self.assertEqual(self.cliente.put(f'{URL}esquema-institucional/', {'peso_examen': 50, 'peso_trabajo': 50},
                                          format='json').status_code, 403)
        momentos = self.cliente.get(f'{URL}momentos/').data
        self.assertEqual([m['id'] for m in momentos], [self.momento.id])
