"""
Escala de calificación institucional (ADR-019). Único lugar del sistema.

Fuentes:
  - Acuerdo 005 de 2025 (Reglamento Estudiantil de Pregrado, Uniautónoma), verificado:
      Art. 45  escala 0,0-5,0 con un decimal; si la centésima es >= 5 se aproxima por exceso.
      Art. 46  nota de aprobación >= 3,0.
      Art. 47  cortes 30 % · 30 % · 40 %.
  - Resolución 0238 de 2024 (lineamientos de RA), tomada de la propuesta del proyecto
    (texto oficial no publicado; POR VERIFICAR con Vicerrectoría):
      niveles Superior 4,6-5,0 · Alto 3,8-4,5 · Suficiente 3,0-3,7 · Insuficiente 2,2-2,9 ·
      Muy insuficiente 0,0-2,1; los exámenes comprensivos valen el 30 % del tercer corte.
"""

from decimal import ROUND_HALF_UP, Decimal

NOTA_MINIMA = Decimal('0.0')
NOTA_MAXIMA = Decimal('5.0')
NOTA_APROBACION = Decimal('3.0')

# (clave, etiqueta, nota mínima con un decimal), de mayor a menor.
NIVELES = [
    ('superior', 'Superior', Decimal('4.6')),
    ('alto', 'Alto', Decimal('3.8')),
    ('suficiente', 'Suficiente', Decimal('3.0')),
    ('insuficiente', 'Insuficiente', Decimal('2.2')),
    ('muy_insuficiente', 'Muy insuficiente', Decimal('0.0')),
]
NIVELES_APROBADOS = ('superior', 'alto', 'suficiente')
ETIQUETA_NIVEL = {c: e for c, e, _m in NIVELES}

# Pesos institucionales por defecto (configurables en EsquemaCalificacion).
PESO_TERCER_CORTE_EN_DEFINITIVA = Decimal('40')   # Acuerdo 005, Art. 47 (verificado)
PESO_MOMENTO_EN_TERCER_CORTE = Decimal('30')      # Res. 0238/2024 según la propuesta (por verificar)

FUENTES = {
    'escala_redondeo': 'Acuerdo 005 de 2025, Arts. 45 y 46 (verificado)',
    'peso_corte': 'Acuerdo 005 de 2025, Art. 47 (verificado)',
    'niveles': 'Resolución 0238 de 2024, según la propuesta del proyecto (por verificar)',
    'peso_momento': 'Resolución 0238 de 2024, según la propuesta del proyecto (por verificar)',
}


def rangos() -> list:
    """[(clave, etiqueta, mínimo, máximo)] con un decimal, p. ej. ('alto', 'Alto', 3.8, 4.5)."""
    salida, techo = [], NOTA_MAXIMA
    for clave, etiqueta, minimo in NIVELES:
        salida.append((clave, etiqueta, minimo, techo))
        techo = minimo - Decimal('0.1')
    return salida


def redondear(valor) -> Decimal | None:
    """Redondeo reglamentario a un decimal (Art. 45: centésima >= 5 por exceso)."""
    if valor is None:
        return None
    return Decimal(str(valor)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def nivel(nota) -> str | None:
    """Clave del nivel de desempeño de una nota (se redondea primero al decimal reglamentario)."""
    if nota is None:
        return None
    n = redondear(nota)
    for clave, _etiqueta, minimo in NIVELES:
        if n >= minimo:
            return clave
    return NIVELES[-1][0]


def aprueba(nota) -> bool | None:
    return None if nota is None else redondear(nota) >= NOTA_APROBACION
