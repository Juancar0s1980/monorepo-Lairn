"""
Paquete de servicios de `evaluacion_resultados`.

- `extractor_pdf`: texto + hash SHA256 en memoria (el PDF nunca se guarda).
- `agente_pensum`: malla desde PDF del pensum.
- `agente_resolucion`: programa + momentos desde resolución.
- `agente_diseno_evidencias`: estructura DCE desde plan de aula.
- `servicio_importador_nova`: adapter idempotente JSON -> modelos.
- `servicio_trazabilidad`: bitácora de sync y versionado HU-01.8.
"""

from .extractor_pdf import extraer_texto_pdf, calcular_hash_texto
from .servicio_trazabilidad import registrar_sincronizacion
from .servicio_importador_nova import importar_programas_json

__all__ = [
    'extraer_texto_pdf',
    'calcular_hash_texto',
    'registrar_sincronizacion',
    'importar_programas_json',
]
