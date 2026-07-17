"""
Runner que corre DENTRO del contenedor efimero de C++.

Compila con g++ antes de ejecutar. Si la compilacion falla, devuelve
`compilado: false` con el error de compilacion en vez de intentar correr
nada (mismo contrato que el runner de Java).
"""

import os
import json
import base64
import subprocess

MAX_SALIDA = 65536
TIMEOUT_MAXIMO = 10.0
TIMEOUT_COMPILACION = 15.0


def main():
    try:
        payload = json.loads(base64.b64decode(os.environ.get('PAYLOAD_B64', '')))
    except Exception as error:
        print(json.dumps({'stdout': '', 'stderr': f'Payload invalido: {error}', 'exit_code': -1, 'timeout': False, 'compilado': None, 'error_compilacion': None}))
        return

    codigo = payload.get('codigo', '')
    entrada = payload.get('entrada', '')
    timeout = min(float(payload.get('timeout_seg', 5)), TIMEOUT_MAXIMO)

    with open('/tmp/solucion.cpp', 'w') as archivo:
        archivo.write(codigo)

    try:
        compilacion = subprocess.run(
            ['g++', '-O2', '-o', '/tmp/solucion', '/tmp/solucion.cpp'],
            capture_output=True, text=True, timeout=TIMEOUT_COMPILACION,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({'stdout': '', 'stderr': 'Tiempo de compilacion excedido.', 'exit_code': -1, 'timeout': True, 'compilado': False, 'error_compilacion': 'Tiempo de compilacion excedido.'}))
        return

    if compilacion.returncode != 0:
        error = compilacion.stderr[:MAX_SALIDA]
        print(json.dumps({'stdout': '', 'stderr': error, 'exit_code': -1, 'timeout': False, 'compilado': False, 'error_compilacion': error}))
        return

    try:
        proceso = subprocess.run(
            ['/tmp/solucion'], input=entrada, capture_output=True, text=True, timeout=timeout,
        )
        resultado = {
            'stdout': proceso.stdout[:MAX_SALIDA],
            'stderr': proceso.stderr[:MAX_SALIDA],
            'exit_code': proceso.returncode,
            'timeout': False,
            'compilado': True,
            'error_compilacion': None,
        }
    except subprocess.TimeoutExpired:
        resultado = {
            'stdout': '', 'stderr': f'Tiempo de ejecucion excedido ({timeout}s).',
            'exit_code': -1, 'timeout': True, 'compilado': True, 'error_compilacion': None,
        }
    except Exception as error:
        resultado = {'stdout': '', 'stderr': f'Error del runner: {error}', 'exit_code': -1, 'timeout': False, 'compilado': True, 'error_compilacion': None}

    print(json.dumps(resultado))


if __name__ == '__main__':
    main()
