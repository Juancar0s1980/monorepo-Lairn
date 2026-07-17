"""
Verifica los casos de test propuestos por la IA ejecutando la SOLUCIÓN DE
REFERENCIA (no la del estudiante) en el sandbox del microservicio ejecutor.

La IA puede equivocarse calculando a mano la salida esperada de un caso; en
vez de confiar en eso, se corre de verdad la solución de referencia contra
cada entrada propuesta y se usa la salida real como `salida_esperada`. Los
casos donde la solución de referencia falla (error, timeout) se descartan en
vez de colar un test roto — más vale una pregunta con menos casos que uno
que el propio ejercicio no puede pasar.
"""

import json
from .cliente_ejecutor import ejecutar_codigo, ejecutar_sql, EjecutorNoDisponible


def verificar_casos(lenguaje: str, solucion_referencia: str, setup_sql: str, casos_borrador: list) -> list[dict]:
    """
    Devuelve la lista de casos que SÍ se pudieron verificar, con
    `salida_esperada` calculada a partir de la ejecución real. Los que
    fallan se omiten silenciosamente (el llamador decide qué hacer si
    quedan cero casos verificados).
    """
    verificados = []
    for orden, caso in enumerate(casos_borrador, start=1):
        entrada = str(caso.get('entrada', ''))
        es_publico = bool(caso.get('es_publico', False))

        try:
            if lenguaje != 'sql':
                # timeout_seg 8 (no 5): da margen a que Java/C/C++ compilen
                # la solución de referencia antes de correrla.
                resultado = ejecutar_codigo(lenguaje, solucion_referencia, entrada, timeout_seg=8)
                if resultado.get('timeout') or resultado.get('compilado') is False or resultado.get('exit_code') != 0:
                    continue
                salida_esperada = (resultado.get('stdout') or '').strip()
            else:  # sql
                setup_completo = f"{setup_sql}\n{entrada}".strip()
                resultado = ejecutar_sql(setup_completo, solucion_referencia, timeout_seg=5)
                if resultado.get('timeout') or resultado.get('error'):
                    continue
                filas = resultado.get('filas')
                if filas is None:
                    continue
                salida_esperada = json.dumps(filas)
        except EjecutorNoDisponible:
            # Si el ejecutor se cae a mitad de la verificación, mejor devolver
            # lo verificado hasta ahora que reventar toda la generación.
            break

        verificados.append({
            'entrada': entrada,
            'salida_esperada': salida_esperada,
            'es_publico': es_publico,
            'orden': orden,
        })

    # Garantiza al menos un caso público entre los verificados (ejemplo para
    # el estudiante), aunque la IA hubiera marcado todos como ocultos.
    if verificados and not any(c['es_publico'] for c in verificados):
        verificados[0]['es_publico'] = True

    return verificados
