"""
Sirve archivos de `MEDIA_ROOT` con soporte de HTTP Range (206 Partial
Content) — a diferencia de `django.views.static.serve` (usado por el helper
`static()` de Django), que ignora el header `Range` y siempre devuelve el
archivo completo con 200. Los navegadores usan Range para calcular la
duración y permitir "seek" en `<audio>`/`<video>`; sin esto, algunos
navegadores fallan al reproducir o quedan pegados en 0:00 (confirmado con
los audios de pronunciación generados con Edge TTS: `curl -H "Range: ..."`
contra `django.views.static.serve` devolvía 200 en vez de 206).

Solo se usa en desarrollo (`DEBUG=True`, ver `backend_lairn/urls.py`). Los
archivos de este proyecto son pequeños (audio de pronunciación, imágenes,
PDFs de plan de aula), así que se leen enteros en memoria en vez de hacer
streaming por bloques — más simple y suficiente para este volumen.
"""

import mimetypes
import re
from pathlib import Path

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseNotModified
from django.utils._os import safe_join
from django.utils.http import http_date
from django.views.static import was_modified_since

_RANGO_RE = re.compile(r'bytes=(\d*)-(\d*)')


def servir_media_con_rango(request, path, document_root=None):
    fullpath = Path(safe_join(document_root, path))
    if not fullpath.exists() or not fullpath.is_file():
        return HttpResponseNotFound('Archivo no encontrado.')

    statobj = fullpath.stat()
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'), statobj.st_mtime):
        return HttpResponseNotModified()

    content_type, _ = mimetypes.guess_type(str(fullpath))
    content_type = content_type or 'application/octet-stream'
    contenido = fullpath.read_bytes()
    tamano = len(contenido)

    match = _RANGO_RE.match(request.META.get('HTTP_RANGE', ''))
    if match:
        inicio = int(match.group(1)) if match.group(1) else 0
        fin = int(match.group(2)) if match.group(2) else tamano - 1
        fin = min(fin, tamano - 1)
        if tamano == 0 or inicio > fin or inicio >= tamano:
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{tamano}'
            return response
        response = HttpResponse(contenido[inicio:fin + 1], content_type=content_type, status=206)
        response['Content-Range'] = f'bytes {inicio}-{fin}/{tamano}'
        response['Content-Length'] = str(fin - inicio + 1)
    else:
        response = HttpResponse(contenido, content_type=content_type)
        response['Content-Length'] = str(tamano)

    response['Accept-Ranges'] = 'bytes'
    response['Last-Modified'] = http_date(statobj.st_mtime)
    # Sin Cache-Control explícito, el navegador aplica caché heurística basada
    # en Last-Modified y puede reusar una respuesta vieja SIN volver a pedirla
    # al servidor — esto mordió en desarrollo: el navegador siguió sirviendo
    # una respuesta 200 (sin soporte de Range) cacheada de antes de este fix,
    # incluso después de corregir el backend. "no-cache" obliga a revalidar
    # en cada carga (barato: ya soportamos If-Modified-Since arriba, así que
    # revalida con un 304 en vez de re-descargar si no cambió).
    response['Cache-Control'] = 'no-cache'
    return response
