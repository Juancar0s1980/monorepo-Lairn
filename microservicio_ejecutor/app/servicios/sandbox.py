"""
Orquestacion de la ejecucion aislada de codigo.

Cada llamada a `ejecutar()` lanza un contenedor EFIMERO nuevo (uno por
ejecucion, nunca se reutiliza) con:
  - Sin red (`network_disabled=True`): el codigo del estudiante no puede
    llamar a nada fuera del contenedor.
  - Filesystem raiz de solo lectura + /tmp en tmpfs: nada persiste, y lo
    que se escribe desaparece con el contenedor.
  - Memoria, CPU y numero de procesos limitados: un fork-bomb o un bucle
    infinito no puede tumbar el host ni afectar a otros contenedores.
  - Usuario sin privilegios y capabilities de Linux eliminadas.
  - Timeout interno (dentro del runner) + timeout externo de respaldo:
    si el contenedor no responde ni siquiera a eso, se mata por nombre.

El payload (codigo/consulta del estudiante) viaja como variable de entorno
en base64: evita la complejidad de adjuntar un socket de stdin a un
contenedor "detached" via la API de Docker, y no hay ningun secreto que
proteger en esa variable (es literalmente lo que el estudiante escribio).

IMPORTANTE: este servicio requiere acceso al socket de Docker del host
(monta `/var/run/docker.sock`). Es el UNICO servicio del proyecto con ese
acceso — `web` nunca toca Docker directamente, le habla a este servicio
por HTTP interno (mismo patron que `ml`). Si se compromete este servicio,
el atacante hereda control del daemon Docker del host, no solo de los
sandboxes; ver README para hardening adicional recomendado (docker-socket-proxy).
"""

import base64
import json
import time
import uuid

import docker
from docker.errors import ImageNotFound, NotFound

from app.config import ajustes

_cliente = docker.from_env()


def imagenes_listas() -> dict[str, bool]:
    """Reporta si cada imagen runner ya existe en el daemon (para /health)."""
    estado = {}
    for lenguaje, tag in ajustes.IMAGENES.items():
        try:
            _cliente.images.get(tag)
            estado[lenguaje] = True
        except ImageNotFound:
            estado[lenguaje] = False
    return estado


def asegurar_imagenes() -> None:
    """Construye las imagenes runner que falten. Se llama al arrancar el servicio."""
    for lenguaje, tag in ajustes.IMAGENES.items():
        try:
            _cliente.images.get(tag)
        except ImageNotFound:
            ruta = ajustes.DIR_RUNNERS / lenguaje
            _cliente.images.build(path=str(ruta), tag=tag, rm=True)


def _ejecutar_contenedor(imagen: str, payload: dict, timeout_seg: float) -> tuple[bytes, bool]:
    """
    Lanza el contenedor efimero, espera su salida y lo elimina siempre.
    Devuelve (logs_stdout, hubo_timeout_de_infraestructura).
    """
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    nombre = f"lairn-exec-{uuid.uuid4().hex[:12]}"

    contenedor = _cliente.containers.run(
        imagen,
        name=nombre,
        environment={"PAYLOAD_B64": payload_b64},
        detach=True,
        network_disabled=True,
        read_only=True,
        # "exec" es necesario: los lenguajes compilados (C/C++) escriben su
        # binario en /tmp y lo corren directo. El montaje "--tmpfs" de Docker
        # es noexec por defecto, así que hay que pedirlo explícitamente.
        tmpfs={"/tmp": "size=16m,exec"},
        mem_limit=ajustes.MEMORIA_LIMITE,
        memswap_limit=ajustes.MEMORIA_LIMITE,  # swap = memoria => 0 swap real
        nano_cpus=int(ajustes.CPUS_LIMITE * 1_000_000_000),
        pids_limit=ajustes.PIDS_LIMITE,
        user="1000:1000",
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
    )

    hubo_timeout = False
    try:
        # Margen amplio (no solo timeout_seg+3): los lenguajes compilados
        # (Java/C/C++) gastan varios segundos en compilar ANTES de correr,
        # y ese tiempo también tiene que caber en esta espera.
        contenedor.wait(timeout=timeout_seg + 20)
    except Exception:
        # El runner interno deberia haber cortado antes que esto; si llegamos
        # aqui, el contenedor no respondio ni a su propio timeout (ej. la
        # imagen se colgo al arrancar) y lo forzamos desde afuera.
        hubo_timeout = True
        try:
            contenedor.kill()
        except NotFound:
            pass

    logs = contenedor.logs(stdout=True, stderr=False)
    try:
        contenedor.remove(force=True)
    except NotFound:
        pass

    return logs, hubo_timeout


def ejecutar_codigo(lenguaje: str, codigo: str, entrada: str, timeout_seg: float | None) -> dict:
    """
    Ejecuta código en cualquiera de los lenguajes "genéricos" (todos menos
    SQL, que tiene su propio contrato — ver `ejecutar_sql`). El contrato de
    payload/respuesta es el mismo para todos: cada runner sabe compilar (si
    aplica) y correr su propio lenguaje.
    """
    if lenguaje not in ajustes.LENGUAJES_CODIGO:
        raise ValueError(f"Lenguaje no soportado: {lenguaje}")

    timeout = min(timeout_seg or ajustes.TIMEOUT_DEFECTO_SEG, ajustes.TIMEOUT_MAXIMO_SEG)
    inicio = time.monotonic()
    logs, hubo_timeout = _ejecutar_contenedor(
        ajustes.IMAGENES[lenguaje],
        {"codigo": codigo, "entrada": entrada, "timeout_seg": timeout},
        timeout,
    )
    tiempo_ms = round((time.monotonic() - inicio) * 1000)

    base = {"lenguaje": lenguaje, "tiempo_ms": tiempo_ms, "compilado": None, "error_compilacion": None}

    if hubo_timeout:
        return {**base, "stdout": "", "stderr": "Timeout de infraestructura.", "exit_code": -1, "timeout": True}

    try:
        resultado = json.loads(logs.decode(errors="replace").strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {**base, "stdout": "", "stderr": "Salida invalida del runner.", "exit_code": -1, "timeout": False}

    return {**base, **resultado}


def ejecutar_sql(setup_sql: str, consulta: str, timeout_seg: float | None) -> dict:
    timeout = min(timeout_seg or ajustes.TIMEOUT_DEFECTO_SEG, ajustes.TIMEOUT_MAXIMO_SEG)
    inicio = time.monotonic()
    logs, hubo_timeout = _ejecutar_contenedor(
        ajustes.IMAGENES["sql"],
        {"setup_sql": setup_sql, "consulta": consulta, "timeout_seg": timeout},
        timeout,
    )
    tiempo_ms = round((time.monotonic() - inicio) * 1000)

    if hubo_timeout:
        return {"lenguaje": "sql", "filas": None, "columnas": None, "error": "Timeout de infraestructura.", "timeout": True, "tiempo_ms": tiempo_ms}

    try:
        resultado = json.loads(logs.decode(errors="replace").strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"lenguaje": "sql", "filas": None, "columnas": None, "error": "Salida invalida del runner.", "timeout": False, "tiempo_ms": tiempo_ms}

    resultado["lenguaje"] = "sql"
    resultado["tiempo_ms"] = tiempo_ms
    return resultado
