"""
Obtención segura de un JSON desde una URL (importación de programas).

Quien hace la petición es el servidor, así que aquí viven todas las
defensas contra SSRF; el navegador solo envía la URL:
  - solo `https` y sin credenciales embebidas en la URL,
  - lista opcional de dominios autorizados
    (`settings.IMPORTACION_JSON_HOSTS_PERMITIDOS`),
  - el dominio debe resolver ÚNICAMENTE a IP públicas: se bloquean
    loopback, redes privadas, link-local (169.254.x, metadatos cloud),
    reservadas y multicast,
  - la conexión se abre contra la IP ya validada (evita DNS rebinding),
    con SNI y verificación TLS contra el nombre original,
  - redirecciones manuales (máx. 3) revalidando cada salto,
  - timeouts cortos, tiempo total acotado y tamaño máximo de 5 MB.

Los mensajes de `ErrorFuenteUrl` se muestran al administrador: nunca
incluyen IP internas, trazas ni cabeceras del servidor remoto.
"""

import ipaddress
import json
import socket
import time
from urllib.parse import urljoin, urlsplit

import urllib3
from django.conf import settings

TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024
MAX_REDIRECCIONES = 3
TIEMPO_TOTAL_MAXIMO_S = 30
TIMEOUT = urllib3.Timeout(connect=5.0, read=15.0)
# text/plain se admite porque muchos repositorios (p. ej. "raw" de Git)
# sirven .json así; el contenido igual debe parsear como JSON.
TIPOS_CONTENIDO_PERMITIDOS = ('application/json', 'text/json', 'text/plain')
CODIGOS_REDIRECCION = (301, 302, 303, 307, 308)


class ErrorFuenteUrl(Exception):
    """Error con mensaje apto para mostrar al administrador."""


def validar_url(url) -> tuple[str, int, str]:
    """Valida forma y dominio; retorna (host, puerto, ruta_con_query)."""
    if not isinstance(url, str) or not url.strip():
        raise ErrorFuenteUrl('Escribe la URL del recurso JSON.')
    if len(url) > 2000:
        raise ErrorFuenteUrl('La URL es demasiado larga.')
    partes = urlsplit(url.strip())
    if partes.scheme != 'https':
        raise ErrorFuenteUrl('La URL debe empezar por https:// (conexión cifrada).')
    if partes.username or partes.password:
        raise ErrorFuenteUrl('La URL no puede incluir usuario ni contraseña.')
    host = (partes.hostname or '').lower().rstrip('.')
    if not host:
        raise ErrorFuenteUrl('La URL no tiene un dominio válido.')
    try:
        puerto = partes.port or 443
    except ValueError:
        raise ErrorFuenteUrl('El puerto indicado en la URL no es válido.')
    permitidos = getattr(settings, 'IMPORTACION_JSON_HOSTS_PERMITIDOS', [])
    if permitidos and not any(host == p or host.endswith('.' + p) for p in permitidos):
        raise ErrorFuenteUrl('Ese dominio no está en la lista de fuentes autorizadas.')
    ruta = partes.path or '/'
    if partes.query:
        ruta += '?' + partes.query
    return host, puerto, ruta


def resolver_ip_publica(host: str, puerto: int) -> str:
    """Resuelve el dominio y exige que TODAS sus IP sean públicas."""
    try:
        infos = socket.getaddrinfo(host, puerto, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        raise ErrorFuenteUrl('No se encontró el servidor de la URL. Revisa el dominio.')
    ips = []
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        # ::ffff:127.0.0.1 debe evaluarse como la IPv4 que esconde.
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global or ip.is_multicast:
            raise ErrorFuenteUrl('La URL apunta a una red interna o reservada y no está permitida.')
        ips.append(ip)
    if not ips:
        raise ErrorFuenteUrl('No se encontró el servidor de la URL. Revisa el dominio.')
    # Prefiere IPv4: la red de los contenedores no siempre tiene IPv6.
    ips.sort(key=lambda i: i.version)
    return str(ips[0])


def _leer_cuerpo(respuesta, inicio: float) -> bytes:
    tipo = (respuesta.headers.get('Content-Type') or '').split(';')[0].strip().lower()
    if tipo and not (tipo in TIPOS_CONTENIDO_PERMITIDOS or tipo.endswith('+json')):
        raise ErrorFuenteUrl('La URL no devolvió un documento JSON.')
    largo = respuesta.headers.get('Content-Length') or ''
    if largo.isdigit() and int(largo) > TAMANO_MAXIMO_BYTES:
        raise ErrorFuenteUrl('El recurso supera el máximo permitido de 5 MB.')
    cuerpo = bytearray()
    for trozo in respuesta.stream(64 * 1024):
        cuerpo.extend(trozo)
        if len(cuerpo) > TAMANO_MAXIMO_BYTES:
            raise ErrorFuenteUrl('El recurso supera el máximo permitido de 5 MB.')
        if time.monotonic() - inicio > TIEMPO_TOTAL_MAXIMO_S:
            raise ErrorFuenteUrl('El servidor tardó demasiado en enviar el recurso.')
    return bytes(cuerpo)


def obtener_json_desde_url(url: str):
    """Descarga y parsea el JSON de `url` aplicando todas las restricciones."""
    inicio = time.monotonic()
    actual = url.strip() if isinstance(url, str) else url
    for _ in range(MAX_REDIRECCIONES + 1):
        host, puerto, ruta = validar_url(actual)
        ip = resolver_ip_publica(host, puerto)
        pool = urllib3.HTTPSConnectionPool(
            ip, port=puerto, server_hostname=host, assert_hostname=host,
            cert_reqs='CERT_REQUIRED', timeout=TIMEOUT, retries=False, maxsize=1,
        )
        try:
            respuesta = pool.urlopen(
                'GET', ruta,
                headers={
                    'Host': host if puerto == 443 else f'{host}:{puerto}',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'identity',
                    'User-Agent': 'PseudoTutor-Importador/1.0',
                },
                redirect=False, retries=False, preload_content=False,
            )
        except urllib3.exceptions.SSLError:
            pool.close()
            raise ErrorFuenteUrl('El certificado HTTPS del servidor no es válido.')
        except urllib3.exceptions.TimeoutError:
            pool.close()
            raise ErrorFuenteUrl('El servidor tardó demasiado en responder.')
        except urllib3.exceptions.HTTPError:
            pool.close()
            raise ErrorFuenteUrl('No fue posible conectar con el servidor de la URL.')
        try:
            if respuesta.status in CODIGOS_REDIRECCION:
                destino = respuesta.headers.get('Location')
                if not destino:
                    raise ErrorFuenteUrl('El servidor redirigió sin indicar el destino.')
                # El siguiente ciclo revalida esquema, dominio e IP del destino.
                actual = urljoin(actual, destino)
                continue
            if respuesta.status != 200:
                raise ErrorFuenteUrl(
                    f'El servidor respondió con el código {respuesta.status} (se esperaba 200).'
                )
            cuerpo = _leer_cuerpo(respuesta, inicio)
        except urllib3.exceptions.HTTPError:
            raise ErrorFuenteUrl('Se interrumpió la descarga del recurso.')
        finally:
            respuesta.release_conn()
            pool.close()
        try:
            return json.loads(cuerpo.decode('utf-8-sig'))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise ErrorFuenteUrl('El contenido de la URL no es un JSON válido.')
    raise ErrorFuenteUrl('La URL redirige demasiadas veces.')
