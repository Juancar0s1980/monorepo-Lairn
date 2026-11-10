"""
Texto legible de una entrega de tarea, para la preevaluación con IA (HU-15.1).

Formatos con texto: PDF (texto seleccionable), DOCX, ODT, código/TXT y ZIP
(se leen los archivos de texto, PDF y DOCX que contiene). Imágenes y RAR no
tienen texto extraíble aquí: se informa para que el docente califique a mano.
Nada se escribe a disco: se lee el archivo privado ya guardado y se descarta.
"""

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

MAX_CARACTERES = 15000
MAX_ARCHIVOS_ZIP = 30
MAX_BYTES_MIEMBRO = 5 * 1024 * 1024
TEXTO_PLANO = {'txt', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'sql', 'md', 'csv', 'html', 'css', 'json'}
LEGIBLES = TEXTO_PLANO | {'pdf', 'docx', 'odt'}


class EntregaSinTexto(ValueError):
    """La entrega no tiene texto que la IA pueda leer (mensaje para el docente)."""


def _pdf(datos: bytes) -> str:
    lector = PdfReader(io.BytesIO(datos))
    return '\n'.join(p.extract_text() or '' for p in lector.pages)


def _docx(datos: bytes) -> str:
    from docx import Document

    documento = Document(io.BytesIO(datos))
    partes = [p.text for p in documento.paragraphs]
    for tabla in documento.tables:
        for fila in tabla.rows:
            partes.append(' | '.join(c.text for c in fila.cells))
    return '\n'.join(partes)


def _odt(datos: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        raiz = ElementTree.fromstring(z.read('content.xml'))
    return '\n'.join(' '.join(t.strip() for t in nodo.itertext() if t.strip())
                     for nodo in raiz.iter() if nodo.tag.endswith('}p') or nodo.tag.endswith('}h'))


def _plano(datos: bytes) -> str:
    for codificacion in ('utf-8', 'latin-1'):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return ''


def _por_extension(ext: str, datos: bytes) -> str | None:
    if ext == 'pdf':
        return _pdf(datos)
    if ext == 'docx':
        return _docx(datos)
    if ext == 'odt':
        return _odt(datos)
    if ext in TEXTO_PLANO:
        return _plano(datos)
    return None


def _zip(datos: bytes) -> str:
    partes = []
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        miembros = [m for m in z.infolist() if not m.is_dir() and not m.filename.startswith('__MACOSX')]
        for m in miembros[:MAX_ARCHIVOS_ZIP]:
            ext = Path(m.filename).suffix.lower().lstrip('.')
            if m.file_size > MAX_BYTES_MIEMBRO or ext not in LEGIBLES:
                continue
            try:
                texto = _por_extension(ext, z.read(m))
            except Exception:
                continue
            if texto and texto.strip():
                partes.append(f'--- Archivo: {m.filename} ---\n{texto.strip()}')
    return '\n\n'.join(partes)


def texto_de_entrega(entrega) -> tuple[str, list]:
    """Retorna (texto, advertencias). Lanza EntregaSinTexto si no hay nada legible."""
    ext = Path(entrega.nombre_original or '').suffix.lower().lstrip('.')
    with entrega.archivo.open('rb') as f:
        datos = f.read()
    try:
        texto = _zip(datos) if ext == 'zip' else _por_extension(ext, datos)
    except Exception:
        raise EntregaSinTexto('No se pudo leer el archivo de la entrega: puede estar dañado o protegido.')
    if texto is None:
        raise EntregaSinTexto(f'Los archivos .{ext} no tienen texto que la IA pueda leer: califica esta entrega a mano.')
    texto = re.sub(r'[ \t]+', ' ', re.sub(r'\n{3,}', '\n\n', texto)).strip()
    if len(texto) < 40:
        raise EntregaSinTexto('La entrega casi no tiene texto legible (¿es un escaneo o una imagen?): califícala a mano.')
    advertencias = []
    if len(texto) > MAX_CARACTERES:
        advertencias.append(f'La entrega es extensa: se analizaron los primeros {MAX_CARACTERES:,} caracteres.'.replace(',', '.'))
        texto = texto[:MAX_CARACTERES]
    return texto, advertencias
