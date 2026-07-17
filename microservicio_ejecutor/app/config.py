"""
Configuracion central del microservicio ejecutor.
"""

import os
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


class Ajustes:
    NOMBRE: str = "Microservicio Ejecutor Lairn - Sandbox de codigo"
    VERSION: str = "1.0.0"

    # --- Imagenes "runner" (una por lenguaje soportado) ---
    DIR_RUNNERS: Path = RAIZ_PROYECTO / "runners"
    IMAGENES: dict[str, str] = {
        "python": "lairn-runner-python:latest",
        "javascript": "lairn-runner-javascript:latest",
        "java": "lairn-runner-java:latest",
        "cpp": "lairn-runner-cpp:latest",
        "c": "lairn-runner-c:latest",
        "sql": "lairn-runner-sql:latest",
    }

    # Lenguajes compilados/interpretados que comparten el contrato genérico
    # {codigo, entrada} -> {stdout, stderr, exit_code, timeout, compilado?, error_compilacion?}.
    # SQL queda aparte porque su contrato es distinto (setup_sql + consulta -> filas).
    LENGUAJES_CODIGO: tuple[str, ...] = ("python", "javascript", "java", "cpp", "c")

    # --- Limites de la ejecucion (aplicados al contenedor efimero) ---
    TIMEOUT_DEFECTO_SEG: float = float(os.getenv("EJECUTOR_TIMEOUT_SEG", "5"))
    TIMEOUT_MAXIMO_SEG: float = float(os.getenv("EJECUTOR_TIMEOUT_MAXIMO_SEG", "10"))
    MEMORIA_LIMITE: str = os.getenv("EJECUTOR_MEMORIA", "128m")
    CPUS_LIMITE: float = float(os.getenv("EJECUTOR_CPUS", "0.5"))
    PIDS_LIMITE: int = int(os.getenv("EJECUTOR_PIDS_LIMITE", "64"))


ajustes = Ajustes()
