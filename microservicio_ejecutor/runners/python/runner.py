"""
Runner que corre DENTRO del contenedor efimero de Python.

No confia en nada del entorno: lee el payload de una variable de entorno
(evita depender de sockets de stdin), ejecuta el codigo del estudiante como
subproceso hijo (heredando los limites de recursos del contenedor: memoria,
CPU, PIDs, red) y siempre imprime un JSON de resultado a stdout, incluso si
el codigo del estudiante truena.
"""

import os
import sys
import json
import base64
import subprocess

MAX_SALIDA = 65536  # 64 KB, evita que una salida gigante infle la respuesta
TIMEOUT_MAXIMO = 10.0  # tope duro, sin importar lo que pida el payload


def main():
    try:
        payload = json.loads(base64.b64decode(os.environ.get("PAYLOAD_B64", "")))
    except Exception as error:
        print(json.dumps({"stdout": "", "stderr": f"Payload invalido: {error}", "exit_code": -1, "timeout": False}))
        return

    codigo = payload.get("codigo", "")
    entrada = payload.get("entrada", "")
    timeout = min(float(payload.get("timeout_seg", 5)), TIMEOUT_MAXIMO)

    with open("/tmp/solucion.py", "w") as archivo:
        archivo.write(codigo)

    try:
        proceso = subprocess.run(
            [sys.executable, "/tmp/solucion.py"],
            input=entrada,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        resultado = {
            "stdout": proceso.stdout[:MAX_SALIDA],
            "stderr": proceso.stderr[:MAX_SALIDA],
            "exit_code": proceso.returncode,
            "timeout": False,
        }
    except subprocess.TimeoutExpired:
        resultado = {
            "stdout": "",
            "stderr": f"Tiempo de ejecucion excedido ({timeout}s).",
            "exit_code": -1,
            "timeout": True,
        }
    except Exception as error:
        resultado = {"stdout": "", "stderr": f"Error del runner: {error}", "exit_code": -1, "timeout": False}

    print(json.dumps(resultado))


if __name__ == "__main__":
    main()
