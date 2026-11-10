"""
Lectura de los query params de la analítica Saber Pro (HU-24).

Compartido por las vistas de consulta y de exportación para que ambas
interpreten exactamente los mismos filtros.
"""


def entero_opcional(valor, nombre):
    """Convierte un query param opcional a entero, con error claro si es inválido."""
    if valor in (None, ''):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'El parámetro {nombre} debe ser un número entero.')


def parametros_analitica_curso(request):
    """Filtros de la analítica de un curso del docente."""
    return {
        'area_id': entero_opcional(request.query_params.get('area_id'), 'area_id'),
        'simulacro_id': entero_opcional(
            request.query_params.get('simulacro_id'), 'simulacro_id'
        ),
        'competencia_id': entero_opcional(
            request.query_params.get('competencia_id'), 'competencia_id'
        ),
        'afirmacion_id': entero_opcional(
            request.query_params.get('afirmacion_id'), 'afirmacion_id'
        ),
        'parte': entero_opcional(request.query_params.get('parte'), 'parte'),
        'periodo': (request.query_params.get('periodo') or '').strip() or None,
    }


def parametros_analitica_institucional(request):
    """Filtros de la analítica consolidada de la institución."""
    return {
        'curso_id': entero_opcional(request.query_params.get('curso_id'), 'curso_id'),
        'programa_id': entero_opcional(
            request.query_params.get('programa_id'), 'programa_id'
        ),
        'area_id': entero_opcional(request.query_params.get('area_id'), 'area_id'),
        'competencia_id': entero_opcional(
            request.query_params.get('competencia_id'), 'competencia_id'
        ),
        'afirmacion_id': entero_opcional(
            request.query_params.get('afirmacion_id'), 'afirmacion_id'
        ),
        'parte': entero_opcional(request.query_params.get('parte'), 'parte'),
        'periodo': (request.query_params.get('periodo') or '').strip() or None,
    }
