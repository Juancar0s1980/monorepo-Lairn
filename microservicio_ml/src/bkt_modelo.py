"""
Implementacion en NumPy puro de Bayesian Knowledge Tracing (BKT).

Sustituye a pyBKT cuando no se puede instalar (Windows sin MSVC, Python muy
nuevo, etc.). API compatible: .fit(df, skills), .predict(df), .params().

Modelo:
- HMM de 2 estados (no_dominado=0, dominado=1) por cada skill.
- Restriccion BKT clasica: NO hay olvido (P(dominado -> no_dominado) = 0).
- 4 parametros por skill: p_init, p_learn, p_guess, p_slip.

Entrenamiento:
- Algoritmo Baum-Welch (Expectation-Maximization para HMM).
- Multiples reinicios aleatorios para evitar minimos locales.
- Identifiability constraint: p_guess < 0.5, p_slip < 0.5 (truncamos cada
  iteracion para evitar que el modelo aprenda al reves).

Prediccion:
- Forward pass: para cada interaccion devuelve P(L_t) y P(correcto_t).
"""

# numpy para algebra vectorizada y semillas reproducibles
import numpy as np
# pandas para manipular el DataFrame de interacciones
import pandas as pd

# Constante muy pequena para evitar log(0) y divisiones por cero
EPS = 1e-12


def _forward_backward(obs: np.ndarray, p_init: float, p_learn: float,
                       p_guess: float, p_slip: float):
    """
    Calcula alpha, beta y log-verosimilitud de una secuencia de observaciones.

    Recibe:
        obs: array (T,) con 0/1 (incorrecto/correcto).
        p_init, p_learn, p_guess, p_slip: parametros BKT del skill.
    Devuelve:
        (alpha, beta, log_lik) con alpha y beta de shape (T, 2).
    """
    # Longitud de la secuencia (numero de interacciones)
    T = len(obs)

    # --- Matrices del HMM ---
    # Probabilidades iniciales: P(L_1 = 0) = 1-p_init, P(L_1 = 1) = p_init
    pi = np.array([1.0 - p_init, p_init])
    # Matriz de transicion 2x2 con restriccion BKT (sin olvido):
    # fila 0 (no_dominado) -> [1-p_learn, p_learn]
    # fila 1 (dominado)    -> [0, 1]
    A = np.array([[1.0 - p_learn, p_learn], [0.0, 1.0]])

    # --- Probabilidades de emision por estado ---
    # P(o | estado): para o=0 (incorrecto) y o=1 (correcto)
    # b[s, o]: estado s emite observacion o
    b = np.array([
        [1.0 - p_guess, p_guess],     # estado 0 (no_dominado): 1-p_guess incorrecto, p_guess correcto
        [p_slip,       1.0 - p_slip], # estado 1 (dominado):    p_slip incorrecto, 1-p_slip correcto
    ])

    # --- Forward pass: alpha[t, s] = P(o_1..o_t, L_t=s) ---
    # Inicializamos matriz alpha (T filas, 2 columnas para los 2 estados)
    alpha = np.zeros((T, 2))
    # Usaremos escalado por renglon para evitar underflow numerico
    # scaling[t] = factor de normalizacion en el paso t
    scaling = np.zeros(T)

    # Paso inicial (t=0): alpha_1(s) = pi_s * b[s, o_1]
    alpha[0] = pi * b[:, obs[0]]
    # Factor de escala = suma de alpha en t=0 (P(o_1))
    scaling[0] = alpha[0].sum() + EPS
    # Normalizamos para que sume 1 (mantiene proporciones)
    alpha[0] /= scaling[0]

    # Recursion: alpha_t(s) = (sum_s' alpha_{t-1}(s') * A[s', s]) * b[s, o_t]
    for t in range(1, T):
        # Propagamos por la matriz de transicion (alpha_{t-1} @ A da contribuciones por destino)
        alpha[t] = (alpha[t - 1] @ A) * b[:, obs[t]]
        # Escalamos para estabilidad numerica
        scaling[t] = alpha[t].sum() + EPS
        alpha[t] /= scaling[t]

    # --- Backward pass: beta[t, s] = P(o_{t+1}..o_T | L_t=s) ---
    beta = np.zeros((T, 2))
    # En el ultimo paso beta es 1 para ambos estados
    beta[T - 1] = 1.0

    # Recursion hacia atras: beta_t(s) = sum_s' A[s,s'] * b[s', o_{t+1}] * beta_{t+1}(s')
    for t in range(T - 2, -1, -1):
        beta[t] = A @ (b[:, obs[t + 1]] * beta[t + 1])
        # Aplicamos el mismo escalado para mantener coherencia con alpha
        beta[t] /= scaling[t + 1]

    # Log-verosimilitud: sum log(scaling) recupera log P(obs) (ver Rabiner 1989)
    log_lik = float(np.sum(np.log(scaling)))

    return alpha, beta, log_lik


def _em_step(secuencias: list, params: dict) -> tuple:
    """
    Un paso de Baum-Welch (EM) sobre TODAS las secuencias de un skill.

    Recibe:
        secuencias: lista de arrays 1D con las observaciones de cada estudiante.
        params: dict con p_init, p_learn, p_guess, p_slip actuales.
    Devuelve:
        (nuevos_params, log_lik_total): parametros actualizados y log-verosimilitud.
    """
    # Desempaquetamos parametros para legibilidad
    p_init = params['p_init']
    p_learn = params['p_learn']
    p_guess = params['p_guess']
    p_slip = params['p_slip']

    # Acumuladores para el M-step (numerador y denominador de cada estimador)
    # gamma_1(1) acumulado sobre todas las secuencias -> nuevo p_init
    sum_gamma1_dominado = 0.0
    # Numero total de secuencias (denominador de p_init)
    n_secs = 0

    # Para p_learn: sum xi_t(0,1) / sum gamma_t(0)  (transicion no->dom)
    sum_xi_01 = 0.0
    sum_gamma_no_dom = 0.0  # excluye el ultimo paso (no hay transicion despues)

    # Para p_guess: sum gamma_t(0) * I(o_t=1) / sum gamma_t(0)
    sum_gamma_no_dom_correct = 0.0
    sum_gamma_no_dom_all = 0.0  # incluye TODOS los pasos (tambien el ultimo)

    # Para p_slip: sum gamma_t(1) * I(o_t=0) / sum gamma_t(1)
    sum_gamma_dom_incorrect = 0.0
    sum_gamma_dom_all = 0.0

    # Acumulador de log-verosimilitud total
    log_lik_total = 0.0

    # Recorremos cada secuencia (un estudiante = una secuencia)
    for obs in secuencias:
        T = len(obs)
        # Saltamos secuencias vacias por seguridad
        if T == 0:
            continue

        # Calculamos alpha, beta y log-likelihood de la secuencia
        alpha, beta, log_lik = _forward_backward(obs, p_init, p_learn, p_guess, p_slip)
        # Acumulamos verosimilitud total para reportar convergencia
        log_lik_total += log_lik

        # gamma_t(s) = P(L_t=s | observaciones) = alpha[t,s] * beta[t,s] (ya escalados)
        # Normalizamos por fila para garantizar suma=1
        gamma = alpha * beta
        gamma_sum = gamma.sum(axis=1, keepdims=True) + EPS
        gamma /= gamma_sum

        # Acumulamos gamma_1 del estado dominado (para nuevo p_init)
        sum_gamma1_dominado += gamma[0, 1]
        n_secs += 1

        # --- xi_t(s, s') = P(L_t=s, L_{t+1}=s' | obs) ---
        # Lo necesitamos solo para xi(0, 1) (transicion no_dom -> dom = p_learn)
        # Matriz de transicion y emision (necesarias para xi)
        A = np.array([[1.0 - p_learn, p_learn], [0.0, 1.0]])
        b = np.array([
            [1.0 - p_guess, p_guess],
            [p_slip,        1.0 - p_slip],
        ])

        # Iteramos cada par (t, t+1) para acumular xi y gammas
        for t in range(T - 1):
            # Denominador de xi: P(obs) ~ suma sobre estados
            # xi[s, s'] = alpha[t,s] * A[s,s'] * b[s', o_{t+1}] * beta[t+1, s']
            xi = (alpha[t][:, None] * A) * (b[:, obs[t + 1]] * beta[t + 1])[None, :]
            xi /= (xi.sum() + EPS)
            # Acumulamos xi(0, 1) = transicion no_dom -> dom en este paso
            sum_xi_01 += xi[0, 1]

            # Acumulamos gamma_t(0) = no_dominado en t (denominador de p_learn)
            sum_gamma_no_dom += gamma[t, 0]

        # --- Acumuladores de emisiones (sobre TODOS los pasos t=0..T-1) ---
        for t in range(T):
            # P(no_dominado en t)
            g0 = gamma[t, 0]
            # P(dominado en t)
            g1 = gamma[t, 1]
            sum_gamma_no_dom_all += g0
            sum_gamma_dom_all += g1
            # Si observacion fue correcta, suma al numerador de p_guess
            if obs[t] == 1:
                sum_gamma_no_dom_correct += g0
            # Si observacion fue incorrecta, suma al numerador de p_slip
            else:
                sum_gamma_dom_incorrect += g1

    # --- M-step: actualizamos los 4 parametros con los acumuladores ---
    # Nuevo p_init: promedio de P(L_1 = dominado) sobre todas las secuencias
    new_p_init = sum_gamma1_dominado / max(n_secs, 1)
    # Nuevo p_learn: tasa de transicion no_dom -> dom
    new_p_learn = sum_xi_01 / (sum_gamma_no_dom + EPS)
    # Nuevo p_guess: tasa de aciertos en estado no_dominado
    new_p_guess = sum_gamma_no_dom_correct / (sum_gamma_no_dom_all + EPS)
    # Nuevo p_slip: tasa de errores en estado dominado
    new_p_slip = sum_gamma_dom_incorrect / (sum_gamma_dom_all + EPS)

    # --- Identifiability constraint (buena practica #2) ---
    # BKT REQUIERE p_guess < 0.5 y p_slip < 0.5 para que los estados tengan
    # interpretacion coherente. Truncamos si EM intenta cruzar el limite.
    new_p_guess = float(np.clip(new_p_guess, 1e-3, 0.499))
    new_p_slip = float(np.clip(new_p_slip, 1e-3, 0.499))
    # Tambien acotamos init y learn a (0, 1) para evitar valores degenerados
    new_p_init = float(np.clip(new_p_init, 1e-3, 0.999))
    new_p_learn = float(np.clip(new_p_learn, 1e-3, 0.999))

    return {
        'p_init': new_p_init,
        'p_learn': new_p_learn,
        'p_guess': new_p_guess,
        'p_slip': new_p_slip,
    }, log_lik_total


class BKTModel:
    """
    Modelo BKT entrenable y predictivo. API compatible con pyBKT.

    Uso:
        modelo = BKTModel(seed=42, num_fits=5)
        modelo.fit(df_train, skills=['skill_a', 'skill_b'])
        df_pred = modelo.predict(df_test)  # anade correct_predictions, state_predictions
        print(modelo.params())
    """

    def __init__(self, seed: int = 42, num_fits: int = 5,
                 max_iter: int = 200, tol: float = 1e-4):
        """
        Recibe:
            seed: semilla para inicializaciones aleatorias.
            num_fits: numero de reinicios aleatorios del EM (mejor robustez).
            max_iter: iteraciones maximas por reinicio.
            tol: tolerancia de convergencia (delta de log-likelihood).
        """
        self.seed = seed
        self.num_fits = num_fits
        self.max_iter = max_iter
        self.tol = tol
        # Diccionario {skill_name: {p_init, p_learn, p_guess, p_slip}}
        self.params_ = {}
        # Lista de skills entrenados (preserva el orden)
        self.skills_ = []

    def _extraer_secuencias(self, df: pd.DataFrame, skill: str) -> list:
        """
        Convierte el DataFrame de un skill en lista de arrays por estudiante.

        Recibe:
            df: DataFrame con columnas user_id, skill_name, correct, order_id.
            skill: nombre del skill a extraer.
        Devuelve:
            Lista de arrays 1D (uno por estudiante) con secuencias ordenadas.
        """
        # Filtramos solo este skill
        df_skill = df[df['skill_name'] == skill]
        # Ordenamos por (user_id, order_id) para preservar la cronologia
        df_skill = df_skill.sort_values(['user_id', 'order_id'])
        # Agrupamos por estudiante y extraemos su secuencia como array
        return [g['correct'].to_numpy(dtype=int) for _, g in df_skill.groupby('user_id')]

    def _entrenar_skill(self, secuencias: list, seed: int) -> dict:
        """
        Entrena UN skill con multiples reinicios y devuelve los mejores parametros.

        Recibe:
            secuencias: lista de observaciones (una por estudiante).
            seed: semilla base para los reinicios.
        Devuelve:
            dict con los 4 parametros aprendidos.
        """
        # Generador de aleatorios con semilla fija para reproducibilidad
        rng = np.random.default_rng(seed)
        # Mejor resultado encontrado entre todos los reinicios
        mejor = None

        # Recorremos num_fits reinicios aleatorios (random restarts)
        for restart in range(self.num_fits):
            # Inicializacion aleatoria de los 4 parametros en rangos razonables
            params = {
                'p_init':  float(rng.uniform(0.05, 0.50)),  # inicial no muy alto
                'p_learn': float(rng.uniform(0.05, 0.40)),  # aprendizaje moderado
                'p_guess': float(rng.uniform(0.05, 0.30)),  # adivinanza < 0.5
                'p_slip':  float(rng.uniform(0.05, 0.20)),  # descuido < 0.5
            }

            # log-likelihood previo para chequear convergencia
            ll_prev = -np.inf

            # Loop principal de EM (hasta max_iter o convergencia)
            for it in range(self.max_iter):
                # Paso E + M combinado: devuelve nuevos params y log-lik actual
                params, ll = _em_step(secuencias, params)
                # Criterio de convergencia: cambio relativo de log-lik < tol
                if abs(ll - ll_prev) < self.tol:
                    break
                ll_prev = ll

            # Si este reinicio dio mejor verosimilitud, lo guardamos
            if mejor is None or ll > mejor['ll']:
                mejor = {'params': params, 'll': ll}

        return mejor['params']

    def fit(self, data: pd.DataFrame, skills: list) -> 'BKTModel':
        """
        Entrena el modelo BKT sobre todos los skills indicados.

        Recibe:
            data: DataFrame de interacciones (user_id, skill_name, correct, order_id).
            skills: lista de nombres de skills a entrenar.
        Devuelve:
            self (para encadenamiento estilo sklearn).
        """
        # Guardamos la lista de skills para preservar orden
        self.skills_ = list(skills)
        # Entrenamos cada skill por separado (HMMs independientes)
        for i, skill in enumerate(skills):
            # Extraemos las secuencias de este skill
            secs = self._extraer_secuencias(data, skill)
            # Si no hay datos para este skill, lo saltamos
            if not secs:
                continue
            # Cada skill usa una semilla derivada distinta para diversificar inits
            self.params_[skill] = self._entrenar_skill(secs, seed=self.seed + i)
        return self

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Predice correct_predictions y state_predictions para cada interaccion.

        Recibe:
            data: DataFrame de interacciones (mismas columnas que en fit).
        Devuelve:
            Copia del DataFrame con dos columnas nuevas:
            - correct_predictions: P(correcto en t | historia previa)
            - state_predictions: P(L_t = dominado | historia previa)
        """
        # Trabajamos sobre copia para no mutar el original
        df = data.copy().reset_index(drop=True)
        # Inicializamos las columnas nuevas con NaN
        df['correct_predictions'] = np.nan
        df['state_predictions'] = np.nan

        # Iteramos por cada (user_id, skill_name) ya que cada uno es una secuencia
        for (user_id, skill), grp in df.groupby(['user_id', 'skill_name']):
            # Si el skill no fue entrenado, dejamos NaN (no podemos predecir)
            if skill not in self.params_:
                continue
            # Parametros aprendidos para este skill
            p = self.params_[skill]
            # Ordenamos por order_id para procesar cronologicamente
            grp_ord = grp.sort_values('order_id')
            # Indices originales para asignar valores en el DataFrame de salida
            indices = grp_ord.index.to_numpy()

            # Estado actual: P(L_t = dominado), arranca en p_init
            p_l = p['p_init']

            # Procesamos cada interaccion en orden temporal
            for fila_idx, idx in enumerate(indices):
                # Observacion en este paso (0 incorrecto, 1 correcto)
                obs = int(grp_ord.iloc[fila_idx]['correct'])

                # Prediccion de acierto ANTES de ver la observacion:
                # P(correcto) = P(L)*(1-p_slip) + (1-P(L))*p_guess
                p_correct = p_l * (1.0 - p['p_slip']) + (1.0 - p_l) * p['p_guess']

                # Guardamos el estado y la prediccion (corresponden a ESTE paso)
                df.at[idx, 'state_predictions'] = p_l
                df.at[idx, 'correct_predictions'] = p_correct

                # Actualizamos P(L) con la observacion (regla de Bayes)
                if obs == 1:
                    # Numerador: P(L) * P(correcto | dominado) = P(L) * (1-p_slip)
                    num = p_l * (1.0 - p['p_slip'])
                    # Denominador: P(correcto) total (ya calculado)
                    den = p_correct + EPS
                else:
                    # Numerador: P(L) * P(incorrecto | dominado) = P(L) * p_slip
                    num = p_l * p['p_slip']
                    # Denominador: P(incorrecto) = 1 - P(correcto)
                    den = (1.0 - p_correct) + EPS

                # P(L | obs): posterior despues de la observacion
                p_l_post = num / den

                # Transicion al siguiente paso: P(L_{t+1}) = posterior + (1-posterior)*p_learn
                # (un estudiante en estado dominado se queda; uno no_dominado puede aprender)
                p_l = p_l_post + (1.0 - p_l_post) * p['p_learn']

        return df

    def params(self) -> pd.DataFrame:
        """
        Devuelve los parametros aprendidos como DataFrame para inspeccion.

        Devuelve:
            DataFrame con filas = skills y columnas [p_init, p_learn, p_guess, p_slip].
        """
        # Si no se ha entrenado, devolvemos DataFrame vacio con columnas correctas
        if not self.params_:
            return pd.DataFrame(columns=['p_init', 'p_learn', 'p_guess', 'p_slip'])
        # Construimos DataFrame respetando el orden de skills_
        filas = {s: self.params_[s] for s in self.skills_ if s in self.params_}
        return pd.DataFrame(filas).T[['p_init', 'p_learn', 'p_guess', 'p_slip']]


# Prueba rapida: solo corre si ejecutas este archivo directamente
if __name__ == "__main__":
    # Importamos generador desde la raiz del proyecto
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from data.generador_datos import generar_dataset

    # Generamos dataset y entrenamos para validar que funciona end-to-end
    df = generar_dataset()
    modelo = BKTModel(seed=42, num_fits=3, max_iter=100)
    modelo.fit(df, skills=['derivada_seno', 'derivada_coseno', 'regla_cadena'])
    print("Parametros aprendidos:")
    print(modelo.params())
    pred = modelo.predict(df)
    from sklearn.metrics import roc_auc_score
    print(f"AUC (sobre los mismos datos): {roc_auc_score(pred['correct'], pred['correct_predictions']):.4f}")
