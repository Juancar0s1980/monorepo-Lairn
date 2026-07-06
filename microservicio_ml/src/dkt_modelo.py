"""
Implementacion de Deep Knowledge Tracing (DKT) con PyTorch.

Basado en Piech et al. (NeurIPS 2015): "Deep Knowledge Tracing".

Arquitectura:
    Input  -> Embedding 2*K dims (one-hot de (skill, correct))
           -> LSTM (hidden_dim)
           -> Linear (hidden_dim -> K)
           -> Sigmoid
    Output: P(correct) para CADA uno de los K skills, en cada paso temporal.

Para predecir un (skill_t, correct_t) usamos la salida del paso t-1 indexada
en el skill_t. Esto encapsula el "estado de conocimiento" antes de la
observacion (lo mismo que correct_predictions en BKT).

API compatible con BKTModel:
    .fit(data: DataFrame, skills: list)
    .predict(data: DataFrame) -> DataFrame con correct_predictions
"""

# numpy para operaciones auxiliares
import numpy as np
# pandas para los DataFrames de entrada/salida
import pandas as pd
# PyTorch para la red LSTM
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


# ============================================================================
# DATASET: convierte secuencias de (skill, correct) en tensores
# ============================================================================

class SecuenciasKT(Dataset):
    """
    Dataset de secuencias de Knowledge Tracing.

    Cada elemento es una secuencia de un estudiante:
        - skills: lista de skill_ids (enteros 0..K-1)
        - corrects: lista de 0/1
        - longitud: longitud real (para mask)
    """

    def __init__(self, secuencias: list, n_skills: int, max_len: int = 200):
        """
        Recibe:
            secuencias: lista de tuplas (skills_ids, corrects) por estudiante.
            n_skills: numero total de skills (K).
            max_len: longitud maxima de secuencia (truncar largos, padding cortos).
        """
        self.secuencias = secuencias
        self.n_skills = n_skills
        self.max_len = max_len

    def __len__(self) -> int:
        # Numero de secuencias = numero de estudiantes
        return len(self.secuencias)

    def __getitem__(self, idx: int) -> dict:
        """Devuelve un dict con tensores ya en formato para LSTM."""
        skills, corrects = self.secuencias[idx]
        # Truncamos si excede max_len (tomamos las primeras max_len interacciones)
        skills = skills[:self.max_len]
        corrects = corrects[:self.max_len]
        # Longitud real (antes de pad)
        L = len(skills)

        # --- Codificacion ONE-HOT 2K-dim ---
        # Posicion: skill_id * 2 + correct (estandar DKT)
        # Ej: skill=3, correct=1 -> indice 7 en vector de tamano 2K
        x = torch.zeros(self.max_len, 2 * self.n_skills, dtype=torch.float32)
        # Target: skill_id (para indexar la salida) y correct (label)
        target_skill = torch.zeros(self.max_len, dtype=torch.long)
        target_correct = torch.zeros(self.max_len, dtype=torch.float32)
        # Mask para ignorar pasos de padding al calcular loss
        mask = torch.zeros(self.max_len, dtype=torch.float32)

        for t in range(L):
            skill_t = int(skills[t])
            correct_t = int(corrects[t])
            # input en t = one-hot de (skill anterior, correct anterior)
            # DKT prediction setup: dado historial hasta t-1, predecimos t.
            # Es decir, x[t] codifica la respuesta del paso t (cuando ya fue dada)
            # y el target es la siguiente. Nosotros usamos el shift estandar:
            # x[t] codifica (skill_t, correct_t), output[t] predice skill_{t+1}.
            x[t, skill_t * 2 + correct_t] = 1.0
            target_skill[t] = skill_t
            target_correct[t] = float(correct_t)
            mask[t] = 1.0

        return {
            'x': x,
            'target_skill': target_skill,
            'target_correct': target_correct,
            'mask': mask,
            'length': L,
        }


# ============================================================================
# MODELO: LSTM de Knowledge Tracing
# ============================================================================

class DKTNet(nn.Module):
    """
    Red LSTM de Deep Knowledge Tracing.

    Input:  (B, T, 2K) one-hot de (skill, correct)
    Output: (B, T, K) probabilidad de acertar cada skill
    """

    def __init__(self, n_skills: int, hidden_dim: int = 64,
                 num_layers: int = 1, dropout: float = 0.2):
        """
        Recibe:
            n_skills: numero de skills (K).
            hidden_dim: dimension del estado oculto LSTM (default 64).
            num_layers: numero de capas LSTM apiladas.
            dropout: probabilidad de dropout entre capas LSTM.
        """
        super().__init__()
        self.n_skills = n_skills
        self.hidden_dim = hidden_dim
        # Capa LSTM: entrada 2K dims, salida hidden_dim
        # batch_first=True hace que el primer eje sea el batch (mas intuitivo)
        # dropout solo se aplica si num_layers > 1
        self.lstm = nn.LSTM(
            input_size=2 * n_skills,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        # Capa densa de salida: hidden_dim -> K (uno por skill)
        self.fc = nn.Linear(hidden_dim, n_skills)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Recibe:
            x: tensor (B, T, 2K) con one-hot de cada paso.
        Devuelve:
            tensor (B, T, K) con P(correct) para cada skill en cada paso.
        """
        # Pasamos por LSTM. h_t encapsula la historia hasta t.
        out, _ = self.lstm(x)
        # Proyectamos a K dimensiones y aplicamos sigmoide
        logits = self.fc(out)
        probs = torch.sigmoid(logits)
        return probs


# ============================================================================
# WRAPPER: API tipo sklearn / pyBKT
# ============================================================================

class DKTModel:
    """
    Wrapper de alto nivel sobre DKTNet. API:
        modelo = DKTModel(seed=42, hidden_dim=64, n_epochs=30)
        modelo.fit(df_train, skills=['s1','s2','s3'])
        df_pred = modelo.predict(df_test)  # anade correct_predictions
    """

    def __init__(self,
                 seed: int = 42,
                 hidden_dim: int = 64,
                 num_layers: int = 1,
                 dropout: float = 0.2,
                 n_epochs: int = 30,
                 batch_size: int = 32,
                 lr: float = 1e-3,
                 max_len: int = 200,
                 device: str = 'cpu',
                 verbose: bool = True):
        """
        Recibe:
            seed: semilla global (numpy + torch).
            hidden_dim: dim. del estado oculto LSTM.
            num_layers, dropout: arquitectura LSTM.
            n_epochs, batch_size, lr: hiperparametros de entrenamiento.
            max_len: longitud maxima de secuencia (trunca / padea).
            device: 'cpu' o 'cuda' (usa CPU por defecto).
            verbose: si True, imprime progreso cada epoca.
        """
        self.seed = seed
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.lr = lr
        self.max_len = max_len
        self.device = torch.device(device)
        self.verbose = verbose

        # Atributos que se llenan en fit()
        self.skill_to_id = {}    # mapeo skill_name -> id entero
        self.id_to_skill = {}    # mapeo inverso
        self.n_skills = 0        # K
        self.net = None          # red entrenada
        self.loss_history = []   # loss por epoca (para grafica)

    # --- Helpers ---
    def _extraer_secuencias(self, df: pd.DataFrame) -> list:
        """
        Convierte DataFrame en lista de (skill_ids, corrects) por estudiante.

        Ordena por (user_id, order_global) para preservar el orden temporal
        del estudiante a lo largo de TODOS sus skills (no solo dentro de uno).
        """
        # Creamos un order_global si no existe (orden absoluto por estudiante)
        df = df.copy()
        # Ordenamos por user_id y luego por order_id dentro de cada (user, skill).
        # Para DKT necesitamos UN orden global por estudiante; usamos el orden
        # de aparicion en el DataFrame que YA viene ordenado.
        df = df.sort_values(['user_id', 'skill_name', 'order_id'])
        # Reordenamos por user_id manteniendo el orden interno
        secuencias = []
        for user_id, grupo in df.groupby('user_id'):
            # Convertir skill_name a id entero (mapeo definido en fit)
            skills_ids = [self.skill_to_id[s] for s in grupo['skill_name'].tolist()
                          if s in self.skill_to_id]
            corrects = grupo['correct'].tolist()[:len(skills_ids)]
            if len(skills_ids) > 0:
                secuencias.append((skills_ids, corrects))
        return secuencias

    def fit(self, data: pd.DataFrame, skills: list) -> 'DKTModel':
        """
        Entrena el DKT sobre el DataFrame de interacciones.

        Recibe:
            data: DataFrame con columnas user_id, skill_name, correct, order_id.
            skills: lista de nombres de skills (define el vocabulario K).
        Devuelve:
            self.
        """
        # Reproducibilidad: fijamos semillas en numpy y torch
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)

        # Mapeo skill_name -> id entero
        self.skill_to_id = {s: i for i, s in enumerate(skills)}
        self.id_to_skill = {i: s for s, i in self.skill_to_id.items()}
        self.n_skills = len(skills)

        # Construir secuencias y DataLoader
        secuencias = self._extraer_secuencias(data)
        if self.verbose:
            print(f'   [DKT] {len(secuencias)} secuencias de entrenamiento, '
                  f'K={self.n_skills} skills, max_len={self.max_len}')

        dataset = SecuenciasKT(secuencias, self.n_skills, self.max_len)
        loader = DataLoader(dataset, batch_size=self.batch_size,
                            shuffle=True, num_workers=0)

        # Instanciar la red y el optimizador
        self.net = DKTNet(self.n_skills, self.hidden_dim,
                          self.num_layers, self.dropout).to(self.device)
        optim = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        # Loss: binary cross-entropy (sin reduccion para aplicar mascara)
        bce = nn.BCELoss(reduction='none')

        # --- Loop de entrenamiento ---
        self.net.train()
        self.loss_history = []
        for epoca in range(self.n_epochs):
            loss_acum = 0.0
            n_obs_acum = 0
            for batch in loader:
                # Mover tensores al device (CPU/GPU)
                x = batch['x'].to(self.device)               # (B, T, 2K)
                tgt_skill = batch['target_skill'].to(self.device)   # (B, T)
                tgt_correct = batch['target_correct'].to(self.device)  # (B, T)
                mask = batch['mask'].to(self.device)         # (B, T)

                # Forward pass: predicciones (B, T, K)
                preds_all = self.net(x)

                # --- SHIFT estandar DKT ---
                # El paso t predice la SIGUIENTE interaccion (t+1).
                # Tomamos pred[t-1, skill_t] para predecir correct_t.
                # Equivalente: descartamos el primer paso (no hay historia previa).
                preds_shift = preds_all[:, :-1, :]          # (B, T-1, K)
                tgt_skill_shift = tgt_skill[:, 1:]           # (B, T-1)
                tgt_correct_shift = tgt_correct[:, 1:]       # (B, T-1)
                mask_shift = mask[:, 1:]                     # (B, T-1)

                # Indexar prediccion en el skill correspondiente a cada paso
                # gather: para cada (b, t), tomar preds[b, t, tgt_skill[b,t]]
                preds_skill = preds_shift.gather(
                    2, tgt_skill_shift.unsqueeze(-1)).squeeze(-1)  # (B, T-1)

                # Loss binaria + mascara
                loss_per_step = bce(preds_skill, tgt_correct_shift)  # (B, T-1)
                loss_masked = (loss_per_step * mask_shift).sum()
                n_obs = mask_shift.sum()
                loss = loss_masked / n_obs.clamp_min(1.0)

                # Backprop
                optim.zero_grad()
                loss.backward()
                optim.step()

                loss_acum += loss_masked.item()
                n_obs_acum += int(n_obs.item())

            # Loss promedio de la epoca
            loss_epoca = loss_acum / max(n_obs_acum, 1)
            self.loss_history.append(loss_epoca)

            if self.verbose and (epoca + 1) % 5 == 0:
                print(f'   [DKT] Epoca {epoca + 1}/{self.n_epochs} - loss: {loss_epoca:.4f}')

        return self

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Predice P(correct) para cada interaccion de test.

        Recibe:
            data: DataFrame de interacciones (mismas columnas que en fit).
        Devuelve:
            Copia con dos columnas nuevas:
            - correct_predictions: P(correcto) predicha
            - state_predictions: P(correcto) en el skill propio (equivalente a P(L))
        """
        # Validacion: skills desconocidos quedan con NaN
        df = data.copy().reset_index(drop=True)
        df['correct_predictions'] = np.nan
        df['state_predictions'] = np.nan

        # La red en modo eval (desactiva dropout)
        self.net.eval()
        # Preparamos secuencias en orden de usuario
        df_ord = df.sort_values(['user_id', 'skill_name', 'order_id'])
        # iteramos por estudiante
        with torch.no_grad():
            for user_id, grupo in df_ord.groupby('user_id'):
                # Indices originales en el DataFrame para asignar predicciones
                indices = grupo.index.to_numpy()
                # Convertir skills a ids (saltar los no entrenados)
                pairs = []
                for idx_local, (idx_global, fila) in enumerate(grupo.iterrows()):
                    s = fila['skill_name']
                    if s not in self.skill_to_id:
                        continue
                    pairs.append((idx_global, self.skill_to_id[s], int(fila['correct'])))

                if not pairs:
                    continue

                # Construir tensor de entrada para este estudiante
                L = min(len(pairs), self.max_len)
                x = torch.zeros(1, self.max_len, 2 * self.n_skills, dtype=torch.float32,
                                device=self.device)
                for t in range(L):
                    _, skill_id, correct_t = pairs[t]
                    x[0, t, skill_id * 2 + correct_t] = 1.0

                # Forward pass: probs (1, T, K)
                probs = self.net(x).cpu().numpy()[0]  # (T, K)

                # Para cada paso t, P(correct) en el skill correspondiente es
                # probs[t-1, skill_t]. El paso 0 no tiene historia previa,
                # asignamos 0.5 (probabilidad neutral).
                for t in range(L):
                    idx_global, skill_id, _ = pairs[t]
                    if t == 0:
                        p = 0.5  # sin historia previa
                    else:
                        p = float(probs[t - 1, skill_id])
                    df.at[idx_global, 'correct_predictions'] = p
                    # state_predictions: misma probabilidad (no hay un P(L) explicito en DKT)
                    df.at[idx_global, 'state_predictions'] = p

        # Volver a modo train por si el usuario sigue entrenando
        self.net.train()
        return df

    def params(self) -> pd.DataFrame:
        """
        DKT no tiene parametros interpretables como BKT.

        Devuelve un resumen del tamano del modelo en lugar de p_init/p_learn/etc.
        """
        if self.net is None:
            return pd.DataFrame()
        total_params = sum(p.numel() for p in self.net.parameters())
        return pd.DataFrame({
            'arquitectura': ['LSTM'],
            'hidden_dim': [self.hidden_dim],
            'num_layers': [self.num_layers],
            'n_skills': [self.n_skills],
            'total_params': [total_params],
        }).T


# Prueba rapida
if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from data.generador_datos import generar_dataset

    df = generar_dataset(n_estudiantes=200, seed=42)
    print('Dataset generado:', len(df), 'filas')

    skills = ['derivada_seno', 'derivada_coseno', 'regla_cadena']
    modelo = DKTModel(seed=42, hidden_dim=32, n_epochs=10, batch_size=16, verbose=True)
    modelo.fit(df, skills=skills)

    df_pred = modelo.predict(df).dropna(subset=['correct_predictions'])
    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(df_pred['correct'], df_pred['correct_predictions'])
    print(f'AUC en train: {auc:.4f}')
    print('\nResumen del modelo:')
    print(modelo.params())
