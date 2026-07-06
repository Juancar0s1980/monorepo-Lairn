"""
Descargador y preprocesador del dataset REAL ASSISTments 2009-2010.

ASSISTments es el dataset estandar del campo de Knowledge Tracing. Lo usan
papers clasicos (Piech 2015 - DKT, Pandey 2019 - SAKT) lo que permite
COMPARAR nuestros AUC con la literatura publicada.

Datos:
- ~4.000 estudiantes reales (secundaria, USA)
- ~525.000 interacciones reales
- ~110 skills de matematicas
- Acceso publico (sin login, sin registro)

Flujo:
1. Intenta descargar el CSV desde mirrors conocidos.
2. Si todos fallan, imprime instrucciones de descarga manual.
3. Procesa el CSV: limpia nulos, renombra columnas a nuestro schema.
4. Guarda en data/assistments.csv.
"""

# urllib estandar de Python (sin dependencias extra) para descargar
import urllib.request
import urllib.error
# Para validacion del archivo descargado
import hashlib
# Manipulacion del CSV
import pandas as pd
# Rutas
from pathlib import Path
# Mensajes de error claros
import sys


# Lista de mirrors conocidos (en orden de preferencia).
# Si encuentras una URL mas estable, agregala al inicio de la lista.
URLS_MIRRORS = [
    'https://raw.githubusercontent.com/jennyzhang0215/DKVMN/master/data/assist2009_updated/assist2009_updated_train.csv',
    'https://raw.githubusercontent.com/arghosh/AKT/master/data/assist2009_pid/assist2009_pid_train.csv',
]

# URL oficial para descarga manual (si los mirrors fallan)
URL_OFICIAL = 'https://sites.google.com/site/assistmentsdata/datasets/2009-2010-assistment-data'

# Ruta destino del CSV procesado.
# Usamos ruta ABSOLUTA basada en la ubicacion de ESTE archivo (__file__)
# para que funcione igual si se llama desde la raiz del proyecto o desde
# notebooks/. __file__ = ruta de descargar_assistments.py. .parent = data/.
# .parent.parent = raiz del proyecto. Asi siempre apuntamos a raiz/data/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUTA_DESTINO = PROJECT_ROOT / 'data' / 'assistments.csv'

# Tamano minimo aceptable para considerar la descarga exitosa (~1 MB)
TAMANO_MIN_BYTES = 1_000_000


def _intentar_descargar(url: str, destino: Path) -> bool:
    """
    Intenta descargar un archivo desde una URL.

    Recibe:
        url: URL del archivo a descargar.
        destino: ruta donde guardar.
    Devuelve:
        True si la descarga fue exitosa, False si fallo.
    """
    print(f'  Probando: {url[:80]}...')
    try:
        # Pedimos el archivo con timeout de 30s para no colgar la sesion
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        # Validamos que sea un archivo razonablemente grande (no error HTML)
        if len(data) < TAMANO_MIN_BYTES:
            print(f'  [FAIL] Archivo demasiado pequeno ({len(data)} bytes). Posible error.')
            return False
        # Guardamos a disco
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(data)
        print(f'  [OK] Descargado: {len(data):,} bytes -> {destino}')
        return True
    except urllib.error.HTTPError as e:
        print(f'  [FAIL] HTTP {e.code}: {e.reason}')
        return False
    except urllib.error.URLError as e:
        print(f'  [FAIL] Conexion: {e.reason}')
        return False
    except Exception as e:
        print(f'  [FAIL] {type(e).__name__}: {e}')
        return False


def _parsear_formato_dkvmn(ruta: Path) -> pd.DataFrame:
    """
    Parsea el formato DKVMN de ASSISTments (3 lineas por estudiante).

    Estructura del archivo:
        linea N+0: longitud de la secuencia del estudiante (ej. 64)
        linea N+1: skill_ids separados por coma (64 valores)
        linea N+2: correctness 0/1 separados por coma (64 valores)
        ... y se repite para cada estudiante

    Recibe:
        ruta: archivo crudo descargado.
    Devuelve:
        DataFrame con user_id, skill_name, correct, order_id.
    """
    # Leemos todas las lineas del archivo
    with open(ruta, 'r', encoding='utf-8') as f:
        lineas = [l.strip() for l in f if l.strip()]

    # Acumulador de filas
    filas = []
    # Contador de estudiantes (user_id incremental)
    user_id = 0
    # Procesamos en bloques de 3 lineas
    i = 0
    while i < len(lineas):
        try:
            # Longitud declarada de la secuencia
            n = int(lineas[i])
            # Listas de skills y correctness (deben tener longitud n)
            skills = lineas[i + 1].split(',')
            corrects = lineas[i + 2].split(',')
            # Validacion: las 3 longitudes deben coincidir
            if not (len(skills) == n == len(corrects)):
                # Si no coincide, intentamos con el menor (datos sucios)
                n = min(len(skills), len(corrects))
            # Generamos las filas para este estudiante
            for t in range(n):
                filas.append({
                    'user_id': user_id,
                    'skill_name': f'skill_{skills[t].strip()}',  # prefijo para ser texto
                    'correct': int(corrects[t].strip()),
                    'order_id': t,  # se ajusta luego por skill
                })
            user_id += 1
            i += 3
        except (ValueError, IndexError) as e:
            # Linea malformada -> saltamos un bloque
            print(f'  [WARN] Bloque malformado en linea {i}: {e}')
            i += 3

    df = pd.DataFrame(filas)
    return df


def _procesar_csv_assistments(ruta_csv_crudo: Path) -> pd.DataFrame:
    """
    Convierte el archivo crudo de ASSISTments a nuestro schema estandar.

    Detecta automaticamente el formato:
    - Formato DKVMN (lineas de 3): el que usan los mirrors de papers DKT/SAKT.
    - Formato CSV tabular: el original con columnas user_id, skill_name, etc.

    Recibe:
        ruta_csv_crudo: ruta del CSV descargado.
    Devuelve:
        DataFrame en schema Lairn (user_id, skill_name, correct, order_id).
    """
    # Leemos las primeras lineas para detectar el formato
    with open(ruta_csv_crudo, 'r', encoding='utf-8', errors='ignore') as f:
        primera = f.readline().strip()

    # Heuristica: si la primera linea es solo un numero -> formato DKVMN
    if primera.isdigit():
        print('  Formato detectado: DKVMN (3-lineas-por-estudiante)')
        df = _parsear_formato_dkvmn(ruta_csv_crudo)
    else:
        # Formato CSV tabular tradicional
        print('  Formato detectado: CSV tabular')
        try:
            df = pd.read_csv(ruta_csv_crudo, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(ruta_csv_crudo, low_memory=False, encoding='latin-1')
        # Mapeo de columnas tipico de ASSISTments tabular
        candidatos = {
            'user_id': ['user_id', 'student_id', 'studentId'],
            'skill_name': ['skill_name', 'skill', 'skillName', 'kc'],
            'correct': ['correct', 'is_correct', 'isCorrect'],
            'order_id': ['order_id', 'orderId', 'timestamp', 'time'],
        }
        columnas_mapeadas = {}
        for nombre_estandar, posibles in candidatos.items():
            encontrado = next((c for c in posibles if c in df.columns), None)
            if encontrado is None:
                raise ValueError(
                    f'No se encontro columna para "{nombre_estandar}". '
                    f'Disponibles: {df.columns.tolist()[:15]}'
                )
            columnas_mapeadas[encontrado] = nombre_estandar
        df = df.rename(columns=columnas_mapeadas)[['user_id', 'skill_name', 'correct', 'order_id']]

    # --- Limpieza comun ---
    n_antes = len(df)
    df = df.dropna()
    if n_antes - len(df) > 0:
        print(f'  Eliminadas {n_antes - len(df):,} filas con nulos')

    # Forzamos tipos
    df['user_id'] = df['user_id'].astype(int)
    df['skill_name'] = df['skill_name'].astype(str)
    df['correct'] = df['correct'].astype(int)
    # Normalizamos order_id como contador 0..N-1 por cada (user, skill)
    df = df.sort_values(['user_id', 'skill_name', 'order_id'])
    df['order_id'] = df.groupby(['user_id', 'skill_name']).cumcount().astype(int)
    df = df.reset_index(drop=True)

    # Validacion final
    assert df['correct'].isin([0, 1]).all(), 'correct no es binario'
    return df


def _imprimir_instrucciones_manuales() -> None:
    """Imprime guia clara para descargar manualmente si los mirrors fallan."""
    print('\n' + '=' * 70)
    print('NO SE PUDO DESCARGAR AUTOMATICAMENTE')
    print('=' * 70)
    print('\nOpciones para descargar manualmente:')
    print(f'\n  1. Sitio oficial: {URL_OFICIAL}')
    print('     -> registrate (gratis), descarga "skill_builder_data_corrected.csv"')
    print('\n  2. Kaggle: https://www.kaggle.com/datasets/nicolaswattiez/skillbuilder-data-2009-2010')
    print('     -> requiere cuenta Kaggle')
    print('\n  3. Mirror academico de tu universidad o profesor')
    print('\nUna vez tengas el archivo:')
    print(f'  - Coloca el CSV en: {RUTA_DESTINO.absolute()}')
    print('  - Vuelve a correr este script con --procesar-local')
    print('=' * 70)


def descargar_y_procesar(forzar: bool = False, procesar_local: bool = False) -> pd.DataFrame:
    """
    Funcion principal: descarga (si necesario), procesa y devuelve el DataFrame.

    Recibe:
        forzar: si True, redescarga incluso si el archivo ya existe.
        procesar_local: si True, salta la descarga y procesa el archivo local.
    Devuelve:
        DataFrame con schema estandar Lairn.
    """
    # Si ya existe el procesado y no se fuerza, lo cargamos directo
    if RUTA_DESTINO.exists() and not forzar:
        print(f'[OK] Ya existe: {RUTA_DESTINO}')
        return pd.read_csv(RUTA_DESTINO)

    # CSV crudo (antes de procesar) se guarda como .raw.csv
    ruta_crudo = RUTA_DESTINO.with_suffix('.raw.csv')

    # Si procesar_local, asumimos que el usuario ya coloco el CSV crudo
    if procesar_local:
        if not ruta_crudo.exists():
            raise FileNotFoundError(
                f'No existe {ruta_crudo}. Coloca ahi el CSV descargado manualmente.'
            )
        print(f'[INFO] Procesando archivo local: {ruta_crudo}')
    else:
        # Intentamos descargar de cada mirror en orden
        print('[INFO] Descargando ASSISTments...')
        exitoso = False
        for url in URLS_MIRRORS:
            if _intentar_descargar(url, ruta_crudo):
                exitoso = True
                break
        if not exitoso:
            _imprimir_instrucciones_manuales()
            sys.exit(1)

    # Procesar el CSV crudo a nuestro schema
    print('[INFO] Procesando CSV a schema Lairn...')
    df = _procesar_csv_assistments(ruta_crudo)

    # Guardar procesado
    RUTA_DESTINO.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_DESTINO, index=False)
    print(f'\n[OK] Procesado y guardado: {RUTA_DESTINO}')
    print(f'     {len(df):,} interacciones, {df["user_id"].nunique():,} estudiantes, '
          f'{df["skill_name"].nunique()} skills')

    return df


if __name__ == '__main__':
    # Permite forzar redescarga o procesar archivo local desde linea de comandos
    forzar = '--forzar' in sys.argv
    procesar_local = '--procesar-local' in sys.argv
    descargar_y_procesar(forzar=forzar, procesar_local=procesar_local)
