"""
Pruebas de la asignación masiva de docentes (ADR-017).

Escenario (programa P1):
- A1 con el curso C1 del docente D1; A2 y A3 sin curso; A4 inactiva.
- B1 en el programa P2.
- D1 tiene además el curso "Dos" (mismo nombre que A2); D2 no tiene cursos.
- E es un estudiante; X es un docente inactivo.
"""

import json
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.evaluacion_resultados.models import AsignaturaMalla, ProgramaAcademico
from apps.evaluacion_resultados.services.servicio_importador_nova import importar_programas_json
from apps.evaluacion_resultados.tests.test_analitica_ra import _usuario
from apps.examenes.models import Curso

URL = '/api/evaluacion/asignacion-docentes/'


def _csv(texto, nombre='asignaciones.csv'):
    return SimpleUploadedFile(nombre, texto.encode('utf-8'), content_type='text/csv')


class BaseAsignacion(TestCase):
    def setUp(self):
        self.p1 = ProgramaAcademico.objects.create(codigo='P1', nombre='Ingeniería')
        self.p2 = ProgramaAcademico.objects.create(codigo='P2', nombre='Derecho')
        self.d1 = _usuario('d1@t.co', 'Docente')
        self.d2 = _usuario('d2@t.co', 'Docente')
        self.est = _usuario('e@t.co', 'Estudiante')
        self.inactivo = _usuario('x@t.co', 'Docente')
        self.inactivo.is_active = False
        self.inactivo.save()
        self.c1 = Curso.objects.create(nombre='C1', docente=self.d1)
        self.c_dos = Curso.objects.create(nombre='Dos', docente=self.d1)
        self.a1 = AsignaturaMalla.objects.create(codigo='A1', nombre='Uno', programa=self.p1, curso_vinculado=self.c1)
        self.a2 = AsignaturaMalla.objects.create(codigo='A2', nombre='Dos', programa=self.p1)
        self.a3 = AsignaturaMalla.objects.create(codigo='A3', nombre='Tres', programa=self.p1)
        self.a4 = AsignaturaMalla.objects.create(codigo='A4', nombre='Cuatro', programa=self.p1, activo=False)
        self.b1 = AsignaturaMalla.objects.create(codigo='B1', nombre='Bé', programa=self.p2)
        self.cliente = APIClient()
        self.cliente.force_authenticate(_usuario('coord@t.co', 'Coordinador'))

    def analizar(self, archivo, programa=None):
        return self.cliente.post(URL + 'analizar/', {'archivo': archivo, 'programa': (programa or self.p1).id},
                                 format='multipart')


class PruebasAnalisis(BaseAsignacion):
    def test_estados_por_fila_sin_escribir(self):
        r = self.analizar(_csv(
            'asignatura_codigo;docente_email;curso_codigo\n'
            'A1;d1@t.co;\n'            # 2 ya asignada
            'a2;d1@t.co;\n'            # 3 válida: usa el curso "Dos" de D1 (mismo nombre)
            'A3;d2@t.co;\n'            # 4 advertencia: se creará un curso
            'A2;d2@t.co;\n'            # 5 error: repetida
            'B1;d1@t.co;\n'            # 6 error: otro programa
            'A9;d1@t.co;\n'            # 7 error: no existe
            'A4;d1@t.co;\n'            # 8 error: inactiva
            ';d1@t.co;\n'              # 9 error: falta código
        ))
        self.assertEqual(r.status_code, 200)
        estados = {f['fila']: (f['estado'], f['mensaje']) for f in r.data['filas']}
        self.assertEqual(estados[2][0], 'ya_asignada')
        self.assertEqual(estados[3][0], 'valida')
        self.assertEqual(r.data['filas'][1]['curso']['codigo'], self.c_dos.codigo)
        self.assertEqual(estados[4][0], 'advertencia')
        self.assertIn('se creará el curso "Tres"', estados[4][1])
        self.assertIn('repetida', estados[5][1])
        self.assertIn('pertenece al programa P2', estados[6][1])
        self.assertIn('No existe la asignatura', estados[7][1])
        self.assertIn('inactiva', estados[8][1])
        self.assertIn('Falta el código', estados[9][1])
        self.assertEqual(r.data['resumen']['error'], 5)
        self.assertEqual(r.data['resumen']['cursos_nuevos'], 1)
        # Vista previa: no escribe nada.
        self.a2.refresh_from_db()
        self.assertIsNone(self.a2.curso_vinculado)
        self.assertEqual(Curso.objects.count(), 2)

    def test_validaciones_del_docente_y_curso(self):
        otro = Curso.objects.create(nombre='Otro', docente=self.d2)
        r = self.analizar(_csv(
            'asignatura_codigo,docente_email,curso_codigo\n'
            'A1,no-es-correo,\n'
            'A2,nadie@t.co,\n'
            'A3,e@t.co,\n'
            'A1,x@t.co,\n'  # repetida (A1 ya apareció) se evalúa antes que el docente
        ))
        mensajes = [f['mensaje'] for f in r.data['filas']]
        self.assertIn('Correo inválido', mensajes[0])
        self.assertIn('No existe un usuario', mensajes[1])
        self.assertIn('no tiene el rol Docente', mensajes[2])
        r = self.analizar(_csv(f'asignatura_codigo,docente_email,curso_codigo\nA2,x@t.co,\nA3,d1@t.co,{otro.codigo}\n'
                               'A1,d1@t.co,ZZZ\n'))
        mensajes = [f['mensaje'] for f in r.data['filas']]
        self.assertIn('inactiva', mensajes[0])
        self.assertIn('pertenece a d2@t.co', mensajes[1])
        self.assertIn('No existe el curso', mensajes[2])

    def test_cambio_de_docente_es_advertencia(self):
        r = self.analizar(_csv('asignatura_codigo,docente_email\nA1,d2@t.co\n'))
        fila = r.data['filas'][0]
        self.assertEqual(fila['estado'], 'advertencia')
        self.assertIn('Reemplaza a', fila['mensaje'])
        self.assertEqual(fila['anterior']['docente_email'], 'd1@t.co')
        self.assertEqual(r.data['resumen']['cambios_docente'], 1)

    def test_estructura_formatos_y_omitidas(self):
        r = self.analizar(_csv('codigo;otra\nA1;x\n'))
        self.assertEqual(r.status_code, 400)
        self.assertIn('faltan las columnas docente_email', r.data['detalle'])
        r = self.analizar(SimpleUploadedFile('a.pdf', b'%PDF'))
        self.assertEqual(r.status_code, 400)
        # Plantilla con docente vacío: la fila se omite (no cambia la asignatura).
        r = self.analizar(_csv('asignatura_codigo,asignatura_nombre,docente_email\nA3,Tres,\n'))
        self.assertEqual(r.data['filas'][0]['estado'], 'omitida')
        # JSON.
        datos = json.dumps({'asignaciones': [{'asignatura_codigo': 'A3', 'docente_email': 'd1@t.co'}, 'x']})
        r = self.analizar(SimpleUploadedFile('a.json', datos.encode('utf-8')))
        self.assertEqual([f['estado'] for f in r.data['filas']], ['advertencia', 'error'])
        # Excel.
        from openpyxl import Workbook

        libro = Workbook()
        libro.active.append(['Código asignatura', 'Correo docente'])
        libro.active.append(['A3', 'd2@t.co'])
        salida = BytesIO()
        libro.save(salida)
        r = self.analizar(SimpleUploadedFile('a.xlsx', salida.getvalue()))
        self.assertEqual(r.data['filas'][0]['estado'], 'advertencia')


class PruebasConfirmar(BaseAsignacion):
    def _confirmar(self, analisis, **cambios):
        cuerpo = {'programa': self.p1.id, 'filas': analisis['entrada'], 'huella': analisis['huella'], **cambios}
        return self.cliente.post(URL + 'confirmar/', cuerpo, format='json')

    def test_aplica_validas_y_advertencias_sin_duplicar(self):
        a = self.analizar(_csv('asignatura_codigo,docente_email\nA1,d1@t.co\nA2,d1@t.co\nA3,d2@t.co\nA9,d1@t.co\n')).data
        r = self._confirmar(a)
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.data['resumen']['asignadas'], r.data['resumen']['cursos_creados']), (2, 1))
        self.a2.refresh_from_db()
        self.a3.refresh_from_db()
        self.assertEqual(self.a2.curso_vinculado, self.c_dos)
        self.assertEqual((self.a3.curso_vinculado.docente, self.a3.curso_vinculado.nombre), (self.d2, 'Tres'))
        # Repetir el mismo archivo no duplica cursos ni cambia nada.
        a = self.analizar(_csv('asignatura_codigo,docente_email\nA1,d1@t.co\nA2,d1@t.co\nA3,d2@t.co\n')).data
        self.assertEqual(a['resumen']['ya_asignada'], 3)
        self.assertEqual(self._confirmar(a).data['resumen']['asignadas'], 0)
        self.assertEqual(Curso.objects.filter(nombre='Tres').count(), 1)
        # Trazabilidad.
        from apps.evaluacion_resultados.models import RegistroSincronizacion

        self.assertTrue(RegistroSincronizacion.objects.filter(entidad='asignacion_docentes').exists())

    def test_mismo_docente_misma_asignatura_nombre_crea_un_curso(self):
        AsignaturaMalla.objects.create(codigo='A5', nombre='Tres', programa=self.p1)
        a = self.analizar(_csv('asignatura_codigo,docente_email\nA3,d2@t.co\nA5,d2@t.co\n')).data
        self.assertIn('se crea en otra fila', a['filas'][1]['mensaje'])
        self._confirmar(a)
        self.assertEqual(Curso.objects.filter(docente=self.d2).count(), 1)

    def test_huella_y_transaccion(self):
        a = self.analizar(_csv('asignatura_codigo,docente_email\nA3,d2@t.co\n')).data
        a['entrada'][0]['docente_email'] = 'd1@t.co'
        self.assertEqual(self._confirmar(a).status_code, 409)
        self.a3.refresh_from_db()
        self.assertIsNone(self.a3.curso_vinculado)
        # Si una escritura falla, no queda nada a medias.
        from unittest import mock

        a = self.analizar(_csv('asignatura_codigo,docente_email\nA2,d1@t.co\nA3,d2@t.co\n')).data
        original = AsignaturaMalla.save

        def fallar(self_, *args, **kwargs):
            if self_.codigo == 'A3':
                raise RuntimeError('fallo simulado')
            return original(self_, *args, **kwargs)

        cliente = APIClient()
        cliente.force_authenticate(_usuario('adm@t.co', 'Administrador'))
        with mock.patch.object(AsignaturaMalla, 'save', fallar):
            r = cliente.post(URL + 'confirmar/', {'programa': self.p1.id, 'filas': a['entrada'], 'huella': a['huella']},
                             format='json')
        self.assertEqual(r.status_code, 500)
        self.assertIn('No se guardó ningún cambio', r.data['detalle'])
        self.a2.refresh_from_db()
        self.assertIsNone(self.a2.curso_vinculado)
        self.assertFalse(Curso.objects.filter(nombre='Tres').exists())


class PruebasPlantillaYPermisos(BaseAsignacion):
    def test_plantilla_con_asignaturas_y_docente_actual(self):
        r = self.cliente.get(URL + 'plantilla/', {'programa': self.p1.id, 'formato': 'csv'})
        self.assertEqual(r.status_code, 200)
        lineas = r.content.decode('utf-8-sig').splitlines()
        self.assertEqual(lineas[0], 'asignatura_codigo,asignatura_nombre,semestre,docente_email,curso_codigo,docente_actual')
        self.assertTrue(any(l.startswith(f'A1,Uno,,d1@t.co,{self.c1.codigo},') for l in lineas))
        self.assertFalse(any(l.startswith('A4') or l.startswith('B1') for l in lineas))  # inactiva / otro programa
        from openpyxl import load_workbook

        r = self.cliente.get(URL + 'plantilla/', {'programa': self.p1.id, 'formato': 'xlsx'})
        libro = load_workbook(BytesIO(r.content))
        self.assertEqual(libro.sheetnames, ['Asignaciones', 'Docentes', 'Instrucciones'])
        correos = [c.value for c in libro['Docentes']['A'][1:]]
        self.assertEqual(correos, ['d1@t.co', 'd2@t.co'])  # solo docentes activos
        # La plantilla descargada se puede subir tal cual: filas con docente → ya asignada, sin docente → omitida.
        a = self.analizar(SimpleUploadedFile('p.xlsx', r.content)).data
        self.assertEqual({f['asignatura_codigo']: f['estado'] for f in a['filas']},
                         {'A1': 'ya_asignada', 'A2': 'omitida', 'A3': 'omitida'})

    def test_permisos(self):
        for rol in ('Docente', 'Estudiante', 'Vicerrector'):
            self.cliente.force_authenticate(_usuario(f'{rol}@t.co', rol))
            with self.subTest(rol=rol):
                self.assertEqual(self.cliente.get(URL + 'plantilla/', {'programa': self.p1.id}).status_code, 403)
                self.assertEqual(self.analizar(_csv('asignatura_codigo,docente_email\nA3,d1@t.co\n')).status_code, 403)
                self.assertEqual(self.cliente.post(URL + 'confirmar/', {}, format='json').status_code, 403)
        self.cliente.force_authenticate(_usuario('adm2@t.co', 'Administrador'))
        self.assertEqual(self.cliente.get(URL + 'plantilla/', {'programa': self.p1.id}).status_code, 200)
        self.assertEqual(self.cliente.get(URL + 'plantilla/').status_code, 400)


class PruebasImportadorPensum(BaseAsignacion):
    def test_campos_opcionales_de_docente(self):
        lote = {'asignaturas': [
            {'codigo': 'A2', 'nombre': 'Dos', 'programa_codigo': 'P1', 'docente_email': 'd1@t.co'},
            {'codigo': 'N1', 'nombre': 'Nueva', 'programa_codigo': 'P1', 'docente_email': 'd2@t.co'},
            {'codigo': 'A3', 'nombre': 'Tres', 'programa_codigo': 'P1', 'docente_email': 'nadie@t.co'},
            {'codigo': 'N2', 'nombre': 'Sin docente', 'programa_codigo': 'P1'},
        ]}
        previa = importar_programas_json(lote, modo='simulacro')
        docentes = {f['clave']: f for f in previa['registros'] if f['entidad'] == 'docente'}
        self.assertEqual(docentes['A2']['accion'], 'actualizar')
        self.assertIn('se creará el curso "Nueva"', docentes['N1']['motivo'])
        self.assertEqual(docentes['A3']['accion'], 'rechazar')
        self.assertNotIn('N2', docentes)
        # El docente inválido no rechaza la asignatura.
        self.assertIn(('asignatura', 'A3', 'actualizar'),
                      [(f['entidad'], f['clave'], f['accion']) for f in previa['registros']])
        self.assertIsNone(AsignaturaMalla.objects.get(codigo='A2').curso_vinculado)

        importar_programas_json(lote, modo='real', huella_esperada=previa['huella'])
        self.assertEqual(AsignaturaMalla.objects.get(codigo='A2').curso_vinculado, self.c_dos)
        n1 = AsignaturaMalla.objects.get(codigo='N1')
        self.assertEqual((n1.curso_vinculado.docente, n1.curso_vinculado.nombre), (self.d2, 'Nueva'))
        self.assertIsNone(AsignaturaMalla.objects.get(codigo='A3').curso_vinculado)
        self.assertIsNone(AsignaturaMalla.objects.get(codigo='N2').curso_vinculado)
        # Idempotente: la segunda vez no crea cursos.
        segunda = importar_programas_json(lote, modo='real')
        self.assertEqual(Curso.objects.filter(nombre='Nueva').count(), 1)
        self.assertEqual({f['clave']: f['accion'] for f in segunda['registros'] if f['entidad'] == 'docente'}['N1'],
                         'sin_cambios')
