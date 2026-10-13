"""
Extractor de texto PDF en memoria (seguridad por diseño).

El archivo subido NUNCA se persiste a disco ni a `FileField`: se lee
del request, se extrae el texto y se descarta. Solo se guarda el
SHA256 del texto (`hash_texto`) para no reprocesar el mismo documento
y el nombre del archivo para auditoría.
"""

import hashlib

from pypdf import PdfReader


def extraer_texto_pdf(archivo) -> str:
    """Extrae todo el texto seleccionable de un PDF en memoria."""
    lector = PdfReader(archivo)
    paginas = [pagina.extract_text() or '' for pagina in lector.pages]
    return '\n'.join(paginas).strip()


def calcular_hash_texto(texto: str) -> str:
    """SHA256 del texto normalizado (detección de duplicados)."""
    normalizado = ' '.join(texto.split()).lower()
    return hashlib.sha256(normalizado.encode('utf-8')).hexdigest()
