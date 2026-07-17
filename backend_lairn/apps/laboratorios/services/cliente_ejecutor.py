"""
Cliente del microservicio ejecutor (sandbox de código para preguntas de
laboratorio). Mismo patrón que `motor_adaptativo.services.cliente_ml`, pero
SIN heurístico de respaldo: si el ejecutor no responde, se lo decimos
explícitamente al estudiante en vez de simular un resultado falso — ejecutar
código no es algo que se pueda degradar silenciosamente como el heurístico
de dominio.
"""

import json
import requests
from django.conf import settings


class EjecutorNoDisponible(Exception):
    """El microservicio ejecutor no está configurado o no respondió."""


def _url(ruta: str) -> str:
    base = getattr(settings, 'EJECUTOR_SERVICE_URL', '') or ''
    if not base:
        raise EjecutorNoDisponible('EJECUTOR_SERVICE_URL no está configurado.')
    return f"{base.rstrip('/')}/{ruta.lstrip('/')}"


def ejecutar_codigo(lenguaje: str, codigo: str, entrada: str = '', timeout_seg: float = 5) -> dict:
    """
    Ejecuta código en cualquier lenguaje "genérico" soportado (todos menos
    SQL, que tiene su propio contrato — ver `ejecutar_sql`). El timeout HTTP
    del cliente deja margen amplio: los lenguajes compilados (Java/C/C++)
    gastan varios segundos compilando antes de correr.
    """
    try:
        respuesta = requests.post(
            _url('ejecutar/codigo'),
            json={'lenguaje': lenguaje, 'codigo': codigo, 'entrada': entrada, 'timeout_seg': timeout_seg},
            timeout=timeout_seg + 25,
        )
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException as error:
        raise EjecutorNoDisponible(str(error)) from error


def ejecutar_sql(setup_sql: str, consulta: str, timeout_seg: float = 5) -> dict:
    try:
        respuesta = requests.post(
            _url('ejecutar/sql'),
            json={'setup_sql': setup_sql, 'consulta': consulta, 'timeout_seg': timeout_seg},
            timeout=timeout_seg + 5,
        )
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException as error:
        raise EjecutorNoDisponible(str(error)) from error


def correr_casos_test(pregunta, codigo_o_consulta: str, casos) -> list[dict]:
    """
    Corre el código/consulta del estudiante contra una lista de `CasoTest` y
    devuelve, por caso, si pasó, la salida esperada y la obtenida.

    - Lenguajes de código (Python/JavaScript/Java/C++/C): compara `stdout`
      (recortado) contra `salida_esperada`. Si el lenguaje compila y falla
      la compilación, el caso no pasa y `stderr` trae el error de compilación.
    - SQL: compara las filas obtenidas (serializadas) contra `salida_esperada`.
      El campo `entrada` de un caso SQL es DDL/DML ADICIONAL que se anexa al
      `setup_sql` de la pregunta para ese caso puntual — permite variar los
      datos semilla por caso sin repetir el esquema completo en cada uno.
    """
    resultados = []
    for caso in casos:
        if pregunta.lenguaje != 'sql':
            salida = ejecutar_codigo(pregunta.lenguaje, codigo_o_consulta, caso.entrada, timeout_seg=5)
            obtenida = (salida.get('stdout') or '').strip()
            paso = (
                not salida.get('timeout')
                and salida.get('compilado') is not False
                and salida.get('exit_code') == 0
                and obtenida == caso.salida_esperada.strip()
            )
            resultados.append({
                'caso_test_id': caso.id,
                'es_publico': caso.es_publico,
                'paso': paso,
                'salida_obtenida': obtenida,
                'salida_esperada': caso.salida_esperada.strip(),
                'stderr': salida.get('error_compilacion') or salida.get('stderr') or '',
                'timeout': bool(salida.get('timeout')),
            })
        else:  # sql
            setup_completo = f"{pregunta.setup_sql}\n{caso.entrada}".strip()
            salida = ejecutar_sql(setup_completo, codigo_o_consulta, timeout_seg=5)
            filas = salida.get('filas')
            obtenida = json.dumps(filas) if filas is not None else ''
            paso = not salida.get('error') and obtenida.strip() == caso.salida_esperada.strip()
            resultados.append({
                'caso_test_id': caso.id,
                'es_publico': caso.es_publico,
                'paso': paso,
                'salida_obtenida': obtenida,
                'salida_esperada': caso.salida_esperada.strip(),
                'stderr': salida.get('error') or '',
                'timeout': bool(salida.get('timeout')),
            })
    return resultados
