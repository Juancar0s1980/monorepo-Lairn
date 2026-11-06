"""
Reglas de negocio de las tareas prácticas (HU-08A / HU-08B).

- Rúbrica: criterios con peso (suman 100 %) y niveles con valor 0-5.
- Nota ponderada = Σ peso/100 × valor del nivel elegido (HU-08B.4).
- Plazo: a tiempo / con retraso / cerrado según `permite_tardias` (HU-08A.3).
- Formatos: grupos legibles para el docente que se traducen a extensiones.
"""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.utils import timezone

# Grupo visible al docente -> extensiones aceptadas en la entrega.
FORMATOS = {
    'pdf': ['pdf'],
    'documento': ['doc', 'docx', 'odt'],
    'zip': ['zip'],
    'rar': ['rar'],
    'codigo': ['py', 'js', 'ts', 'java', 'cpp', 'c', 'sql', 'txt'],
    'imagen': ['png', 'jpg', 'jpeg'],
}
TAMANO_MAX_ENTREGA = 20 * 1024 * 1024
TAMANO_MAX_GUIA = 10 * 1024 * 1024
# Los archivos guía los sube el docente; se aceptan formatos de documento comunes.
EXTENSIONES_GUIA = {'pdf', 'doc', 'docx', 'odt', 'zip', 'png', 'jpg', 'jpeg', 'txt'}
MAX_CRITERIOS, MIN_NIVELES, MAX_NIVELES = 10, 2, 5


class ErrorRubrica(ValueError):
    pass


def extensiones_permitidas(formatos: list) -> set:
    return {ext for grupo in formatos for ext in FORMATOS.get(grupo, [])}


def extension(nombre: str) -> str:
    return Path(nombre or '').suffix.lower().lstrip('.')


def validar_formatos(formatos) -> list:
    if not isinstance(formatos, list) or not formatos:
        raise ValueError('Elige al menos un formato de entrega permitido.')
    desconocidos = [f for f in formatos if f not in FORMATOS]
    if desconocidos:
        raise ValueError(f'Formato no reconocido: {", ".join(map(str, desconocidos))}.')
    return list(dict.fromkeys(formatos))


def validar_rubrica(rubrica) -> list:
    """Normaliza y valida la rúbrica; lanza ErrorRubrica con un mensaje para el docente."""
    if not isinstance(rubrica, list) or not rubrica:
        raise ErrorRubrica('La rúbrica necesita al menos un criterio.')
    if len(rubrica) > MAX_CRITERIOS:
        raise ErrorRubrica(f'La rúbrica admite como máximo {MAX_CRITERIOS} criterios.')
    limpia = []
    for i, c in enumerate(rubrica, start=1):
        if not isinstance(c, dict) or not str(c.get('criterio') or '').strip():
            raise ErrorRubrica(f'El criterio {i} no tiene nombre.')
        peso = c.get('peso')
        if isinstance(peso, bool) or not isinstance(peso, int) or not 1 <= peso <= 100:
            raise ErrorRubrica(f'El peso del criterio {i} debe ser un entero entre 1 y 100.')
        niveles = c.get('niveles')
        if not isinstance(niveles, list) or not MIN_NIVELES <= len(niveles) <= MAX_NIVELES:
            raise ErrorRubrica(f'El criterio {i} debe tener entre {MIN_NIVELES} y {MAX_NIVELES} niveles.')
        niveles_limpios = []
        for n in niveles:
            nombre = str((n or {}).get('nombre') or '').strip() if isinstance(n, dict) else ''
            valor = n.get('valor') if isinstance(n, dict) else None
            if not nombre:
                raise ErrorRubrica(f'Hay un nivel sin nombre en el criterio {i}.')
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not 0 <= valor <= 5:
                raise ErrorRubrica(f'El valor del nivel "{nombre}" (criterio {i}) debe estar entre 0 y 5.')
            niveles_limpios.append({
                'nombre': nombre[:60], 'descripcion': str(n.get('descripcion') or '').strip()[:300],
                'valor': round(float(valor), 2),
            })
        limpia.append({
            'criterio': str(c['criterio']).strip()[:150], 'descripcion': str(c.get('descripcion') or '').strip()[:500],
            'peso': peso, 'niveles': niveles_limpios,
        })
    total = sum(c['peso'] for c in limpia)
    if total != 100:
        # HU-08B.2: alerta de inconsistencia si las ponderaciones no suman 100 %.
        raise ErrorRubrica(f'Los pesos de la rúbrica suman {total} %; deben sumar exactamente 100 %.')
    return limpia


def rubrica_desde_resultado(resultado) -> list:
    """Convierte la rúbrica DCE del RA ({criterio, niveles: 'bajo/básico/alto', peso}) en rúbrica de tarea.

    Los valores de los niveles se reparten de forma pareja en la escala 1-5
    (p. ej. 3 niveles -> 1.0, 3.0, 5.0); el docente puede ajustarlos.
    """
    criterios = [c for c in (resultado.criterios_rubrica or []) if isinstance(c, dict) and c.get('criterio')]
    if not criterios:
        return []
    rubrica = []
    for c in criterios:
        nombres = [n.strip().capitalize() for n in str(c.get('niveles') or 'Bajo/Básico/Alto').split('/') if n.strip()]
        nombres = nombres[:MAX_NIVELES] if len(nombres) >= MIN_NIVELES else ['Bajo', 'Básico', 'Alto']
        paso = 4 / (len(nombres) - 1)
        rubrica.append({
            'criterio': str(c['criterio'])[:150], 'descripcion': '',
            'peso': int(c.get('peso') or 0),
            'niveles': [{'nombre': n, 'descripcion': '', 'valor': round(1 + paso * i, 2)} for i, n in enumerate(nombres)],
        })
    # Si los pesos del RA no suman 100, se reparten de nuevo para que la rúbrica sea válida.
    if sum(c['peso'] for c in rubrica) != 100:
        base, resto = divmod(100, len(rubrica))
        for i, c in enumerate(rubrica):
            c['peso'] = base + (1 if i < resto else 0)
    return rubrica


def calcular_nota(rubrica: list, niveles_elegidos: list) -> Decimal:
    if len(niveles_elegidos) != len(rubrica):
        raise ValueError('Elige un nivel para cada criterio de la rúbrica.')
    total = Decimal('0')
    for criterio, indice in zip(rubrica, niveles_elegidos):
        if isinstance(indice, bool) or not isinstance(indice, int) or not 0 <= indice < len(criterio['niveles']):
            raise ValueError(f'Nivel no válido en el criterio "{criterio["criterio"]}".')
        total += Decimal(str(criterio['peso'])) / 100 * Decimal(str(criterio['niveles'][indice]['valor']))
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def estado_plazo(tarea, ahora=None) -> str:
    """'abierta' | 'tardia' (vencida pero acepta) | 'cerrada'."""
    ahora = ahora or timezone.now()
    if ahora <= tarea.fecha_limite:
        return 'abierta'
    return 'tardia' if tarea.permite_tardias else 'cerrada'


def estado_entrega(entrega) -> str:
    if entrega is None:
        return 'sin_entregar'
    return 'con_retraso' if entrega.con_retraso else 'a_tiempo'


def estudiantes_de_tarea(tarea):
    """Estudiantes inscritos en el curso Lairn vinculado a la asignatura de la tarea."""
    curso_id = tarea.asignatura.curso_vinculado_id
    User = get_user_model()
    if curso_id is None:
        return User.objects.none()
    return User.objects.filter(inscripciones__curso_id=curso_id, role__name='Estudiante').order_by(
        'first_last_name', 'first_name',
    )
