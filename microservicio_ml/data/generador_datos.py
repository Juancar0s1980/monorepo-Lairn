"""
Generador de datos sinteticos AVANZADO para Knowledge Tracing - Lairn.

A diferencia de un generador trivial (sigmoide pura), este simulador
introduce 7 FUENTES DE VARIABILIDAD que reproducen fenomenos observados
en datos reales de aprendizaje:

  1. PERFILES de estudiante: rapido / promedio / lento / abandonador.
  2. DIFICULTAD por concepto: seno < coseno < regla_cadena.
  3. DEPENDENCIAS curriculares: dominar 'derivada_seno' acelera el
     aprendizaje de 'derivada_coseno' y 'regla_cadena' (transferencia).
  4. CURVA DE OLVIDO: si no practicas un concepto durante varios pasos,
     P(dominio) decae exponencialmente (olvido a la Ebbinghaus).
  5. FATIGA: a partir de cierto numero de interacciones por sesion baja
     la atencion y la P(acertar).
  6. RUIDO PUNTUAL: ~5% de interacciones tienen un "evento" aleatorio
     (despiste, suerte, conexion cortada) que vuelve la respuesta azar.
  7. SESIONES VARIABLES: power-law -> pocos estudiantes hacen muchas
     interacciones, muchos hacen pocas (mas realista que uniforme).

Esto produce datos donde BKT, DKT y SAKT realmente tienen algo distinto
que aprender (BKT no captura olvido/dependencias; DKT/SAKT si).

API publica:
- generar_dataset(n_estudiantes, conceptos, ..., seed)
- guardar_dataset(df, ruta)
"""

# Operaciones numericas y semillas reproducibles
import numpy as np
# DataFrame de salida
import pandas as pd
# Rutas multiplataforma
from pathlib import Path


# ============================================================================
# CONSTANTES DEL MODELO DE COMPORTAMIENTO
# ============================================================================

# Semilla por defecto para reproducibilidad
SEED_DEFAULT = 42

# Conceptos por defecto (ordenados por dependencia curricular)
CONCEPTOS_DEFAULT = ['derivada_seno', 'derivada_coseno', 'regla_cadena']

# --- 1. Perfiles de estudiante ---
# Cada perfil tiene su propia curva de aprendizaje (alpha, beta), tasa de
# olvido y proporcion poblacional. Suman 1.0 (100% de estudiantes cubiertos).
PERFILES = {
    'rapido':   {'alpha': 0.40, 'beta': -0.30, 'olvido': 0.020, 'prop': 0.15},
    'promedio': {'alpha': 0.25, 'beta': -1.00, 'olvido': 0.050, 'prop': 0.60},
    'lento':    {'alpha': 0.12, 'beta': -1.60, 'olvido': 0.090, 'prop': 0.20},
    'rinde':    {'alpha': 0.06, 'beta': -2.20, 'olvido': 0.150, 'prop': 0.05},
}

# --- 2. Dificultad intrinseca de cada concepto ---
# Se RESTA al logit. Positivo = mas dificil (baja P(acertar)).
DIFICULTAD_CONCEPTO = {
    'derivada_seno':   0.0,   # base
    'derivada_coseno': 0.3,   # un poco mas dificil
    'regla_cadena':    1.0,   # mucho mas dificil (requiere composicion)
}

# --- 3. Dependencias curriculares ---
# Si el estudiante ya domina el pre-requisito, su logit recibe un BOOST.
# Estructura: concepto -> (pre-requisito, magnitud del boost).
DEPENDENCIAS = {
    'derivada_coseno': ('derivada_seno', 0.40),
    'regla_cadena':    ('derivada_seno', 0.50),
}

# --- 4. Curva de olvido ---
# Cada paso sin practicar un concepto reduce P(dominio) por factor (1 - olvido).
# El parametro olvido viene del perfil (ver PERFILES).

# --- 5. Fatiga ---
# A partir de UMBRAL_FATIGA interacciones acumuladas hoy, baja la atencion.
UMBRAL_FATIGA = 20
PENALIZACION_FATIGA = 0.04  # por cada interaccion extra sobre el umbral

# --- 6. Ruido puntual ---
# Probabilidad de que una interaccion sea "evento aleatorio" (50/50)
PROB_RUIDO = 0.05

# --- 7. Sesiones variables ---
# Distribucion del numero total de interacciones POR ESTUDIANTE (no por skill).
# Power-law: la mayoria tiene pocas, unos pocos tienen muchas.
MIN_SESIONES_TOTALES = 15   # un estudiante muy basico
MAX_SESIONES_TOTALES = 90   # un estudiante muy intenso
EXPONENTE_POWERLAW = 1.5    # >1: sesga hacia valores bajos (mas realista)

# Umbral para considerar concepto "dominado" (afecta dependencias y olvido)
UMBRAL_DOMINIO = 0.70


def _sigmoide(x: float) -> float:
    """Sigmoide estandar para mapear logits a probabilidades."""
    return 1.0 / (1.0 + np.exp(-x))


def _asignar_perfil(rng: np.random.Generator) -> str:
    """Sortea un perfil de estudiante segun las proporciones de PERFILES."""
    # Lista de nombres y sus probabilidades en el mismo orden
    nombres = list(PERFILES.keys())
    pesos = np.array([PERFILES[n]['prop'] for n in nombres])
    # Normalizamos por si las proporciones no suman exactamente 1
    pesos = pesos / pesos.sum()
    # rng.choice respeta los pesos
    return str(rng.choice(nombres, p=pesos))


def _muestrear_n_sesiones(rng: np.random.Generator) -> int:
    """
    Muestrea el numero de sesiones totales que hara un estudiante.

    Usa power-law: muchos estudiantes con pocas sesiones, pocos con muchas.
    """
    # Power-law inversa: u ~ U(0,1) -> N = MIN * u^(-1/exp), truncado a MAX
    u = rng.random()
    # Formula de inverse-CDF para Pareto/power-law
    n = MIN_SESIONES_TOTALES * (u ** (-1.0 / EXPONENTE_POWERLAW))
    # Truncamos al maximo razonable
    return int(min(n, MAX_SESIONES_TOTALES))


def _muestrear_secuencia_conceptos(n: int, conceptos: list,
                                     rng: np.random.Generator) -> list:
    """
    Decide el orden en que el estudiante practica los conceptos.

    Sigue un orden curricular suave: empieza mas por 'derivada_seno', luego
    introduce 'derivada_coseno', y al final 'regla_cadena'. Pero permite
    cierta mezcla (intercalado) como un curso real.

    Recibe:
        n: numero total de interacciones del estudiante.
        conceptos: lista de conceptos disponibles.
        rng: generador aleatorio.
    Devuelve:
        Lista de longitud n con el concepto practicado en cada paso.
    """
    # Probabilidad de elegir cada concepto cambia segun el progreso temporal.
    # En tercio 1: peso fuerte a primer concepto (0.7, 0.2, 0.1)
    # En tercio 2: (0.3, 0.5, 0.2)
    # En tercio 3: (0.2, 0.3, 0.5)
    pesos_por_fase = [
        np.array([0.70, 0.20, 0.10]),
        np.array([0.30, 0.50, 0.20]),
        np.array([0.20, 0.30, 0.50]),
    ]
    secuencia = []
    for i in range(n):
        # Determinamos en que tercio estamos
        fase = min(2, int(3 * i / n))
        # Tomamos los pesos correspondientes (recortados al numero de conceptos)
        pesos = pesos_por_fase[fase][:len(conceptos)]
        pesos = pesos / pesos.sum()  # renormalizar
        # Elegimos un concepto con esos pesos
        idx = rng.choice(len(conceptos), p=pesos)
        secuencia.append(conceptos[idx])
    return secuencia


def _simular_estudiante(user_id: int, n_sesiones: int, conceptos: list,
                         perfil_nombre: str, rng: np.random.Generator) -> list:
    """
    Simula la trayectoria completa de UN estudiante a traves de sus sesiones.

    Para cada interaccion calcula la P(acertar) considerando:
    - Perfil del estudiante (alpha, beta, olvido)
    - Dificultad del concepto
    - Estado actual de aprendizaje en el concepto
    - Boost por dominio de pre-requisitos
    - Olvido desde la ultima practica del concepto
    - Fatiga acumulada
    - Ruido puntual

    Recibe:
        user_id: id numerico del estudiante.
        n_sesiones: numero total de interacciones a simular.
        conceptos: lista de conceptos disponibles.
        perfil_nombre: clave en PERFILES.
        rng: generador aleatorio.
    Devuelve:
        Lista de dicts con las interacciones generadas (en orden temporal).
    """
    # Extraemos parametros del perfil
    perfil = PERFILES[perfil_nombre]
    alpha = perfil['alpha']
    beta = perfil['beta']
    tasa_olvido = perfil['olvido']

    # Decidimos el orden curricular de conceptos para este estudiante
    secuencia_conceptos = _muestrear_secuencia_conceptos(n_sesiones, conceptos, rng)

    # Estado interno por concepto:
    # - dominio[c]: nivel actual estimado de dominio en (0, 1)
    # - n_practicas[c]: cuantas veces practicado el concepto
    # - paso_ultimo[c]: en que paso global se practico por ultima vez
    dominio = {c: 0.0 for c in conceptos}
    n_practicas = {c: 0 for c in conceptos}
    paso_ultimo = {c: -1 for c in conceptos}

    interacciones = []

    # Iteramos cada paso temporal
    for paso, skill in enumerate(secuencia_conceptos):
        # --- 4. Aplicar OLVIDO a todos los conceptos NO practicados recientemente ---
        for c in conceptos:
            if paso_ultimo[c] >= 0:
                pasos_sin_practicar = paso - paso_ultimo[c]
                # Decay exponencial: dominio *= (1 - olvido)^pasos
                if pasos_sin_practicar > 0:
                    dominio[c] *= (1.0 - tasa_olvido) ** pasos_sin_practicar

        # --- Calculo de la P(acertar) en esta interaccion ---
        # Logit base: depende de cuantas veces practicado ESTE skill y del perfil
        t_skill = n_practicas[skill]
        logit = alpha * t_skill + beta

        # --- 2. Restar dificultad del concepto ---
        logit -= DIFICULTAD_CONCEPTO.get(skill, 0.0)

        # --- 3. Boost por dependencia: si el pre-requisito esta dominado ---
        if skill in DEPENDENCIAS:
            prereq, magnitud = DEPENDENCIAS[skill]
            if dominio[prereq] >= UMBRAL_DOMINIO:
                logit += magnitud

        # --- Bonus por dominio actual del propio skill ---
        # Si ya tiene cierto dominio, sigue acertando con mas probabilidad
        logit += 1.5 * dominio[skill]

        # --- 5. Penalizacion por FATIGA (interacciones acumuladas hoy) ---
        if paso > UMBRAL_FATIGA:
            logit -= PENALIZACION_FATIGA * (paso - UMBRAL_FATIGA)

        # Convertimos logit a probabilidad
        p_acertar = _sigmoide(logit)

        # --- 6. RUIDO puntual: con prob PROB_RUIDO, la respuesta es azar 50/50 ---
        if rng.random() < PROB_RUIDO:
            p_acertar = 0.5

        # Sorteo de la respuesta
        correct = int(rng.random() < p_acertar)

        # --- Actualizar estado de dominio ---
        # Si acerto, dominio sube un poco; si fallo, sube menos (pero no baja)
        # Esta es una version simplificada de la actualizacion BKT
        if correct:
            dominio[skill] = min(1.0, dominio[skill] + 0.10)
        else:
            dominio[skill] = min(1.0, dominio[skill] + 0.03)

        # Registrar la interaccion. order_id es local al skill (1, 2, 3...
        # por cada concepto), como en pyBKT y la mayoria de literatura.
        interacciones.append({
            'user_id': user_id,
            'skill_name': skill,
            'correct': correct,
            'order_id': t_skill,        # n-esima vez que ve ESTE skill
            'paso_global': paso,        # n-esimo evento del estudiante (debug)
            'perfil': perfil_nombre,    # para inspeccion / debug
        })

        # Actualizamos contadores
        n_practicas[skill] += 1
        paso_ultimo[skill] = paso

    return interacciones


def generar_dataset(
    n_estudiantes: int = 1000,
    conceptos: list = None,
    min_interacciones: int = None,  # IGNORADO (compatibilidad API antigua)
    max_interacciones: int = None,  # IGNORADO (compatibilidad API antigua)
    seed: int = SEED_DEFAULT,
) -> pd.DataFrame:
    """
    Genera un DataFrame de interacciones con variabilidad realista.

    Recibe:
        n_estudiantes: cantidad de estudiantes a simular.
        conceptos: lista de skills (default 3 de calculo).
        min_interacciones, max_interacciones: ignorados (compatibilidad).
            El numero de interacciones por estudiante se muestrea via
            power-law para mayor realismo (ver MIN/MAX_SESIONES_TOTALES).
        seed: semilla.
    Devuelve:
        DataFrame con columnas user_id, skill_name, correct, order_id,
        mas dos columnas auxiliares (paso_global, perfil) para depuracion.
    """
    if conceptos is None:
        conceptos = CONCEPTOS_DEFAULT

    # Generador NumPy moderno con semilla fija
    rng = np.random.default_rng(seed)
    todas_interacciones = []

    # Recorremos cada estudiante
    for user_id in range(n_estudiantes):
        # 1. Asignar perfil aleatorio segun proporciones poblacionales
        perfil = _asignar_perfil(rng)
        # 7. Muestrear cuantas sesiones totales hara (power-law)
        n_sesiones = _muestrear_n_sesiones(rng)
        # Simular su trayectoria completa
        interacciones = _simular_estudiante(user_id, n_sesiones, conceptos, perfil, rng)
        todas_interacciones.extend(interacciones)

    # Convertir a DataFrame y forzar tipos
    df = pd.DataFrame(todas_interacciones)
    df['user_id'] = df['user_id'].astype(int)
    df['skill_name'] = df['skill_name'].astype(str)
    df['correct'] = df['correct'].astype(int)
    df['order_id'] = df['order_id'].astype(int)

    # VALIDACION antes de devolver
    assert df.isnull().sum().sum() == 0, 'Nulos en dataset'
    assert df['correct'].isin([0, 1]).all(), 'correct no binario'
    # Cobertura por concepto: al menos un estudiante practico cada uno
    assert set(df['skill_name'].unique()) <= set(conceptos), 'Skills inesperados'

    return df


def guardar_dataset(df: pd.DataFrame, ruta: str = 'data/interacciones.csv') -> None:
    """
    Persiste el DataFrame a CSV (solo columnas estandar).

    Recibe:
        df: DataFrame de interacciones.
        ruta: ruta del CSV de salida.
    """
    ruta_path = Path(ruta)
    ruta_path.parent.mkdir(parents=True, exist_ok=True)
    # Guardamos solo las 4 columnas estandar (sin paso_global, perfil)
    cols_estandar = ['user_id', 'skill_name', 'correct', 'order_id']
    df[cols_estandar].to_csv(ruta_path, index=False)


# Prueba rapida y reporte de variabilidad
if __name__ == '__main__':
    df = generar_dataset(n_estudiantes=500)
    print(f'Filas totales: {len(df):,}')
    print(f'Estudiantes: {df["user_id"].nunique()}')
    print(f'Tasa acierto global: {df["correct"].mean():.3f}\n')

    print('Tasa de acierto por concepto:')
    print(df.groupby('skill_name')['correct'].agg(['mean', 'count']).round(3), '\n')

    print('Tasa de acierto por perfil:')
    print(df.groupby('perfil')['correct'].agg(['mean', 'count']).round(3), '\n')

    print('Distribucion de interacciones por estudiante:')
    n_por_user = df.groupby('user_id').size()
    print(n_por_user.describe().round(1))
