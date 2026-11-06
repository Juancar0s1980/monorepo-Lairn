"""
Pruebas de tareas prácticas (HU-08A / HU-08B) y su uso en la evaluación
formal (HU-06.4). Los archivos se escriben en una carpeta temporal.
"""

import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    Competencia,
    EntregaTarea,
    MomentoEvaluacion,
    MomentoResultado,
    ProgramaAcademico,
    ResultadoAprendizaje,
    TareaPractica,
)
from apps.evaluacion_resultados.models.modelo_tarea import almacenamiento_privado
from apps.evaluacion_resultados.services.servicio_tareas import (
    ErrorRubrica,
    calcular_nota,
    rubrica_desde_resultado,
    validar_rubrica,
)
from apps.examenes.models import Curso, Inscripcion
from apps.users.models import Role, User

DOC = '/api/evaluacion/docente'
EST = '/api/evaluacion/estudiante'
RUBRICA = [
    {'criterio': 'Análisis', 'peso': 60, 'niveles': [{'nombre': 'Bajo', 'valor': 1}, {'nombre': 'Alto', 'valor': 5}]},
    {'criterio': 'Presentación', 'peso': 40, 'niveles': [{'nombre': 'Bajo', 'valor': 2}, {'nombre': 'Alto', 'valor': 4}]},
]


def _usuario(email, rol):
    return User.objects.create_user(
        email=email, password='x', first_name='N', first_last_name='A',
        role=Role.objects.get_or_create(name=rol)[0],
    )


def _pdf(nombre='entrega.pdf', tamano=10):
    return SimpleUploadedFile(nombre, b'%PDF' + b'0' * tamano, content_type='application/pdf')


class PruebasRubrica(TestCase):
    def test_pesos_deben_sumar_100(self):
        self.assertEqual(len(validar_rubrica(RUBRICA)), 2)
        with self.assertRaisesMessage(ErrorRubrica, 'suman 90'):
            validar_rubrica([{**RUBRICA[0], 'peso': 50}, RUBRICA[1]])

    def test_nota_ponderada(self):
        # 60% × 5 + 40% × 2 = 3.80
        self.assertEqual(calcular_nota(validar_rubrica(RUBRICA), [1, 0]), Decimal('3.80'))
        with self.assertRaises(ValueError):
            calcular_nota(RUBRICA, [1])

    def test_rubrica_desde_ra_reparte_niveles_y_pesos(self):
        ra = mock.Mock(criterios_rubrica=[{'criterio': 'A', 'niveles': 'bajo/básico/alto', 'peso': 30},
                                          {'criterio': 'B', 'niveles': 'bajo/alto', 'peso': 30}])
        rubrica = validar_rubrica(rubrica_desde_resultado(ra))
        self.assertEqual([n['valor'] for n in rubrica[0]['niveles']], [1.0, 3.0, 5.0])
        self.assertEqual(sum(c['peso'] for c in rubrica), 100)


class PruebasTareas(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for atributo in ('location', 'base_location'):
            parche = mock.patch.object(almacenamiento_privado, atributo, self.tmp)
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self.docente = _usuario('doc@t.co', 'Docente')
        self.estudiante = _usuario('est@t.co', 'Estudiante')
        self.ajeno = _usuario('ajeno@t.co', 'Estudiante')
        programa = ProgramaAcademico.objects.create(codigo='P1', nombre='Ing')
        curso = Curso.objects.create(nombre='Curso', docente=self.docente)
        Inscripcion.objects.create(estudiante=self.estudiante, curso=curso)
        self.asignatura = AsignaturaMalla.objects.create(codigo='A1', nombre='Asig', programa=programa, curso_vinculado=curso)
        comp = Competencia.objects.create(programa=programa, nombre='C', tipo='especifica')
        self.ra = ResultadoAprendizaje.objects.create(competencia=comp, asignatura=self.asignatura, descripcion='RA')
        self.momento = MomentoEvaluacion.objects.create(programa=programa, semestre_referencia=4, nombre='M1')
        MomentoResultado.objects.create(momento=self.momento, resultado=self.ra)
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.docente)

    def _crear(self, **extra):
        datos = {
            'asignatura': self.asignatura.id, 'resultado': self.ra.id, 'titulo': 'Informe',
            'descripcion': 'Entregar un informe en PDF.', 'formatos_permitidos': ['pdf'],
            'fecha_limite': (timezone.now() + timedelta(days=2)).isoformat(),
            'permite_tardias': False, 'rubrica': RUBRICA, **extra,
        }
        return self.cliente.post(f'{DOC}/tareas/', datos, format='json')

    def _publicada(self, **extra):
        tid = self._crear(**extra).data['id']
        r = self.cliente.post(f'{DOC}/tareas/{tid}/publicar/')
        self.assertEqual(r.status_code, 200, r.data)
        return tid

    def _entregar(self, tid, archivo=None, usuario=None):
        self.cliente.force_authenticate(usuario or self.estudiante)
        return self.cliente.post(f'{EST}/tareas/{tid}/entregar/', {'archivo': archivo or _pdf()}, format='multipart')

    def test_crear_y_publicar_valida_rubrica(self):
        self.assertEqual(self._crear(rubrica=[{**RUBRICA[0], 'peso': 10}, RUBRICA[1]]).status_code, 400)  # HU-08B.2
        tid = self._crear(formatos_permitidos=[]).data['id']
        self.assertEqual(self.cliente.post(f'{DOC}/tareas/{tid}/publicar/').status_code, 400)  # sin formatos
        self.assertEqual(self.cliente.get(f'{EST}/tareas/').status_code, 403)  # docente no es estudiante

    def test_borrador_no_es_visible_y_publicada_si(self):
        borrador = self._crear().data['id']
        publicada = self._publicada()
        self.cliente.force_authenticate(self.estudiante)
        ids = [t['id'] for t in self.cliente.get(f'{EST}/tareas/').data]
        self.assertEqual(ids, [publicada])  # HU-08A.1
        self.assertEqual(self.cliente.get(f'{EST}/tareas/{borrador}/').status_code, 404)
        self.cliente.force_authenticate(self.ajeno)  # no inscrito
        self.assertEqual(self.cliente.get(f'{EST}/tareas/').data, [])

    def test_entrega_definitiva_formato_y_unica(self):
        tid = self._publicada()
        self.assertEqual(self._entregar(tid, SimpleUploadedFile('x.exe', b'MZ')).status_code, 400)
        r = self._entregar(tid)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['mi_entrega']['estado'], 'a_tiempo')  # HU-08A.2
        self.assertEqual(self._entregar(tid).status_code, 409)  # sin reenvío
        self.assertEqual(self._entregar(tid, usuario=self.ajeno).status_code, 404)

    def test_plazo_vencido_segun_politica(self):
        cerrada = self._publicada(permite_tardias=False)
        tardia = self._publicada(permite_tardias=True)
        TareaPractica.objects.filter(id__in=[cerrada, tardia]).update(fecha_limite=timezone.now() - timedelta(hours=1))
        self.assertEqual(self._entregar(cerrada).status_code, 400)  # HU-08A.3 envío deshabilitado
        r = self._entregar(tardia)
        self.assertEqual(r.data['mi_entrega']['estado'], 'con_retraso')

    def test_panel_calificar_y_retroalimentacion(self):
        tid = self._publicada()
        self.cliente.force_authenticate(self.docente)
        panel = self.cliente.get(f'{DOC}/tareas/{tid}/entregas/').data
        self.assertEqual([f['estado'] for f in panel], ['sin_entregar'])  # HU-08B.3
        self._entregar(tid)
        self.cliente.force_authenticate(self.docente)
        entrega = EntregaTarea.objects.get()
        descarga = self.cliente.get(f'{DOC}/entregas/{entrega.id}/archivo/')
        self.assertEqual(descarga.status_code, 200)
        self.assertEqual(self.cliente.post(f'{DOC}/entregas/{entrega.id}/calificar/', {'niveles_elegidos': [1]}, format='json').status_code, 400)
        r = self.cliente.post(f'{DOC}/entregas/{entrega.id}/calificar/',
                              {'niveles_elegidos': [1, 0], 'observaciones': 'Buen análisis'}, format='json')
        self.assertEqual(r.data['entrega']['calificacion']['nota'], '3.80')  # HU-08B.4
        self.cliente.force_authenticate(self.estudiante)
        mia = self.cliente.get(f'{EST}/tareas/{tid}/').data['mi_entrega']['calificacion']
        self.assertEqual((mia['nota'], mia['observaciones']), ('3.80', 'Buen análisis'))  # HU-08A.4 / 08B.5

    def test_otro_docente_no_accede(self):
        tid = self._publicada()
        self.cliente.force_authenticate(_usuario('otro@t.co', 'Docente'))
        self.assertEqual(self.cliente.get(f'{DOC}/tareas/{tid}/').status_code, 404)
        self.assertEqual(self.cliente.get(f'{DOC}/tareas/{tid}/entregas/').status_code, 404)

    def test_generar_con_ia_usa_rubrica_del_ra(self):
        self.ra.criterios_rubrica = [{'criterio': 'Diseño', 'niveles': 'bajo/alto', 'peso': 100}]
        self.ra.save()
        respuesta = mock.Mock(content='{"titulo": "Caso", "descripcion": "Escenario y entregable"}')
        cliente_ia = mock.Mock()
        cliente_ia.chat.completions.create.return_value = mock.Mock(choices=[mock.Mock(message=respuesta)])
        with mock.patch('apps.evaluacion_resultados.services.agente_tareas.obtener_cliente_ia',
                        return_value=(cliente_ia, 'm', 'max_tokens')):
            r = self.cliente.post(f'{DOC}/tareas/generar/', {
                'asignatura': self.asignatura.id, 'resultado': self.ra.id,
                'fecha_limite': (timezone.now() + timedelta(days=1)).isoformat(),
            }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual((r.data['origen'], r.data['estado']), ('ia', 'borrador'))
        self.assertEqual(r.data['rubrica'][0]['criterio'], 'Diseño')

    def test_evaluacion_formal_por_tarea(self):
        tid = self._publicada()
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))
        ahora = timezone.now()
        base = {'nombre': 'Eval', 'fecha_inicio': (ahora + timedelta(days=1)).isoformat(),
                'fecha_fin': (ahora + timedelta(days=2)).isoformat(), 'duracion_minutos': 60}
        url = f'/api/evaluacion/momentos/{self.momento.id}/evaluaciones/'
        self.assertEqual(self.cliente.post(url, {**base, 'tipo': 'tarea'}, format='json').status_code, 400)
        r = self.cliente.post(url, {**base, 'tipo': 'tarea', 'tarea': tid}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['cobertura'][0]['preguntas'], 1)
        publicada = self.cliente.post(f'/api/evaluacion/evaluaciones/{r.data["id"]}/publicar/')
        self.assertEqual(publicada.data['estado'], 'publicada')
