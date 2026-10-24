"""
Pruebas de `servicio_fuente_url`: defensas SSRF y límites de descarga.

No hacen red real: `socket.getaddrinfo` y el pool de urllib3 se simulan.
"""

import socket
from unittest import mock

from django.test import SimpleTestCase, override_settings

from apps.evaluacion_resultados.services import servicio_fuente_url as fuente
from apps.evaluacion_resultados.services.servicio_fuente_url import (
    ErrorFuenteUrl,
    obtener_json_desde_url,
    resolver_ip_publica,
    validar_url,
)


def _dns(*ips):
    return [(socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 443))
            for ip in ips]


class _RespuestaFalsa:
    def __init__(self, status=200, cuerpo=b'{}', headers=None):
        self.status = status
        self._cuerpo = cuerpo
        self.headers = {'Content-Type': 'application/json', **(headers or {})}

    def stream(self, tamano):
        for i in range(0, len(self._cuerpo), tamano):
            yield self._cuerpo[i:i + tamano]

    def release_conn(self):
        pass


class PruebasValidarUrl(SimpleTestCase):
    def test_rechaza_esquemas_no_https(self):
        for url in ('http://ejemplo.com/a.json', 'file:///etc/passwd', 'ftp://x.com/a', 'gopher://x'):
            with self.assertRaises(ErrorFuenteUrl):
                validar_url(url)

    def test_rechaza_credenciales_en_url(self):
        with self.assertRaises(ErrorFuenteUrl):
            validar_url('https://usuario:clave@ejemplo.com/a.json')

    def test_acepta_https_y_conserva_query(self):
        self.assertEqual(
            validar_url('https://Ejemplo.com/datos.json?v=1'),
            ('ejemplo.com', 443, '/datos.json?v=1'),
        )

    @override_settings(IMPORTACION_JSON_HOSTS_PERMITIDOS=['uniautonoma.edu.co'])
    def test_lista_de_dominios_autorizados(self):
        self.assertEqual(validar_url('https://api.uniautonoma.edu.co/p')[0], 'api.uniautonoma.edu.co')
        with self.assertRaises(ErrorFuenteUrl):
            validar_url('https://uniautonoma.edu.co.atacante.com/p')


class PruebasResolverIp(SimpleTestCase):
    def test_bloquea_redes_internas(self):
        internas = ('127.0.0.1', '10.0.0.5', '172.17.0.2', '192.168.1.1',
                    '169.254.169.254', '0.0.0.0', '::1', '::ffff:127.0.0.1', 'fd00::1')
        for ip in internas:
            with self.subTest(ip=ip), mock.patch.object(fuente.socket, 'getaddrinfo', return_value=_dns(ip)):
                with self.assertRaises(ErrorFuenteUrl):
                    resolver_ip_publica('ejemplo.com', 443)

    def test_bloquea_si_alguna_ip_es_interna(self):
        with mock.patch.object(fuente.socket, 'getaddrinfo', return_value=_dns('93.184.216.34', '10.0.0.1')):
            with self.assertRaises(ErrorFuenteUrl):
                resolver_ip_publica('ejemplo.com', 443)

    def test_acepta_ip_publica(self):
        with mock.patch.object(fuente.socket, 'getaddrinfo', return_value=_dns('93.184.216.34')):
            self.assertEqual(resolver_ip_publica('ejemplo.com', 443), '93.184.216.34')

    def test_dominio_inexistente(self):
        with mock.patch.object(fuente.socket, 'getaddrinfo', side_effect=socket.gaierror):
            with self.assertRaises(ErrorFuenteUrl):
                resolver_ip_publica('no-existe.invalid', 443)


class PruebasObtenerJson(SimpleTestCase):
    def _con_respuestas(self, *respuestas, ips=None):
        """Simula DNS y un pool que devuelve las respuestas en orden."""
        pool = mock.MagicMock()
        pool.urlopen.side_effect = list(respuestas)
        resolver = mock.patch.object(
            fuente.socket, 'getaddrinfo',
            side_effect=[_dns(ip) for ip in (ips or ['93.184.216.34'] * len(respuestas))],
        )
        return resolver, mock.patch.object(fuente.urllib3, 'HTTPSConnectionPool', return_value=pool), pool

    def test_descarga_y_parsea(self):
        resolver, clase_pool, pool = self._con_respuestas(_RespuestaFalsa(cuerpo=b'{"programas": []}'))
        with resolver, clase_pool as constructor:
            self.assertEqual(obtener_json_desde_url('https://ejemplo.com/a.json'), {'programas': []})
        # Conecta a la IP validada pero verifica TLS contra el dominio.
        args, kwargs = constructor.call_args
        self.assertEqual(args[0], '93.184.216.34')
        self.assertEqual(kwargs['assert_hostname'], 'ejemplo.com')
        self.assertFalse(pool.urlopen.call_args.kwargs['redirect'])

    def test_redireccion_a_red_interna_bloqueada(self):
        resolver, clase_pool, _ = self._con_respuestas(
            _RespuestaFalsa(status=302, headers={'Location': 'https://interno.local/x'}),
            _RespuestaFalsa(),
            ips=['93.184.216.34', '10.0.0.8'],
        )
        with resolver, clase_pool, self.assertRaises(ErrorFuenteUrl):
            obtener_json_desde_url('https://ejemplo.com/a.json')

    def test_redireccion_a_http_bloqueada(self):
        resolver, clase_pool, _ = self._con_respuestas(
            _RespuestaFalsa(status=301, headers={'Location': 'http://ejemplo.com/a.json'}),
        )
        with resolver, clase_pool, self.assertRaises(ErrorFuenteUrl):
            obtener_json_desde_url('https://ejemplo.com/a.json')

    def test_estado_distinto_de_200(self):
        resolver, clase_pool, _ = self._con_respuestas(_RespuestaFalsa(status=404))
        with resolver, clase_pool, self.assertRaisesMessage(ErrorFuenteUrl, '404'):
            obtener_json_desde_url('https://ejemplo.com/a.json')

    def test_tipo_de_contenido_no_json(self):
        resolver, clase_pool, _ = self._con_respuestas(
            _RespuestaFalsa(headers={'Content-Type': 'text/html'}),
        )
        with resolver, clase_pool, self.assertRaises(ErrorFuenteUrl):
            obtener_json_desde_url('https://ejemplo.com/a.json')

    def test_excede_tamano_maximo(self):
        grande = b'[' + b'1,' * (fuente.TAMANO_MAXIMO_BYTES // 2 + 10) + b'1]'
        resolver, clase_pool, _ = self._con_respuestas(_RespuestaFalsa(cuerpo=grande))
        with resolver, clase_pool, self.assertRaisesMessage(ErrorFuenteUrl, '5 MB'):
            obtener_json_desde_url('https://ejemplo.com/a.json')

    def test_json_invalido(self):
        resolver, clase_pool, _ = self._con_respuestas(_RespuestaFalsa(cuerpo=b'<html>'))
        with resolver, clase_pool, self.assertRaises(ErrorFuenteUrl):
            obtener_json_desde_url('https://ejemplo.com/a.json')
