"""
Pruebas de convocados, inscritos y cargue masivo ampliado (ADR-012).
Reutiliza el escenario de supervisión: docente con curso (est, est2 inscritos),
`externo` sin inscripción y una evaluación publicada `eid`.
"""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.evaluacion_resultados.models import (
    AsistenciaEvaluacion,
    ConvocadoEvaluacion,
    IntentoEvaluacion,
    PerfilAcademico,
    ProgramaAcademico,
)
from apps.evaluacion_resultados.tests.test_supervision import API, BaseSupervision, _usuario
from apps.examenes.models import Curso, Inscripcion

LISTA = f'{API}/estudiantes/'


class PruebasVistaPreviaAmpliada(BaseSupervision):
    def cargar(self, contenido, confirmar=False, nombre='lista.csv'):
        archivo = SimpleUploadedFile(nombre, contenido.encode('utf-8'), content_type='text/csv')
        return self.como(self.coordinador).post(
            f'{API}/evaluaciones/{self.eid}/convocados/cargue/',
            {'archivo': archivo, 'confirmar': 'true' if confirmar else 'false'}, format='multipart',
        )

    def test_columnas_opcionales_y_diferencias_sin_sobrescribir(self):
        programa = ProgramaAcademico.objects.get(codigo='P1')
        PerfilAcademico.objects.create(usuario=self.externo, codigo_matricula='2020-001', programa=programa,
                                       semestre_actual=3)
        csv = ('Correo;Nombre completo;Código estudiantil;Programa;Semestre\n'
               'ext@t.co;Otro Nombre;2020-999;P1;3\n'
               ';Sin Correo;123;P1;1\n')
        r = self.cargar(csv)
        self.assertEqual(r.status_code, 200)
        fila = r.data['filas'][0]
        self.assertEqual(fila['estado'], 'agregar')
        self.assertEqual(fila['archivo'], {'nombre': 'Otro Nombre', 'codigo': '2020-999', 'programa': 'P1', 'semestre': '3'})
        self.assertEqual(fila['sistema']['codigo'], '2020-001')
        self.assertEqual(sorted(fila['diferencias']), ['codigo', 'nombre'])  # programa y semestre coinciden
        self.assertEqual(r.data['filas'][1]['estado'], 'campo_obligatorio_faltante')
        self.assertEqual(r.data['con_diferencias'], 1)
        self.assertEqual(r.data['columnas'], ['codigo', 'nombre', 'programa', 'semestre'])
        # Confirmar agrega la convocatoria pero NO toca la cuenta ni el perfil.
        self.cargar(csv, confirmar=True)
        self.externo.refresh_from_db()
        self.assertEqual((self.externo.first_name, self.externo.perfil_academico.codigo_matricula), ('Ciro', '2020-001'))
        self.assertTrue(ConvocadoEvaluacion.objects.filter(estudiante=self.externo).exists())

    def test_json_con_filas(self):
        r = self.como(self.coordinador).post(
            f'{API}/evaluaciones/{self.eid}/convocados/cargue/',
            {'filas': [{'correo': 'ext@t.co', 'nombre': 'Ciro A'}, {'correo': ''}]}, format='json',
        )
        self.assertEqual([f['estado'] for f in r.data['filas']], ['agregar', 'campo_obligatorio_faltante'])
        self.assertEqual(r.data['filas'][0]['diferencias'], [])  # el nombre coincide con la cuenta

    def test_validacion_global_solo_administrador(self):
        cuerpo = {'correos': ['est@t.co', 'doc@t.co', 'nadie@t.co', 'malo', 'est@t.co']}
        r = self.como(_usuario('admin@t.co', 'Administrador')).post(f'{LISTA}validar/', cuerpo, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([f['estado'] for f in r.data['filas']],
                         ['existe', 'no_es_estudiante', 'no_encontrado', 'invalido', 'duplicado_en_archivo'])
        self.assertEqual(self.como(self.coordinador).post(f'{LISTA}validar/', cuerpo, format='json').status_code, 403)


class PruebasListado(BaseSupervision):
    def setUp(self):
        super().setUp()
        ConvocadoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=self.externo)
        AsistenciaEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=self.estudiante, estado='presente')
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=self.estudiante, vence_en=self.ahora,
                                         enviado_en=self.ahora)
        IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=self.estudiante2, vence_en=self.ahora,
                                         integridad='suspendido')

    def lista(self, usuario=None, **params):
        r = self.como(usuario or self.coordinador).get(LISTA, params)
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        return r.data

    def test_estados_y_conteos(self):
        datos = self.lista()
        self.assertEqual(datos['total'], 3)
        por_correo = {f['email']: set(f['estados']) for f in datos['filas']}
        self.assertEqual(por_correo['est@t.co'], {'inscrito', 'convocado_curso', 'presente', 'presento'})
        self.assertEqual(por_correo['est2@t.co'], {'inscrito', 'convocado_curso', 'suspendido', 'no_presento'})
        self.assertEqual(por_correo['ext@t.co'], {'convocado_cargue', 'no_presento'})
        c = datos['conteos']
        self.assertEqual((c['inscrito'], c['convocado_cargue'], c['presento'], c['suspendido']), (2, 1, 1, 1))

    def test_filtros_busqueda_y_paginacion(self):
        self.assertEqual([f['email'] for f in self.lista(estado='convocado_cargue')['filas']], ['ext@t.co'])
        self.assertEqual([f['email'] for f in self.lista(buscar='beto')['filas']], ['est2@t.co'])
        pagina = self.lista(tamano=2, pagina=2)
        self.assertEqual((pagina['total'], pagina['paginas'], pagina['pagina'], len(pagina['filas'])), (3, 2, 2, 1))
        detalle = self.lista(evaluacion=self.eid)
        fila = next(f for f in detalle['filas'] if f['email'] == 'est2@t.co')
        self.assertEqual(fila['en_evaluacion'], {'origen': 'curso', 'presente': False, 'intento': 'en_curso',
                                                 'integridad': 'suspendido'})
        self.assertEqual(self.como(self.coordinador).get(LISTA, {'estado': 'raro'}).status_code, 400)
        self.assertEqual(self.como(self.coordinador).get(LISTA, {'programa': 'x'}).status_code, 400)

    def test_exportacion_con_los_mismos_filtros(self):
        r = self.como(self.coordinador).get(LISTA, {'formato': 'csv', 'estado': 'inscrito'})
        texto = r.content.decode('utf-8-sig')
        self.assertIn('est@t.co', texto)
        self.assertNotIn('ext@t.co', texto)
        from openpyxl import load_workbook

        r = self.como(self.coordinador).get(LISTA, {'formato': 'xlsx', 'tamano': 1})
        hoja = load_workbook(BytesIO(r.content))['Estudiantes']
        self.assertEqual(hoja.max_row, 4)  # encabezado + las 3 filas (la exportación no pagina)

    def test_alcance_del_docente(self):
        datos = self.como(self.docente).get(f'{API}/docente/estudiantes/').data
        # Sin supervisión, el docente ve solo los inscritos de su curso (no el convocado por cargue).
        self.assertEqual({f['email'] for f in datos['filas']}, {'est@t.co', 'est2@t.co'})
        self.asignar(self.docente.id)
        datos = self.como(self.docente).get(f'{API}/docente/estudiantes/').data
        self.assertEqual({f['email'] for f in datos['filas']}, {'est@t.co', 'est2@t.co', 'ext@t.co'})
        otro = self.como(self.otro_docente).get(f'{API}/docente/estudiantes/').data
        self.assertEqual(otro['filas'], [])  # su curso no tiene inscritos; no supervisa nada

    def test_permisos(self):
        for rol in ('Vicerrector', 'Estudiante', 'Docente'):
            with self.subTest(rol=rol):
                self.assertEqual(self.como(_usuario(f'{rol}@x.co', rol)).get(LISTA).status_code, 403)
        self.assertEqual(self.como(self.coordinador).get(f'{API}/docente/estudiantes/').status_code, 403)
        self.assertEqual(self.como(_usuario('adm@x.co', 'Administrador')).get(LISTA).status_code, 200)

    def test_sin_consultas_n_mas_uno(self):
        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                self.como(self.coordinador).get(LISTA)
            return len(capturadas)

        antes = consultas()
        curso = Curso.objects.get(nombre='Curso')
        for i in range(6):
            e = _usuario(f'nuevo{i}@t.co', 'Estudiante')
            Inscripcion.objects.create(estudiante=e, curso=curso)
            IntentoEvaluacion.objects.create(evaluacion=self.evaluacion, estudiante=e, vence_en=self.ahora,
                                             enviado_en=self.ahora)
        self.assertEqual(consultas(), antes)
