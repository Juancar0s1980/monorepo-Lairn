"""
Runner que corre DENTRO del contenedor efimero de SQL.

Ejecuta la consulta del estudiante contra una base SQLite EN MEMORIA
(nunca la base de datos real del proyecto), previamente poblada con el
`setup_sql` que define el docente al crear la pregunta (esquema + datos
semilla). Un "authorizer" bloquea ATTACH/DETACH y PRAGMA: no hay ninguna
razon legitima para que una consulta de estudiante los use, y reduce
superficie de ataque incluso dentro del sandbox.
"""

import os
import json
import base64
import sqlite3

MAX_FILAS = 1000
TIMEOUT_MAXIMO = 10.0

ACCIONES_BLOQUEADAS = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA}


def _autorizador(accion, *_args):
    if accion in ACCIONES_BLOQUEADAS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def main():
    try:
        payload = json.loads(base64.b64decode(os.environ.get("PAYLOAD_B64", "")))
    except Exception as error:
        print(json.dumps({"filas": None, "columnas": None, "error": f"Payload invalido: {error}"}))
        return

    setup_sql = payload.get("setup_sql", "")
    consulta = payload.get("consulta", "")
    timeout = min(float(payload.get("timeout_seg", 5)), TIMEOUT_MAXIMO)

    conexion = sqlite3.connect(":memory:", timeout=timeout)
    conexion.set_authorizer(_autorizador)
    cursor = conexion.cursor()

    resultado = {"filas": None, "columnas": None, "error": None}
    try:
        if setup_sql.strip():
            cursor.executescript(setup_sql)
        cursor.execute(consulta)
        filas = cursor.fetchmany(MAX_FILAS)
        resultado["columnas"] = [d[0] for d in cursor.description] if cursor.description else []
        resultado["filas"] = filas
    except Exception as error:
        resultado["error"] = str(error)
    finally:
        conexion.close()

    print(json.dumps(resultado))


if __name__ == "__main__":
    main()
