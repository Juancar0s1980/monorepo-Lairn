"""
Pruebas de integridad académica en la presentación (ADR-010): incidentes,
advertencia, suspensión con tiempo congelado y decisión del docente.
El reloj se mueve con `mock.patch` para simular el paso del tiempo.
"""

from datetime import timedelta
from unittest import mock

from django.utils import timezone

from apps.evaluacion_resultados.models import (
    EvaluacionFormal,
    IncidenteIntento,
    IntentoEvaluacion,
    ResolucionIntegridad,
)
from apps.evaluacion_resultados.tests.test_supervision import API, DOC, EST, BaseSupervision

RELOJ = 'django.utils.timezone.now'


class BaseIntegridad(BaseSupervision):
    def setUp(self):
        super().setUp()
        self.est = self.como(self.estudiante)
        self.assertEqual(self.est.post(f'{EST}/{self.eid}/iniciar/').status_code, 201)
        self.intento = IntentoEvaluacion.objects.get()

    def incidente(self, tipo='cambio_pestana', segundos=0):
        cliente = self.como(self.estudiante)
        with mock.patch(RELOJ, return_value=timezone.now() + timedelta(seconds=segundos)):
            return cliente.post(f'{EST}/{self.eid}/incidentes/', {'tipo': tipo}, format='json')

    def suspender(self):
        self.incidente('copiar')
        return self.incidente('cambio_pestana', segundos=5)

    def resolver_gestor(self, accion, motivo='Revisado en sala'):
        return self.como(self.coordinador).post(
            f'{API}/evaluaciones/{self.eid}/intentos/{self.estudiante.id}/resolver/',
            {'accion': accion, 'motivo': motivo}, format='json',
        )


class PruebasIncidentes(BaseIntegridad):
    def test_advertencia_y_luego_suspension(self):
        r = self.incidente('copiar')
        self.assertEqual((r.status_code, r.data['consecuencia'], r.data['integridad']), (201, 'advertencia', 'advertido'))
        self.assertIn('Si vuelve a ocurrir', r.data['aviso'])
        r = self.incidente('cambio_pestana', segundos=5)
        self.assertEqual((r.data['consecuencia'], r.data['integridad']), ('suspension', 'suspendido'))
        self.assertIn('espera la decisión del docente', r.data['aviso'])
        intento = IntentoEvaluacion.objects.get()
        self.assertAlmostEqual(intento.segundos_restantes_al_suspender, 30 * 60 - 5, delta=3)

    def test_eventos_casi_simultaneos_cuentan_una_vez(self):
        self.incidente('cambio_pestana')
        r = self.incidente('salir_pantalla_completa', segundos=1)  # blur + fullscreenchange del mismo gesto
        self.assertEqual(r.data['consecuencia'], 'agrupado')
        self.assertEqual(IntentoEvaluacion.objects.get().integridad, 'advertido')
        self.assertEqual(IncidenteIntento.objects.count(), 2)  # se registran ambos, cuenta uno

    def test_pantalla_completa_no_disponible_es_informativo(self):
        r = self.incidente('pantalla_completa_no_disponible')
        self.assertEqual(r.data['consecuencia'], 'sin_efecto')
        self.assertEqual(IntentoEvaluacion.objects.get().integridad, 'normal')

    def test_tipo_invalido_y_sin_intento(self):
        self.assertEqual(self.incidente('robar').status_code, 400)
        self.como(self.estudiante2)
        r = self.cliente.post(f'{EST}/{self.eid}/incidentes/', {'tipo': 'copiar'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_suspendido_congela_tiempo_y_bloquea(self):
        self.suspender()
        intento = IntentoEvaluacion.objects.get()
        despues = intento.vence_en + timedelta(hours=1)
        with mock.patch(RELOJ, return_value=despues):
            datos = self.como(self.estudiante).get(f'{EST}/{self.eid}/').data
            r_resp = self.cliente.put(f'{EST}/{self.eid}/respuestas/', {'pregunta': self.pregunta.id, 'opcion': 0}, format='json')
            r_env = self.cliente.post(f'{EST}/{self.eid}/enviar/')
            self.como(self.coordinador).get(f'{API}/evaluaciones/{self.eid}/seguimiento/')
        self.assertEqual(datos['intento']['estado'], 'en_curso')  # sin cierre automático
        self.assertEqual(datos['intento']['integridad'], 'suspendido')
        self.assertNotIn('preguntas', datos)
        self.assertEqual((r_resp.status_code, r_env.status_code), (409, 409))
        self.assertIsNone(IntentoEvaluacion.objects.get().enviado_en)
        r = self.incidente('pegar', segundos=10)  # suspendido: se registra sin efecto
        self.assertEqual(r.data['consecuencia'], 'sin_efecto')


class PruebasResolucion(BaseIntegridad):
    def test_reactivar_con_tiempo_restante(self):
        self.suspender()
        restantes = IntentoEvaluacion.objects.get().segundos_restantes_al_suspender
        luego = timezone.now() + timedelta(minutes=40)
        with mock.patch(RELOJ, return_value=luego):
            r = self.resolver_gestor('reactivar')
        self.assertEqual(r.status_code, 200)
        intento = IntentoEvaluacion.objects.get()
        self.assertEqual(intento.integridad, 'reactivado')
        self.assertAlmostEqual((intento.vence_en - luego).total_seconds(), restantes, delta=1)
        self.assertEqual(ResolucionIntegridad.objects.get().accion, 'reactivar')
        # Tras reactivar, un nuevo incidente suspende sin advertencia.
        with mock.patch(RELOJ, return_value=luego + timedelta(seconds=30)):
            r = self.como(self.estudiante).post(f'{EST}/{self.eid}/incidentes/', {'tipo': 'copiar'}, format='json')
        self.assertEqual(r.data['consecuencia'], 'suspension')

    def test_anular_por_fraude_excluye_del_porcentaje(self):
        self.suspender()
        r = self.resolver_gestor('anular', 'Copió de otra ventana')
        self.assertEqual((r.status_code, r.data['integridad']), (200, 'anulado_fraude'))
        intento = IntentoEvaluacion.objects.get()
        self.assertEqual((intento.nota, intento.aciertos, intento.enviado), (0, 0, True))
        self.assertEqual(intento.motivo_resolucion, 'Copió de otra ventana')
        datos = self.como(self.coordinador).get(f'{API}/evaluaciones/{self.eid}/seguimiento/').data
        self.assertEqual(datos['conteos']['anulados'], 1)
        admin = self.como(_admin())
        desempeno = admin.get(f'{API}/programas/{self.evaluacion.momento.programa_id}/desempeno-ra/').data
        self.assertEqual(desempeno['resumen']['anulados_fraude'], 1)
        self.assertEqual(desempeno['resumen']['intentos'], 0)
        reporte = admin.get(f'{API}/reporte-ejecutivo/').data
        self.assertEqual((reporte['integridad']['anulaciones'], reporte['integridad']['suspensiones']), (1, 1))
        self.assertEqual(reporte['indicadores']['resultados'], 0)  # la nota 0 no entra al promedio

    def test_validaciones_de_resolucion(self):
        self.assertEqual(self.resolver_gestor('reactivar').status_code, 409)  # aún no está suspendido
        self.suspender()
        self.assertEqual(self.resolver_gestor('reactivar', '   ').status_code, 400)  # motivo obligatorio
        self.assertEqual(self.resolver_gestor('borrar').status_code, 400)

    def test_solo_el_supervisor_asignado_decide(self):
        self.asignar(self.docente.id)
        self.suspender()
        url = f'{DOC}/{self.eid}/intentos/{self.estudiante.id}/resolver/'
        cuerpo = {'accion': 'reactivar', 'motivo': 'Falla de conexión'}
        self.assertEqual(self.como(self.otro_docente).post(url, cuerpo, format='json').status_code, 404)
        self.assertEqual(self.resolver_gestor('reactivar').status_code, 409)  # hay supervisor: decide él
        self.assertEqual(self.como(self.estudiante).post(url, cuerpo, format='json').status_code, 403)
        r = self.como(self.estudiante).post(
            f'{API}/evaluaciones/{self.eid}/intentos/{self.estudiante.id}/resolver/', cuerpo, format='json',
        )
        self.assertEqual(r.status_code, 403)
        r = self.como(self.docente).post(url, cuerpo, format='json')
        self.assertEqual((r.status_code, r.data['integridad']), (200, 'reactivado'))

    def test_supervision_muestra_incidentes_sin_nota(self):
        self.asignar(self.docente.id)
        self.suspender()
        datos = self.como(self.docente).get(f'{DOC}/{self.eid}/').data
        fila = next(f for f in datos['filas'] if f['estudiante'] == self.estudiante.id)
        integridad = fila['intento']['integridad']
        self.assertEqual(integridad['estado'], 'suspendido')
        self.assertEqual([i['consecuencia'] for i in integridad['incidentes']], ['advertencia', 'suspension'])
        self.assertEqual(integridad['incidentes_contados'], 2)
        self.assertEqual(datos['conteos']['suspendidos'], 1)
        self.assertNotIn('nota', fila['intento'])


def _admin():
    from apps.evaluacion_resultados.tests.test_supervision import _usuario
    return _usuario('admin@t.co', 'Administrador')


class PruebasSinCambios(BaseSupervision):
    def test_evaluacion_sin_incidentes_sigue_igual(self):
        # Sin incidentes, la presentación y el cierre automático funcionan como antes (HU-07).
        est = self.como(self.estudiante)
        est.post(f'{EST}/{self.eid}/iniciar/')
        intento = IntentoEvaluacion.objects.get()
        with mock.patch(RELOJ, return_value=intento.vence_en + timedelta(minutes=1)):
            datos = est.get(f'{EST}/{self.eid}/').data
        self.assertEqual((datos['intento']['estado'], datos['intento']['integridad']), ('enviado', 'normal'))
        self.assertTrue(EvaluacionFormal.objects.exists())
