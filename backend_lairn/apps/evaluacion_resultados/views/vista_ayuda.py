"""
Centro de ayuda (ADR-018).

- `GET  ayuda/?q=&categoria=`   guías visibles para el rol (búsqueda sin tildes).
- `GET  ayuda/<slug>/`           detalle de la guía.
- `GET  ayuda/<slug>/video/`     video de la guía (con sesión; no se publica en /media).
- Administrador: `POST ayuda/` crea, `PATCH ayuda/<slug>/` edita, y
  `POST|DELETE ayuda/<slug>/video/` sube o quita el video (mp4/webm, máx. 100 MB).

Cada usuario ve las guías publicadas de su rol (o sin rol = todas). El
Administrador ve todas, incluidas las no publicadas, para mantenerlas.
"""

import mimetypes
import os
import unicodedata

from django.http import FileResponse, Http404
from django.utils.text import slugify
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evaluacion_resultados.models import ArticuloAyuda, OpcionesCategoriaAyuda
from core.permissions.permisos_rol import EsAdministrador

ROLES_VALIDOS = {'Administrador', 'Coordinador', 'Vicerrector', 'Docente', 'Estudiante'}
EXTENSIONES_VIDEO = {'.mp4': 'video/mp4', '.webm': 'video/webm'}
MAX_BYTES_VIDEO = 100 * 1024 * 1024
CAMPOS_EDITABLES = ('titulo', 'resumen', 'notas', 'ruta', 'categoria', 'roles', 'pasos', 'publicado', 'orden')
MAXIMOS = {'titulo': 150, 'resumen': 300, 'ruta': 200, 'notas': 5000}


def _normalizar(texto) -> str:
    texto = unicodedata.normalize('NFD', str(texto or '').lower())
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')


def _es_admin(request) -> bool:
    return EsAdministrador().has_permission(request, None)


def _rol(usuario):
    return usuario.role.name if getattr(usuario, 'role_id', None) else None


def visibles(request) -> list:
    if _es_admin(request):
        return list(ArticuloAyuda.objects.all())
    rol = _rol(request.user)
    return [a for a in ArticuloAyuda.objects.filter(publicado=True) if not a.roles or rol in a.roles]


def _datos(a, detalle=False) -> dict:
    d = {
        'slug': a.slug, 'titulo': a.titulo, 'categoria': a.categoria,
        'categoria_nombre': OpcionesCategoriaAyuda(a.categoria).label, 'resumen': a.resumen, 'ruta': a.ruta,
        'roles': a.roles, 'tiene_video': bool(a.video), 'publicado': a.publicado, 'orden': a.orden,
        'actualizado_en': a.actualizado_en,
    }
    if detalle:
        d.update(pasos=a.pasos, notas=a.notas, video_nombre=a.video_nombre)
    return d


def _obtener(request, slug):
    a = next((x for x in visibles(request) if x.slug == slug), None)
    if a is None:
        raise Http404
    return a


def _texto(valor, campo):
    valor = str(valor or '').strip()
    if campo in ('titulo', 'resumen') and not valor:
        raise ValueError(f'"{campo}" no puede quedar vacío.')
    if len(valor) > MAXIMOS[campo]:
        raise ValueError(f'"{campo}" admite máximo {MAXIMOS[campo]} caracteres.')
    if campo == 'ruta' and valor and not valor.startswith('/'):
        raise ValueError('"ruta" debe ser una pantalla de la plataforma (empieza por /).')
    return valor


def _pasos(valor):
    if not isinstance(valor, list) or len(valor) > 30:
        raise ValueError('"pasos" debe ser una lista (máximo 30).')
    pasos = []
    for p in valor:
        if not isinstance(p, dict) or not str(p.get('titulo') or '').strip():
            raise ValueError('Cada paso necesita un título.')
        pasos.append({'titulo': str(p['titulo']).strip()[:200], 'detalle': str(p.get('detalle') or '').strip()[:1500]})
    return pasos


def _validar(datos, parcial: bool) -> dict:
    """Campos limpios; lanza ValueError con un mensaje claro."""
    limpio = {}
    for campo in CAMPOS_EDITABLES:
        if campo not in datos:
            if not parcial and campo in ('titulo', 'resumen', 'categoria'):
                raise ValueError(f'Falta "{campo}".')
            continue
        valor = datos[campo]
        if campo in MAXIMOS:
            valor = _texto(valor, campo)
        elif campo == 'categoria' and valor not in OpcionesCategoriaAyuda.values:
            raise ValueError('Categoría inválida.')
        elif campo == 'roles' and (not isinstance(valor, list) or not set(valor) <= ROLES_VALIDOS):
            raise ValueError('"roles" debe ser una lista de roles válidos (vacía = todos).')
        elif campo == 'pasos':
            valor = _pasos(valor)
        elif campo == 'publicado':
            valor = valor in (True, 'true', 'True', 1, '1')
        elif campo == 'orden':
            if not str(valor).isdigit():
                raise ValueError('"orden" debe ser un número entero positivo.')
            valor = int(valor)
        limpio[campo] = valor
    return limpio


class VistaListaAyuda(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        articulos = visibles(request)
        conteo = {}
        for a in articulos:
            conteo[a.categoria] = conteo.get(a.categoria, 0) + 1
        categoria = request.query_params.get('categoria', '')
        if categoria:
            articulos = [a for a in articulos if a.categoria == categoria]
        terminos = _normalizar(request.query_params.get('q', '')).split()
        if terminos:
            def texto(a):
                pasos = ' '.join(f"{p.get('titulo', '')} {p.get('detalle', '')}" for p in a.pasos)
                return _normalizar(f'{a.titulo} {a.resumen} {a.notas} {pasos} {OpcionesCategoriaAyuda(a.categoria).label}')
            articulos = [a for a in articulos if all(t in texto(a) for t in terminos)]
        orden = list(OpcionesCategoriaAyuda.values)
        articulos.sort(key=lambda a: (orden.index(a.categoria), a.orden, a.titulo))
        return Response({
            'categorias': [{'clave': c.value, 'nombre': c.label, 'total': conteo[c.value]}
                           for c in OpcionesCategoriaAyuda if conteo.get(c.value)],
            'articulos': [_datos(a) for a in articulos],
            'puede_editar': _es_admin(request),
        })

    def post(self, request):
        if not _es_admin(request):
            return Response({'detalle': 'Solo el Administrador crea guías.'}, status=403)
        try:
            datos = _validar(request.data, parcial=False)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        base = slugify(datos['titulo'])[:70] or 'guia'
        slug, n = base, 2
        while ArticuloAyuda.objects.filter(slug=slug).exists():
            slug, n = f'{base}-{n}', n + 1
        a = ArticuloAyuda.objects.create(slug=slug, actualizado_por=request.user, **datos)
        return Response(_datos(a, detalle=True), status=201)


class VistaDetalleAyuda(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        return Response(_datos(_obtener(request, slug), detalle=True))

    def patch(self, request, slug):
        if not _es_admin(request):
            return Response({'detalle': 'Solo el Administrador edita las guías.'}, status=403)
        a = _obtener(request, slug)
        try:
            datos = _validar(request.data, parcial=True)
        except ValueError as error:
            return Response({'detalle': str(error)}, status=400)
        for campo, valor in datos.items():
            setattr(a, campo, valor)
        a.actualizado_por = request.user
        a.save()
        return Response(_datos(a, detalle=True))


class VistaVideoAyuda(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        a = _obtener(request, slug)
        if not a.video:
            raise Http404
        tipo = mimetypes.guess_type(a.video.name)[0] or 'video/mp4'
        return FileResponse(a.video.open('rb'), content_type=tipo)

    def post(self, request, slug):
        if not _es_admin(request):
            return Response({'detalle': 'Solo el Administrador sube videos.'}, status=403)
        a = _obtener(request, slug)
        archivo = request.FILES.get('video')
        if archivo is None:
            return Response({'detalle': 'Adjunta un video .mp4 o .webm.'}, status=400)
        extension = os.path.splitext(archivo.name or '')[1].lower()
        if extension not in EXTENSIONES_VIDEO:
            return Response({'detalle': 'Formato no soportado: usa .mp4 o .webm.'}, status=400)
        if archivo.size > MAX_BYTES_VIDEO:
            return Response({'detalle': 'El video supera el máximo de 100 MB.'}, status=400)
        anterior = a.video.name if a.video else None
        a.video.save(f'{a.slug}{extension}', archivo, save=False)
        a.video_nombre = (archivo.name or '')[:200]
        a.actualizado_por = request.user
        a.save()
        if anterior and anterior != a.video.name:
            a.video.storage.delete(anterior)
        return Response(_datos(a, detalle=True))

    def delete(self, request, slug):
        if not _es_admin(request):
            return Response({'detalle': 'Solo el Administrador quita videos.'}, status=403)
        a = _obtener(request, slug)
        if a.video:
            a.video.delete(save=False)
        a.video_nombre = ''
        a.actualizado_por = request.user
        a.save()
        return Response(_datos(a, detalle=True))
