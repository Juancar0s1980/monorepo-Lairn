"""
Pruebas de supervisión en sala, asistencia, seguimiento en vivo y cargue
masivo de convocados (ADR-009).
"""

from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    AsistenciaEvaluacion,
    Competencia,
    ConvocadoEvaluacion,
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

API = '/api/evaluacion'
EST = f'{API}/estudiante/evaluaciones'
DOC = f'{API}/docente/supervision'


def _usuario(email, rol, nombre='N'):
    return User.objects.create_user(
        email=email, password='x', first_name=nombre, first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


class BaseSupervision(TestCase):
    def setUp(self):
        self.ahora = timezone.now()
        self.coordinador = _usuario('coord@t.co', 'Coordinador')
        self.docente = _usuario('doc@t.co', 'Docente')            # dueño del curso: supervisor válido
        self.otro_docente = _usuario('doc2@t.co', 'Docente')
        Curso.objects.create(nombre='Otro curso', docente=self.otro_docente)
        self.docente_sin_cursos = _usuario('doc3@t.co', 'Docente')
        self.estudiante = _usuario('est@t.co', 'Estudiante', 'Ana')
        self.estudiante2 = _usuario('est2@t.co', 'Estudiante', 'Beto')
        self.externo = _usuario('ext@t.co', 'Estudiante', 'Ciro')  # no inscrito: llega por cargue
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        curso = Curso.objects.create(nombre='Curso', docente=self.docente)
        for e in (self.estudiante, self.estudiante2):
            Inscripcion.objects.create(estudiante=e, curso=curso)
        asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=programa, curso_vinculado=curso)
        comp = Competencia.objects.create(programa=programa, nombre='C', tipo='especifica')
        ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=asignatura, descripcion='RA')
        momento = MomentoEvaluacion.objects.create(programa=programa, semestre_referencia=4, nombre='M1')
        self.evaluacion = EvaluacionFormal.objects.create(
            momento=momento, nombre='Eval', fecha_inicio=self.ahora - timedelta(minutes=5),
            fecha_fin=self.ahora + timedelta(hours=2), duracion_minutos=30, estado='publicada',
        )
        self.pregunta = PreguntaBanco.objects.create(
            asignatura=asignatura, resultado=ra, enunciado='P', opciones=['a', 'b'],
            respuesta_correcta=0, estado='aprobada',
        )
        EvaluacionPregunta.objects.create(evaluacion=self.evaluacion, pregunta=self.pregunta, orden=0)
        self.cliente = APIClient()
        self.eid = self.evaluacion.id

    def como(self, usuario):
        self.cliente.force_authenticate(usuario)
        return self.cliente

    def asignar(self, supervisor_id):
        return self.como(self.coordinador).patch(
            f'{API}/evaluaciones/{self.eid}/supervisor/', {'supervisor': supervisor_id}, format='json',
        )

    def marcar(self, estudiante, estado, **extra):
        return self.como(self.docente).put(
            f'{DOC}/{self.eid}/asistencia/', {'estudiante': estudiante.id, 'estado': estado, **extra}, format='json',
        )


class PruebasAsignacionSupervisor(BaseSupervision):
    def test_disponibles_solo_docentes_con_cursos(self):
        datos = self.como(self.coordinador).get(f'{API}/supervisores-disponibles/').data
        self.assertEqual({d['email'] for d in datos}, {'doc@t.co', 'doc2@t.co'})

    def test_asignar_publicada_y_validaciones(self):
        r = self.asignar(self.docente.id)
        self.assertEqual(r.status_code, 200)  # publicada: se permite igual
        self.assertEqual(r.data['supervisor'], self.docente.id)
        self.assertTrue(r.data['supervisor_nombre'])
        self.assertEqual(self.asignar(self.docente_sin_cursos.id).status_code, 400)
        self.assertEqual(self.asignar(self.estudiante.id).status_code, 400)
        self.assertEqual(self.asignar(None).data['supervisor'], None)
        # El supervisor no se cambia por el PATCH del detalle (solo lectura).
        self.como(self.coordinador).patch(f'{API}/evaluaciones/{self.eid}/', {'supervisor': self.docente.id}, format='json')
        self.assertIsNone(EvaluacionFormal.objects.get().supervisor_id)

    def test_no_tarea_ni_cerrada(self):
        EvaluacionFormal.objects.filter(pk=self.eid).update(fecha_fin=self.ahora - timedelta(minutes=1))
        self.assertEqual(self.asignar(self.docente.id).status_code, 400)
        EvaluacionFormal.objects.filter(pk=self.eid).update(fecha_fin=self.ahora + timedelta(hours=1), tipo='tarea')
        self.assertEqual(self.asignar(self.docente.id).status_code, 400)

    def test_solo_gestores(self):
        self.assertEqual(self.como(self.docente).get(f'{API}/supervisores-disponibles/').status_code, 403)
        self.assertEqual(self.como(self.estudiante).get(f'{API}/evaluaciones/{self.eid}/seguimiento/').status_code, 403)


class PruebasBloqueoAsistencia(BaseSupervision):
    def test_sin_supervisor_sigue_igual(self):
        r = self.como(self.estudiante).get(f'{EST}/{self.eid}/')
        self.assertFalse(r.data['requiere_asistencia'])
        self.assertIsNone(r.data['asistencia'])
        self.assertEqual(self.cliente.post(f'{EST}/{self.eid}/iniciar/').status_code, 201)

    def test_bloqueo_hasta_presente(self):
        self.asignar(self.docente.id)
        r = self.como(self.estudiante).get(f'{EST}/{self.eid}/')
        self.assertTrue(r.data['requiere_asistencia'])
        self.assertEqual(r.data['asistencia'], 'pendiente')
        bloqueo = self.cliente.post(f'{EST}/{self.eid}/iniciar/')
        self.assertEqual(bloqueo.status_code, 403)
        self.assertIn('docente supervisor', bloqueo.data['detalle'])
        self.assertEqual(self.marcar(self.estudiante, 'presente').status_code, 200)
        self.assertEqual(self.como(self.estudiante).post(f'{EST}/{self.eid}/iniciar/').status_code, 201)

    def test_tarde_habilita_y_no_reduce_duracion(self):
        self.asignar(self.docente.id)
        self.marcar(self.estudiante, 'tarde')
        self.assertEqual(self.como(self.estudiante).post(f'{EST}/{self.eid}/iniciar/').status_code, 201)
        intento = IntentoEvaluacion.objects.get()
        self.assertAlmostEqual((intento.vence_en - intento.iniciado_en).total_seconds(), 1800, delta=2)
        self.assertIsNotNone(AsistenciaEvaluacion.objects.get().llegada_en)

    def test_ausente_y_excusa_no_habilitan(self):
        self.asignar(self.docente.id)
        self.marcar(self.estudiante, 'ausente')
        self.assertEqual(self.como(self.estudiante).post(f'{EST}/{self.eid}/iniciar/').status_code, 403)
        self.assertEqual(self.cliente.get(f'{EST}/{self.eid}/').data['asistencia'], 'ausente')

    def test_excusa_exige_tipo(self):
        self.asignar(self.docente.id)
        self.assertEqual(self.marcar(self.estudiante, 'excusa').status_code, 400)
        r = self.marcar(self.estudiante, 'excusa', tipo_excusa='permiso_medico', observacion='Incapacidad EPS')
        self.assertEqual(r.status_code, 200)
        registro = AsistenciaEvaluacion.objects.get()
        self.assertEqual((registro.tipo_excusa, registro.observacion), ('permiso_medico', 'Incapacidad EPS'))

    def test_no_ausentar_a_quien_inicio(self):
        self.asignar(self.docente.id)
        self.marcar(self.estudiante, 'presente')
        self.como(self.estudiante).post(f'{EST}/{self.eid}/iniciar/')
        self.assertEqual(self.marcar(self.estudiante, 'ausente').status_code, 409)
        self.assertEqual(self.marcar(self.estudiante, 'excusa', tipo_excusa='otra').status_code, 409)
        self.assertEqual(self.marcar(self.estudiante, 'tarde').status_code, 200)

    def test_no_convocado_y_ventana(self):
        self.asignar(self.docente.id)
        self.assertEqual(self.marcar(self.externo, 'presente').status_code, 400)
        EvaluacionFormal.objects.filter(pk=self.eid).update(
            fecha_inicio=self.ahora + timedelta(hours=3), fecha_fin=self.ahora + timedelta(hours=5),
        )
        self.assertEqual(self.marcar(self.estudiante, 'presente').status_code, 400)  # aún falta > 2 h

    def test_solo_supervisor_asignado(self):
        self.asignar(self.docente.id)
        self.assertEqual(self.como(self.otro_docente).get(f'{DOC}/{self.eid}/').status_code, 404)
        r = self.como(self.otro_docente).put(
            f'{DOC}/{self.eid}/asistencia/', {'estudiante': self.estudiante.id, 'estado': 'presente'}, format='json',
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.como(self.otro_docente).get(f'{DOC}/').data, [])
        self.assertEqual([e['id'] for e in self.como(self.docente).get(f'{DOC}/').data], [self.eid])

    def test_masiva(self):
        self.asignar(self.docente.id)
        r = self.como(self.docente).put(
            f'{DOC}/{self.eid}/asistencia/masiva/',
            {'estudiantes': [self.estudiante.id, self.estudiante2.id], 'estado': 'presente'}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(AsistenciaEvaluacion.objects.filter(estado='presente').count(), 2)
        r = self.cliente.put(f'{DOC}/{self.eid}/asistencia/masiva/',
                             {'estudiantes': [self.externo.id], 'estado': 'presente'}, format='json')
        self.assertEqual(r.status_code, 400)


class PruebasCargueOpcional(BaseSupervision):
    def test_publicar_e_iniciar_sin_cargue(self):
        # El cargue masivo es opcional: sin él se publica y los inscritos por curso presentan.
        EvaluacionFormal.objects.filter(pk=self.eid).update(estado='borrador')
        r = self.como(self.coordinador).post(f'{API}/evaluaciones/{self.eid}/publicar/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ConvocadoEvaluacion.objects.count(), 0)
        self.asignar(self.docente.id)
        self.marcar(self.estudiante, 'presente')
        self.assertEqual(self.como(self.estudiante).post(f'{EST}/{self.eid}/iniciar/').status_code, 201)


class PruebasSeguimiento(BaseSupervision):
    def test_conteos_y_nota_solo_coordinador(self):
        self.asignar(self.docente.id)
        self.marcar(self.estudiante, 'presente')
        self.marcar(self.estudiante2, 'excusa', tipo_excusa='calamidad')
        est = self.como(self.estudiante)
        est.post(f'{EST}/{self.eid}/iniciar/')
        est.put(f'{EST}/{self.eid}/respuestas/', {'pregunta': self.pregunta.id, 'opcion': 0}, format='json')
        est.post(f'{EST}/{self.eid}/enviar/')

        datos = self.como(self.coordinador).get(f'{API}/evaluaciones/{self.eid}/seguimiento/').data
        self.assertIn('ahora_servidor', datos)
        c = datos['conteos']
        self.assertEqual(
            (c['convocados'], c['presentes'], c['excusa'], c['sin_llamar'], c['enviados'], c['sin_iniciar'], c['en_curso']),
            (2, 1, 1, 0, 1, 1, 0),
        )
        fila = next(f for f in datos['filas'] if f['estudiante'] == self.estudiante.id)
        self.assertEqual(fila['origen'], 'curso')
        self.assertEqual(fila['intento']['nota'], Decimal('5.00'))

        docente = self.como(self.docente).get(f'{DOC}/{self.eid}/').data
        fila = next(f for f in docente['filas'] if f['estudiante'] == self.estudiante.id)
        self.assertNotIn('nota', fila['intento'])
        self.assertEqual(fila['intento']['respondidas'], 1)


class PruebasCargueConvocados(BaseSupervision):
    def cargar(self, contenido, confirmar=False, nombre='lista.csv'):
        archivo = SimpleUploadedFile(nombre, contenido.encode('utf-8'), content_type='text/csv')
        return self.como(self.coordinador).post(
            f'{API}/evaluaciones/{self.eid}/convocados/cargue/',
            {'archivo': archivo, 'confirmar': 'true' if confirmar else 'false'}, format='multipart',
        )

    def test_previa_no_escribe_y_clasifica(self):
        _usuario('doc9@t.co', 'Docente')
        csv = 'nombre;correo\nC;EXT@t.co\nA;est@t.co\nX;nadie@t.co\nD;doc9@t.co\nC2;ext@t.co\nM;no-es-correo\n'
        r = self.cargar(csv)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ConvocadoEvaluacion.objects.count(), 0)
        estados = [f['estado'] for f in r.data['filas']]
        self.assertEqual(estados, ['agregar', 'ya_convocado', 'no_encontrado', 'no_es_estudiante',
                                   'duplicado_en_archivo', 'invalido'])
        self.assertEqual(r.data['filas'][1]['origen'], 'curso')
        self.assertEqual(r.data['totales']['agregar'], 1)

    def test_confirmar_agrega_solo_faltantes_y_ve_la_evaluacion(self):
        self.assertEqual(self.como(self.externo).get(f'{EST}/').data, [])
        r = self.cargar('correo\next@t.co\nest@t.co\n', confirmar=True)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['agregados'], 1)
        self.assertEqual(list(ConvocadoEvaluacion.objects.values_list('estudiante_id', flat=True)), [self.externo.id])
        # Repetir el cargue deja todo igual: ahora el externo figura como ya convocado por cargue.
        r = self.cargar('correo\next@t.co\nest@t.co\n', confirmar=True)
        self.assertEqual(r.data['agregados'], 0)
        self.assertEqual(r.data['filas'][0]['origen'], 'cargue')
        self.assertEqual(ConvocadoEvaluacion.objects.count(), 1)
        self.assertEqual([e['id'] for e in self.como(self.externo).get(f'{EST}/').data], [self.eid])
        datos = self.como(self.coordinador).get(f'{API}/evaluaciones/{self.eid}/seguimiento/').data
        self.assertEqual(datos['conteos']['convocados'], 3)

    def test_json_y_excel(self):
        r = self.como(self.coordinador).post(
            f'{API}/evaluaciones/{self.eid}/convocados/cargue/', {'correos': ['ext@t.co']}, format='json',
        )
        self.assertEqual(r.data['totales']['agregar'], 1)
        from io import BytesIO

        from openpyxl import Workbook
        libro = Workbook()
        hoja = libro.active
        hoja.append(['Email'])
        hoja.append(['ext@t.co'])
        buffer = BytesIO()
        libro.save(buffer)
        archivo = SimpleUploadedFile('lista.xlsx', buffer.getvalue())
        r = self.cliente.post(f'{API}/evaluaciones/{self.eid}/convocados/cargue/',
                              {'archivo': archivo, 'confirmar': 'true'}, format='multipart')
        self.assertEqual((r.status_code, r.data['agregados']), (201, 1))
        self.assertEqual(self.cargar('x', nombre='lista.pdf').status_code, 400)

    def test_quitar_convocado_por_cargue(self):
        self.cargar('ext@t.co\n', confirmar=True)
        url = f'{API}/evaluaciones/{self.eid}/convocados'
        self.assertEqual(self.cliente.delete(f'{url}/{self.estudiante.id}/').status_code, 404)  # es por curso
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=self.externo, vence_en=self.ahora)
        self.assertEqual(self.cliente.delete(f'{url}/{self.externo.id}/').status_code, 409)
        IntentoEvaluacion.objects.all().delete()
        self.assertEqual(self.cliente.delete(f'{url}/{self.externo.id}/').status_code, 204)
        self.assertEqual(ConvocadoEvaluacion.objects.count(), 0)
