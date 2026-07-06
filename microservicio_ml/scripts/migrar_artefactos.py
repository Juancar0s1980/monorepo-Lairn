"""
Migracion unica: re-guarda los model.pkl para que referencien la nueva ruta de
modulo (ml.modelos.bkt / ml.modelos.dkt) en vez de la antigua (src.bkt_modelo).

Los pickles guardan la ruta del modulo de la clase. Al reorganizar el proyecto
esa ruta cambio, asi que aqui:
  1) registramos alias de los modulos viejos -> nuevos,
  2) cargamos cada pkl (que asi resuelve a las clases NUEVAS),
  3) lo volvemos a guardar (ya con la ruta nueva).

Uso (desde microservicio_ml/, con el entorno de entrenamiento activo):
    python scripts/migrar_artefactos.py
"""

import pickle
import sys
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Modulos nuevos donde viven ahora las clases de los modelos.
import ml.modelos.bkt as bkt_nuevo  # noqa: E402

# Alias para que los pkl viejos (que dicen 'src.bkt_modelo'/'src.dkt_modelo')
# resuelvan a las clases NUEVAS. DKT solo se aliasa si torch esta disponible.
_paquete_src = types.ModuleType("src")
_paquete_src.__path__ = []  # marcar como paquete
sys.modules.setdefault("src", _paquete_src)
sys.modules["src.bkt_modelo"] = bkt_nuevo

try:
    import ml.modelos.dkt as dkt_nuevo  # requiere torch
    sys.modules["src.dkt_modelo"] = dkt_nuevo
    _dkt_ok = True
except Exception as e:  # torch no instalado -> se omiten los DKT
    print(f"[AVISO] No se pudo importar ml.modelos.dkt ({e}); se omiten los DKT.")
    _dkt_ok = False


def migrar():
    dir_artefactos = RAIZ / "artefactos"
    for pkl in sorted(dir_artefactos.glob("*/model.pkl")):
        es_dkt = pkl.parent.name.startswith("dkt")
        if es_dkt and not _dkt_ok:
            print(f"[SKIP]  {pkl}  (DKT sin torch)")
            continue
        with open(pkl, "rb") as f:
            obj = pickle.load(f)
        with open(pkl, "wb") as f:
            pickle.dump(obj, f)
        print(f"[OK]    {pkl}  ->  {type(obj).__module__}.{type(obj).__name__}")


if __name__ == "__main__":
    migrar()
    print("Migracion terminada.")
