# Cómo funcionan BKT y DKT — Explicación desde cero

Este documento explica **línea por línea** qué hace cada uno de los dos modelos del proyecto Lairn, asumiendo que **no sabes programación**. Si te pierdes en algún punto, vuelve a la sección anterior.

---

## 📚 Parte 0 — Conceptos básicos que necesitas saber

Antes de entrar al código, vamos a aclarar el vocabulario mínimo.

### ¿Qué es una "variable"?

Una variable es **una caja con etiqueta** donde guardas un valor.

```python
edad = 25
```

Aquí creamos una caja llamada `edad` y metimos el número `25` dentro. Cuando más adelante digamos `edad`, el programa lee lo que hay en esa caja.

### ¿Qué es una "función"?

Una función es **una receta**: una serie de instrucciones que tienen un nombre. Se ejecuta cuando la "llamas".

```python
def saludar(nombre):
    print("Hola " + nombre)

saludar("Daniel")   # imprime: Hola Daniel
```

- `def` = "define" (define una receta nueva)
- `saludar` = nombre de la receta
- `(nombre)` = ingrediente que recibe
- `print(...)` = mostrar en pantalla

### ¿Qué es una "clase"?

Una clase es **un plano** para crear muchos objetos del mismo tipo. Por ejemplo, un plano "Coche" puede crear muchos coches concretos.

```python
class Coche:
    def __init__(self, color):
        self.color = color   # cada coche tiene su color
    
    def pintar(self, nuevo_color):
        self.color = nuevo_color

mi_coche = Coche("rojo")   # creamos UN coche concreto
mi_coche.pintar("azul")    # ahora es azul
```

- `class` = define el plano
- `__init__` = receta especial que se ejecuta al CREAR un coche
- `self` = "yo mismo" (este coche en particular)

### ¿Qué es un "DataFrame"?

Un **DataFrame** (de la librería `pandas`) es **una tabla**, como una hoja de Excel. Tiene filas y columnas.

```
   user_id  skill_name      correct  order_id
0  0        derivada_seno   0        0
1  0        derivada_seno   1        1
2  0        derivada_coseno 0        0
3  1        derivada_seno   1        0
```

Cada fila es una interacción de un estudiante con un ejercicio.

### ¿Qué es un "tensor"?

Un tensor (PyTorch) es **una caja con números organizados en varias dimensiones**:
- 1 dimensión: una lista `[1, 2, 3]`
- 2 dimensiones: una tabla (matriz)
- 3 dimensiones: un cubo de números

Las redes neuronales necesitan tensores porque pueden hacer muchas operaciones matemáticas a la vez sobre todos esos números.

---

# 🅰️ Parte 1 — BKT (Bayesian Knowledge Tracing)

## 1.1 La idea de BKT en una analogía

Imagina un profesor con una **planilla de notas mental**. Para cada concepto que enseña (derivada_seno, derivada_coseno, regla_cadena), lleva **una sola probabilidad**: *"¿qué tan probable es que este estudiante DOMINE este tema?"*.

Cada vez que el estudiante responde un ejercicio, el profe **actualiza** esa probabilidad usando la regla de Bayes (un teorema de probabilidades):
- Si acertó → "más probable que sí lo domine" → sube
- Si falló → "menos probable" → baja (pero no demasiado, porque pudo ser un descuido)

Y entre cada ejercicio, hay una pequeña probabilidad de que **aprenda algo nuevo** y pase de "no dominar" a "dominar". Esto se llama `p_learn`.

## 1.2 Los 4 parámetros mágicos de BKT

Para cada concepto, BKT estima **4 probabilidades** (números entre 0 y 1):

| Parámetro | Nombre | Qué significa | Ejemplo |
|-----------|--------|---------------|---------|
| `p_init` | Probabilidad inicial | "¿Qué probabilidad hay de que YA sepa este tema antes de empezar?" | 0.10 = "10% de estudiantes ya saben derivar seno al empezar" |
| `p_learn` | Probabilidad de aprender | "Después de cada ejercicio, ¿qué probabilidad hay de que aprenda?" | 0.20 = "Hay 20% de probabilidad de aprenderlo en cada intento" |
| `p_guess` | Probabilidad de adivinar | "Si NO lo sabe, ¿qué probabilidad hay de acertar por suerte?" | 0.25 = "25% de adivinar la respuesta correcta" |
| `p_slip` | Probabilidad de descuido | "Si SÍ lo sabe, ¿qué probabilidad hay de fallar por descuido?" | 0.10 = "10% de equivocarse aunque domine el tema" |

## 1.3 ¿Qué es un HMM (modelo oculto de Markov)?

BKT es un **HMM de 2 estados**. Suena complejo, lo explico simple:

- **2 estados:**
  - Estado 0: "No dominado"
  - Estado 1: "Dominado"
  
- **"Oculto"** significa que **NO podemos ver directamente** en qué estado está el estudiante. Solo vemos si acierta o falla (las "observaciones").
  
- **"Markov"** significa que el estado de mañana solo depende del estado de hoy, no del pasado lejano.

**Transiciones entre estados:**
```
     no_dominado  ──(p_learn)──→  dominado
          ↑                            │
          └──────(0, no se olvida)────┘
```

En el BKT clásico, una vez que dominas un concepto, **no se olvida** (esa es la suposición simplificadora — DKT sí modela olvido).

## 1.4 ¿Cómo BKT actualiza sus probabilidades con Bayes?

Cada vez que vemos una respuesta, hacemos 2 cosas:

**Paso 1 — Update (corrección con la observación):**
```
Si acertó:
  P(dominado | acertó) = P(dominado) × (1 - p_slip) / total
  
Si falló:
  P(dominado | falló) = P(dominado) × p_slip / total
```

Esto es la **regla de Bayes**: dadas nuevas evidencias (la respuesta), actualizamos nuestra creencia previa.

**Paso 2 — Transición (puede haber aprendido):**
```
P(dominado en siguiente paso) = P(dominado actual) + (1 - P(dominado actual)) × p_learn
```

Si ya está dominado, sigue dominado. Si no, hay `p_learn` probabilidad de pasar a dominado.

## 1.5 Recorrido por el código de `src/bkt_modelo.py`

Vamos a abrir el archivo y revisar las partes importantes.

### Líneas 1-22 — Encabezado del archivo

```python
"""
Implementacion en NumPy puro de Bayesian Knowledge Tracing (BKT).
...
"""
```

Esto entre triple-comillas se llama **docstring** — es como el manual del archivo. No se ejecuta, solo describe.

```python
import numpy as np
import pandas as pd

EPS = 1e-12
```

- `import numpy as np` → "trae la librería de matemáticas y llámala `np`" (más corto que `numpy`).
- `import pandas as pd` → trae la librería de tablas.
- `EPS = 1e-12` → constante muy pequeña (0.000000000001). La usamos para evitar dividir entre cero.

### Líneas 25-78 — `_forward_backward()` — El corazón estadístico

Esta función calcula dos cosas para un estudiante:
- **`alpha`**: "probabilidad de haber llegado a este estado tras ver las primeras t respuestas"
- **`beta`**: "probabilidad de las observaciones futuras dado este estado actual"

Es matemáticamente densa, pero conceptualmente: **mira la secuencia hacia adelante y hacia atrás** para repartir probabilidades.

```python
def _forward_backward(obs, p_init, p_learn, p_guess, p_slip):
    T = len(obs)            # número de respuestas del estudiante
```
`T` es el número total de interacciones de ese estudiante (ej. 10 ejercicios).

```python
    pi = np.array([1.0 - p_init, p_init])
```
`pi` es el estado inicial: vector con probabilidad de empezar en no_dominado y dominado.

```python
    A = np.array([[1.0 - p_learn, p_learn], [0.0, 1.0]])
```
`A` es la **matriz de transición**. Esto es matemática matricial — léelo así:
- Si estás en no_dominado: con probabilidad `1-p_learn` te quedas ahí, con `p_learn` pasas a dominado
- Si estás en dominado: te quedas dominado (con probabilidad 1.0)

```python
    b = np.array([
        [1.0 - p_guess, p_guess],
        [p_slip, 1.0 - p_slip],
    ])
```
`b` son las **probabilidades de observación**:
- Si NO dominas: probabilidad `1-p_guess` de fallar, `p_guess` de adivinar y acertar
- Si SÍ dominas: probabilidad `p_slip` de fallar por descuido, `1-p_slip` de acertar

```python
    alpha = np.zeros((T, 2))
    alpha[0] = pi * b[:, obs[0]]
```
Inicializamos `alpha` y calculamos el primer paso multiplicando estado inicial × probabilidad de la primera observación.

El resto del bucle propaga estas probabilidades hacia adelante (forward) y hacia atrás (backward). El resultado es la base para estimar los 4 parámetros en el siguiente paso.

### Líneas 81-179 — `_em_step()` — Una iteración del aprendizaje (EM)

EM = **Expectation-Maximization**. Es un algoritmo que **mejora los parámetros un poquito** en cada iteración. Lo llamamos muchas veces hasta que converja.

Imagina que adivinas los 4 parámetros, luego:
1. **E-step** (Expectation): "dados estos parámetros, ¿qué tan bien explican mis datos?"
2. **M-step** (Maximization): "ajusto los parámetros para explicar mejor"

Repite hasta que el cambio sea mínimo.

```python
def _em_step(secuencias, params):
    p_init = params['p_init']
    p_learn = params['p_learn']
    p_guess = params['p_guess']
    p_slip = params['p_slip']
```
Sacamos los 4 parámetros actuales (la "adivinación" actual).

```python
    sum_gamma1_dominado = 0.0
    n_secs = 0
    sum_xi_01 = 0.0
    sum_gamma_no_dom = 0.0
    sum_gamma_no_dom_correct = 0.0
    sum_gamma_no_dom_all = 0.0
    sum_gamma_dom_incorrect = 0.0
    sum_gamma_dom_all = 0.0
    log_lik_total = 0.0
```
Creamos **acumuladores** (cajas que vamos llenando) para juntar estadísticas sobre TODOS los estudiantes.

```python
    for obs in secuencias:
        ...
        alpha, beta, log_lik = _forward_backward(obs, ...)
```
Para cada estudiante (cada `obs` = lista de 0s y 1s), calculamos sus alpha/beta.

```python
        gamma = alpha * beta
        gamma_sum = gamma.sum(axis=1, keepdims=True) + EPS
        gamma /= gamma_sum
```
`gamma[t, s]` = probabilidad de estar en estado `s` en el paso `t`, **dado todo lo que sabemos**. Lo normalizamos para que sume 1.

```python
        sum_gamma1_dominado += gamma[0, 1]
        n_secs += 1
```
Acumulamos cuántas veces empezamos en estado dominado (para luego promediar y obtener `p_init`).

```python
    new_p_init = sum_gamma1_dominado / max(n_secs, 1)
    new_p_learn = sum_xi_01 / (sum_gamma_no_dom + EPS)
    new_p_guess = sum_gamma_no_dom_correct / (sum_gamma_no_dom_all + EPS)
    new_p_slip = sum_gamma_dom_incorrect / (sum_gamma_dom_all + EPS)
```
**Aquí está la magia:** los nuevos parámetros son simplemente proporciones de los acumuladores. Ejemplo:
- `new_p_guess` = `(suma de veces que acertó estando en no_dominado)` / `(suma de veces que estuvo en no_dominado)`

```python
    new_p_guess = float(np.clip(new_p_guess, 1e-3, 0.499))
    new_p_slip = float(np.clip(new_p_slip, 1e-3, 0.499))
```
**Restricción importante:** forzamos `p_guess < 0.5` y `p_slip < 0.5`. Sin esto, BKT puede "aprender al revés" (confundir dominado con no_dominado).

### Líneas 182-310 — Clase `BKTModel`

#### `__init__()` — Cuando creas un BKTModel

```python
def __init__(self, seed=42, num_fits=5, max_iter=200, tol=1e-4):
    self.seed = seed
    self.num_fits = num_fits
    self.max_iter = max_iter
    self.tol = tol
    self.params_ = {}
    self.skills_ = []
```
Guarda los hiperparámetros. **`self`** es "este BKTModel concreto".
- `seed=42`: semilla aleatoria para que dé el mismo resultado siempre
- `num_fits=5`: hace 5 entrenamientos con inicializaciones distintas y se queda con el mejor (porque EM puede caer en mínimos locales)
- `max_iter=200`: máximo 200 pasos de EM
- `tol=1e-4`: si el cambio entre pasos es menor a 0.0001, ya convergió

#### `_extraer_secuencias()` — Prepara los datos

```python
def _extraer_secuencias(self, df, skill):
    df_skill = df[df['skill_name'] == skill]
    df_skill = df_skill.sort_values(['user_id', 'order_id'])
    return [g['correct'].to_numpy(dtype=int) for _, g in df_skill.groupby('user_id')]
```
Para un skill concreto (ej. `derivada_seno`):
1. Filtra solo las filas de ese skill
2. Ordena por estudiante y orden temporal
3. Devuelve una lista: una secuencia de 0s y 1s por cada estudiante

Ejemplo de salida:
```
[
  [0, 0, 1, 0, 1, 1],   # estudiante 0
  [0, 1, 0, 1, 1, 1, 1],   # estudiante 1
  [1, 1, 1, 1, 1],   # estudiante 2 (este es bueno)
  ...
]
```

#### `_entrenar_skill()` — Entrena UN skill

```python
def _entrenar_skill(self, secuencias, seed):
    rng = np.random.default_rng(seed)
    mejor = None
    
    for restart in range(self.num_fits):
        params = {
            'p_init':  float(rng.uniform(0.05, 0.50)),
            'p_learn': float(rng.uniform(0.05, 0.40)),
            'p_guess': float(rng.uniform(0.05, 0.30)),
            'p_slip':  float(rng.uniform(0.05, 0.20)),
        }
        ...
```
- Hace 5 reinicios (`num_fits`)
- Cada reinicio empieza con valores aleatorios diferentes para los 4 parámetros
- Esto evita caer siempre en el mismo "mínimo local" (un óptimo subóptimo)

```python
        ll_prev = -np.inf
        for it in range(self.max_iter):
            params, ll = _em_step(secuencias, params)
            if abs(ll - ll_prev) < self.tol:
                break
            ll_prev = ll
```
Aquí está **el bucle de EM**: hasta 200 iteraciones de mejora. Si el `log-likelihood` (qué tan bien explican los parámetros los datos) cambia menos que `tol`, paramos antes.

```python
        if mejor is None or ll > mejor['ll']:
            mejor = {'params': params, 'll': ll}
```
Guardamos el mejor reinicio.

#### `fit()` — Entrena TODOS los skills

```python
def fit(self, data, skills):
    self.skills_ = list(skills)
    for i, skill in enumerate(skills):
        secs = self._extraer_secuencias(data, skill)
        if not secs:
            continue
        self.params_[skill] = self._entrenar_skill(secs, seed=self.seed + i)
    return self
```
Por cada skill (`derivada_seno`, `derivada_coseno`, `regla_cadena`), entrena un HMM independiente. **Aquí está la limitación clave de BKT**: cada skill se entrena por separado, no aprende relaciones entre skills.

#### `predict()` — Hace predicciones

Esta es la función más importante para entender:

```python
def predict(self, data):
    df = data.copy().reset_index(drop=True)
    df['correct_predictions'] = np.nan
    df['state_predictions'] = np.nan
```
Copia la tabla y le agrega dos columnas nuevas (vacías).

```python
    for (user_id, skill), grp in df.groupby(['user_id', 'skill_name']):
        if skill not in self.params_:
            continue
        p = self.params_[skill]
        grp_ord = grp.sort_values('order_id')
        indices = grp_ord.index.to_numpy()
        p_l = p['p_init']
```
Para cada par (estudiante, skill):
- `p_l` arranca con `p_init` (probabilidad inicial de estar dominado)

```python
        for fila_idx, idx in enumerate(indices):
            obs = int(grp_ord.iloc[fila_idx]['correct'])
            p_correct = p_l * (1.0 - p['p_slip']) + (1.0 - p_l) * p['p_guess']
            df.at[idx, 'state_predictions'] = p_l
            df.at[idx, 'correct_predictions'] = p_correct
```
**ESTA es la fórmula clave de predicción de BKT:**

```
P(correcto) = P(dominado) × (1 - p_slip) + (1 - P(dominado)) × p_guess
              ^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
              "domina y NO se equivoca"    "no domina pero adivina"
```

```python
            if obs == 1:
                num = p_l * (1.0 - p['p_slip'])
                den = p_correct + EPS
            else:
                num = p_l * p['p_slip']
                den = (1.0 - p_correct) + EPS
            p_l_post = num / den
```
**Update de Bayes con la observación:** si acertó, sube `P(dominado)`; si falló, baja.

```python
            p_l = p_l_post + (1.0 - p_l_post) * p['p_learn']
```
**Transición:** entre paso t y t+1, puede aprender con probabilidad `p_learn`.

---

# 🅱️ Parte 2 — DKT (Deep Knowledge Tracing)

## 2.1 Antes del código: ¿Qué es una red neuronal?

Vamos a explicarlo paso a paso, asumiendo cero conocimiento.

### Neurona artificial — La unidad básica

Una **neurona artificial** es una función matemática muy simple:

```
entradas: x1, x2, x3 (números)
pesos: w1, w2, w3 (números que la red APRENDE)
sesgo: b (otro número que aprende)

salida = activación(x1·w1 + x2·w2 + x3·w3 + b)
```

La "activación" es una función matemática que aplasta el resultado en un rango (típicamente entre 0 y 1, o entre -1 y 1).

**Ejemplo intuitivo:** quieres predecir si un estudiante va a acertar. Entradas: (cuántos ejercicios hizo, cuántos acertó, días desde última práctica). La neurona aprende qué tan importante es cada entrada (los pesos) y combina todo en una probabilidad de acierto.

### Red neuronal — Muchas neuronas conectadas

Una **red** tiene varias **capas** de neuronas. La salida de una capa son las entradas de la siguiente.

```
Entrada → Capa 1 (10 neuronas) → Capa 2 (10 neuronas) → Salida
```

Mientras más capas y neuronas, más patrones complejos puede aprender.

### ¿Cómo "aprende" una red?

1. **Forward pass:** le metes datos, la red predice algo
2. **Cálculo del error (loss):** compara la predicción con la respuesta real → da un número que mide qué tan mal lo hizo
3. **Backward pass (backpropagation):** la red calcula cómo ajustar CADA peso para reducir el error
4. **Update:** ajusta todos los pesos un poquito en la dirección correcta
5. Repite millones de veces

**Es como aprender a tirar tiros libres:** tiras → ves dónde cayó → ajustas el ángulo → repites. Después de miles de tiros, sabes lanzar.

### ¿Qué es un LSTM?

Una **red neuronal regular** solo mira una "instantánea". Pero un estudiante es una **secuencia temporal** (intentó esto, luego esto, luego esto).

LSTM = **Long Short-Term Memory**. Es una red neuronal **con memoria**. Procesa secuencias de cosas (una a la vez) y va manteniendo un "estado mental" que actualiza con cada nueva entrada.

```
LSTM ve la secuencia [x_1, x_2, x_3, ...]
  
  Paso 1: recibe x_1
    estado_oculto_1 = LSTM(x_1, estado_inicial)
    output_1 = predicción basada en estado_1
  
  Paso 2: recibe x_2
    estado_oculto_2 = LSTM(x_2, estado_1)  ← USA el estado anterior
    output_2 = predicción basada en estado_2
  
  ...
```

El "estado oculto" es un **vector de 64 números** (o más) que **resume todo lo que la red sabe del estudiante hasta ahora**. Reemplaza la simple `P(dominado)` de BKT por algo mucho más rico.

LSTM tiene **3 compuertas** internas:
- **Forget gate**: "¿qué tanto olvido del estado anterior?"
- **Input gate**: "¿qué tanto del nuevo input incorporo?"
- **Output gate**: "¿qué tanto del estado revelo en la salida?"

Estas compuertas son **otras pequeñas redes neuronales** que aprenden a regular el flujo de información.

## 2.2 ¿Cómo DKT usa una LSTM para Knowledge Tracing?

```
Entrada (cada paso):
  Vector one-hot de tamaño 2K (donde K = número de skills)
  
  Ejemplo con K=3:
  (skill=0, correct=0) → [1, 0, 0, 0, 0, 0]
  (skill=0, correct=1) → [0, 1, 0, 0, 0, 0]
  (skill=1, correct=0) → [0, 0, 1, 0, 0, 0]
  (skill=1, correct=1) → [0, 0, 0, 1, 0, 0]
  (skill=2, correct=0) → [0, 0, 0, 0, 1, 0]
  (skill=2, correct=1) → [0, 0, 0, 0, 0, 1]
  
  "one-hot" = todos ceros salvo una posición que es 1

Salida (cada paso):
  Vector de tamaño K con probabilidades de acertar CADA skill
  Ejemplo: [0.85, 0.40, 0.30]
           = P(correcto en skill_0), P(correcto en skill_1), P(correcto en skill_2)
```

DKT predice TODO al mismo tiempo. BKT predice un skill a la vez.

## 2.3 Recorrido por el código de `src/dkt_modelo.py`

### Líneas 1-26 — Encabezado e imports

```python
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
```
- `torch` = PyTorch, la librería de redes neuronales
- `torch.nn` = módulo de PyTorch con capas listas (LSTM, Linear, etc.) — `as nn` lo abrevia
- `Dataset, DataLoader` = utilidades para dar datos a la red en lotes (batches)

### Líneas 32-89 — Clase `SecuenciasKT` (preparar datos)

```python
class SecuenciasKT(Dataset):
    def __init__(self, secuencias, n_skills, max_len=200):
        self.secuencias = secuencias
        self.n_skills = n_skills
        self.max_len = max_len
```
Plano para crear un "dataset" de PyTorch. Recibe:
- `secuencias`: lista de tuplas `(skills_de_un_estudiante, respuestas_de_un_estudiante)`
- `n_skills`: cuántos skills hay (K)
- `max_len`: secuencias largas se cortan; cortas se rellenan con ceros (padding)

```python
    def __len__(self):
        return len(self.secuencias)
```
PyTorch necesita saber cuántas secuencias hay. Es la cantidad de estudiantes.

```python
    def __getitem__(self, idx):
        skills, corrects = self.secuencias[idx]
        skills = skills[:self.max_len]
        corrects = corrects[:self.max_len]
        L = len(skills)
        
        x = torch.zeros(self.max_len, 2 * self.n_skills, dtype=torch.float32)
        target_skill = torch.zeros(self.max_len, dtype=torch.long)
        target_correct = torch.zeros(self.max_len, dtype=torch.float32)
        mask = torch.zeros(self.max_len, dtype=torch.float32)
```
Cuando PyTorch pide "dame la secuencia número `idx`":
- Toma esa secuencia, la corta si es muy larga
- Crea tensores vacíos: `x` (entrada), `target_skill`, `target_correct`, `mask`

```python
        for t in range(L):
            skill_t = int(skills[t])
            correct_t = int(corrects[t])
            x[t, skill_t * 2 + correct_t] = 1.0
```
Para cada paso `t` de la secuencia, ponemos un `1.0` en la posición `skill_t * 2 + correct_t` del vector x. Es la **codificación one-hot**.

Ejemplo con K=3:
- skill=0, correct=0 → posición 0 → `[1, 0, 0, 0, 0, 0]`
- skill=0, correct=1 → posición 1 → `[0, 1, 0, 0, 0, 0]`
- skill=2, correct=1 → posición 5 → `[0, 0, 0, 0, 0, 1]`

```python
            target_skill[t] = skill_t
            target_correct[t] = float(correct_t)
            mask[t] = 1.0
```
- `target_skill[t]` = qué skill toca en este paso (necesario para indexar la predicción)
- `target_correct[t]` = la respuesta verdadera (0 o 1)
- `mask[t] = 1.0` = "esta posición es real, no padding"

### Líneas 96-142 — Clase `DKTNet` (la red en sí)

```python
class DKTNet(nn.Module):
    def __init__(self, n_skills, hidden_dim=64, num_layers=1, dropout=0.2):
        super().__init__()
        self.n_skills = n_skills
        self.hidden_dim = hidden_dim
```
Hereda de `nn.Module` (todas las redes en PyTorch heredan de esto). Guarda configuración.

```python
        self.lstm = nn.LSTM(
            input_size=2 * n_skills,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
```
**Crea la capa LSTM**, con:
- `input_size=2*n_skills`: cada entrada es un vector de 2K elementos (one-hot)
- `hidden_size=64`: el estado oculto tiene 64 números (la "memoria")
- `num_layers=1`: una sola capa LSTM apilada
- `batch_first=True`: por convención, el primer eje del tensor es el batch
- `dropout=0.2`: regularización (apaga aleatoriamente 20% de neuronas durante entrenamiento)

```python
        self.fc = nn.Linear(hidden_dim, n_skills)
```
**Capa lineal** (`fc` = fully-connected): transforma los 64 números del estado oculto en K números (uno por skill). Es una multiplicación de matrices: `salida = entrada × W + b`.

```python
    def forward(self, x):
        out, _ = self.lstm(x)
        logits = self.fc(out)
        probs = torch.sigmoid(logits)
        return probs
```
**Este es el "forward pass"** — el flujo de datos:
1. `out, _ = self.lstm(x)` → la LSTM procesa la secuencia, devuelve estados ocultos
2. `logits = self.fc(out)` → la capa lineal proyecta a K dimensiones
3. `probs = torch.sigmoid(logits)` → aplasta a (0,1) — son las probabilidades de acertar cada skill

**Sigmoide:** `sigmoid(x) = 1 / (1 + e^(-x))`. Función matemática que convierte cualquier número en un valor entre 0 y 1.

### Líneas 149-310 — Clase `DKTModel` (el envoltorio)

#### `__init__()` — Configuración

```python
def __init__(self, seed=42, hidden_dim=64, num_layers=1, dropout=0.2,
             n_epochs=30, batch_size=32, lr=1e-3, max_len=200,
             device='cpu', verbose=True):
```
Guarda todos los hiperparámetros.
- `n_epochs=30`: cuántas veces "ve" todos los datos durante entrenamiento
- `batch_size=32`: procesa 32 estudiantes a la vez (más rápido)
- `lr=1e-3`: learning rate, qué tan grandes son los pasos al ajustar los pesos
- `device='cpu'`: corre en CPU (en GPU sería `'cuda'`)

#### `_extraer_secuencias()` — Prepara datos

```python
def _extraer_secuencias(self, df):
    df = df.copy()
    df = df.sort_values(['user_id', 'skill_name', 'order_id'])
    secuencias = []
    for user_id, grupo in df.groupby('user_id'):
        skills_ids = [self.skill_to_id[s] for s in grupo['skill_name'].tolist()
                      if s in self.skill_to_id]
        corrects = grupo['correct'].tolist()[:len(skills_ids)]
        if len(skills_ids) > 0:
            secuencias.append((skills_ids, corrects))
    return secuencias
```
Convierte el DataFrame en una lista: para cada estudiante, una tupla `(lista_de_skills, lista_de_aciertos)`.

#### `fit()` — Entrena la red

```python
def fit(self, data, skills):
    np.random.seed(self.seed)
    torch.manual_seed(self.seed)
```
Fija semillas en numpy Y PyTorch para reproducibilidad.

```python
    self.skill_to_id = {s: i for i, s in enumerate(skills)}
    self.n_skills = len(skills)
```
Mapeo: nombre del skill → número entero. Ej: `{'derivada_seno': 0, 'derivada_coseno': 1, 'regla_cadena': 2}`.

```python
    secuencias = self._extraer_secuencias(data)
    dataset = SecuenciasKT(secuencias, self.n_skills, self.max_len)
    loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
```
Crea el dataset y el loader (que entrega batches automáticamente).

```python
    self.net = DKTNet(self.n_skills, self.hidden_dim, self.num_layers, self.dropout).to(self.device)
    optim = torch.optim.Adam(self.net.parameters(), lr=self.lr)
    bce = nn.BCELoss(reduction='none')
```
- Crea la red neuronal (la `DKTNet` que vimos arriba)
- **Adam** = algoritmo de optimización que ajusta los pesos. Más sofisticado que SGD clásico.
- **BCELoss** = "Binary Cross-Entropy". La función que mide error en clasificación binaria. Cuando la predicción está cerca del valor real, el error es bajo. Cuando está lejos, alto.

```python
    self.net.train()
    self.loss_history = []
    for epoca in range(self.n_epochs):
        loss_acum = 0.0
        n_obs_acum = 0
        for batch in loader:
            x = batch['x'].to(self.device)
            tgt_skill = batch['target_skill'].to(self.device)
            tgt_correct = batch['target_correct'].to(self.device)
            mask = batch['mask'].to(self.device)
```
**Bucle de entrenamiento**: por cada época (30 veces), recorre todos los batches.

```python
            preds_all = self.net(x)
```
**Forward pass**: pasa el batch por la red, obtiene predicciones.

```python
            preds_shift = preds_all[:, :-1, :]
            tgt_skill_shift = tgt_skill[:, 1:]
            tgt_correct_shift = tgt_correct[:, 1:]
            mask_shift = mask[:, 1:]
```
**Shift importante:** el output del paso `t` se usa para predecir el paso `t+1`. Por eso quitamos el último output (no hay siguiente) y el primer target (no tiene historia).

```python
            preds_skill = preds_shift.gather(2, tgt_skill_shift.unsqueeze(-1)).squeeze(-1)
```
**Magia de PyTorch:** de las K predicciones (una por skill), tomamos solo la del skill que tocaba en el paso siguiente. `gather` es como indexar.

```python
            loss_per_step = bce(preds_skill, tgt_correct_shift)
            loss_masked = (loss_per_step * mask_shift).sum()
            n_obs = mask_shift.sum()
            loss = loss_masked / n_obs.clamp_min(1.0)
```
Calcula el error y lo enmascara (ignora padding).

```python
            optim.zero_grad()
            loss.backward()
            optim.step()
```
**Las 3 líneas más importantes del entrenamiento:**
1. `zero_grad()`: borra gradientes anteriores
2. `loss.backward()`: **backpropagation** — calcula cómo cambiar cada peso para reducir el error
3. `optim.step()`: aplica los cambios

```python
        loss_epoca = loss_acum / max(n_obs_acum, 1)
        self.loss_history.append(loss_epoca)
```
Guarda el error promedio de la época (para la gráfica de curva de aprendizaje).

#### `predict()` — Hace predicciones

```python
def predict(self, data):
    df = data.copy().reset_index(drop=True)
    df['correct_predictions'] = np.nan
    df['state_predictions'] = np.nan
    self.net.eval()
```
- `self.net.eval()` apaga el dropout (no queremos randomness en predicción)

```python
    with torch.no_grad():
        for user_id, grupo in df_ord.groupby('user_id'):
            ...
            probs = self.net(x).cpu().numpy()[0]
```
- `with torch.no_grad():` desactiva el cálculo de gradientes (no estamos entrenando, ahorramos memoria)
- Para cada estudiante, corre la red y obtiene la matriz de probabilidades

```python
            for t in range(L):
                idx_global, skill_id, _ = pairs[t]
                if t == 0:
                    p = 0.5
                else:
                    p = float(probs[t - 1, skill_id])
                df.at[idx_global, 'correct_predictions'] = p
                df.at[idx_global, 'state_predictions'] = p
```
**Aquí está el detalle crítico:**
- Para el paso `t`, la predicción de `P(correcto)` la sacamos de `probs[t-1, skill_id]` (output del paso anterior, indexado en el skill actual)
- Para el paso 0, no hay historia previa → asignamos `0.5` (probabilidad neutral)

---

# 🆚 Parte 3 — Comparación final lado a lado

| Aspecto | BKT | DKT |
|---------|-----|-----|
| **Tipo de modelo** | Estadístico (HMM) | Red neuronal (LSTM) |
| **Parámetros** | 4 por skill (12 total con 3 skills) | ~5.000-50.000 pesos |
| **Algoritmo de entrenamiento** | Baum-Welch / EM (probabilístico) | Backpropagation + Adam (gradient descent) |
| **Estado del estudiante** | 1 número por skill: P(dominado) | Vector de 64 números (estado LSTM) |
| **Datos que ve** | Una secuencia por (estudiante, skill) | TODA la historia del estudiante junta |
| **Aprende relaciones entre skills?** | ❌ No | ✅ Sí |
| **Modela olvido?** | ❌ No (BKT clásico) | ✅ Sí (via forget gate del LSTM) |
| **Interpretable?** | ✅ Sí (4 parámetros entendibles) | ❌ No (caja negra) |
| **Velocidad entrenar** | Segundos | Minutos |
| **Datos necesarios** | Pocos (cientos de estudiantes) | Muchos (miles ideal) |
| **AUC esperado ASSISTments** | 0.67-0.73 | 0.80-0.86 |

---

# 📖 Glosario rápido

- **AUC** (Area Under Curve): métrica entre 0.5 (azar) y 1.0 (perfecto). Mide qué tan bien el modelo discrimina aciertos de fallos.
- **Backpropagation**: algoritmo que ajusta los pesos de una red usando la regla de la cadena del cálculo.
- **Batch**: subconjunto de datos procesado a la vez para acelerar entrenamiento.
- **Epoch (época)**: una pasada completa sobre todos los datos.
- **EM (Expectation-Maximization)**: algoritmo iterativo para estimar parámetros cuando hay variables ocultas.
- **HMM (Hidden Markov Model)**: modelo probabilístico de estados ocultos que evolucionan en el tiempo.
- **LSTM (Long Short-Term Memory)**: red neuronal recurrente con memoria de largo plazo.
- **Loss (función de pérdida)**: número que mide cuánto se equivoca el modelo. Lo minimizamos.
- **One-hot**: codificación donde un vector tiene un solo `1` y el resto son ceros.
- **Seed (semilla)**: número que fija la aleatoriedad. Misma semilla = mismo resultado siempre.
- **Sigmoide**: función matemática que aplasta cualquier número en (0, 1).
- **Tensor**: array multidimensional usado en PyTorch.

---

# 🎓 Para defender tu proyecto

Si te preguntan...

**"¿Qué hace BKT?"**
> "Modela cada concepto como un sistema de 2 estados (dominado/no dominado) con probabilidades de transición. Estima 4 parámetros usando Expectation-Maximization, y para cada interacción del estudiante actualiza su probabilidad de dominio con la regla de Bayes."

**"¿Qué hace DKT?"**
> "Usa una red neuronal LSTM que procesa la secuencia completa de interacciones del estudiante (todos los skills juntos). El estado oculto del LSTM funciona como una memoria del conocimiento, y proyectamos ese estado a K probabilidades — una por cada skill — para predecir aciertos futuros."

**"¿Por qué DKT es mejor?"**
> "Porque puede aprender dependencias entre skills (dominar `derivada_seno` ayuda con `derivada_coseno`), modela olvido a través de las compuertas del LSTM, y se adapta a perfiles diferentes de estudiantes implícitamente. BKT trata cada skill como independiente."

**"¿Por qué solo lo supera por poco?"**
> "Tres razones: filtramos a 10 skills (Piech 2015 usó 110, donde DKT brilla más), DKT necesita más epochs y hidden_dim para converger, y la literatura reciente (Yeung 2018) documentó que DKT clásico solo supera a BKT marginalmente sin optimizaciones."

---

# 🗂️ Parte 4 — Archivos de datos: qué hay y por qué

En la carpeta `data/` tienes varios archivos. Esta es la diferencia:

```
data/
├── generador_datos.py        ← código que GENERA datos sintéticos
├── descargar_assistments.py  ← código que DESCARGA datos reales
│
├── interacciones.csv         ← datos ACTIVOS del último Run All
│                              (sintético o real, lo que pusiste en FUENTE_DATOS)
│
├── assistments.csv           ← TODOS los datos reales procesados
│                              (~225.000 interacciones, 3.000 estudiantes,
│                               110 skills) - el dataset estándar de la literatura
│
└── assistments.raw.csv       ← datos reales recién descargados (formato DKVMN)
                                el script `descargar_assistments.py` los procesa
                                y guarda en `assistments.csv`
```

## ¿Por qué `interacciones.csv` tiene menos datos que `assistments.csv`?

Porque `interacciones.csv` es lo que se **carga ACTUALMENTE** en el notebook, después de aplicar filtros:

- Si `FUENTE_DATOS='sintetico'`: genera 1.000 estudiantes × 3 skills ≈ **30.000 interacciones** (no usa `assistments.csv`)
- Si `FUENTE_DATOS='real'`: filtra `assistments.csv` a los **top-10 skills más frecuentes** → ~82.000 interacciones (de 225.000 originales). Los otros 100 skills tienen tan pocos datos cada uno que no servirían para entrenar HMMs estables.

# 🎓 Parte 5 — ¿Con qué datos entrena cada notebook?

**AMBOS notebooks entrenan con AMBAS fuentes automáticamente.**

```
01_bkt.ipynb (Run All completo):

  Celdas 1-13:  Entrena BKT con FUENTE_DATOS (la "primaria")
                Si pusiste 'sintetico' → guarda en modelos/bkt_sintetico/
                Si pusiste 'real'      → guarda en modelos/bkt_real/

  Celdas 14-15: Entrena BKT con la OTRA fuente automáticamente
                (función pipeline_bkt_completo)
                Guarda en la otra carpeta modelos/bkt_*/

  Celdas 16-17: Carga ambos resultados y genera tabla + gráfica comparativa
```

Lo mismo aplica para `02_dkt.ipynb`.

**Una sola ejecución de cada notebook entrena 2 modelos.** Si corres ambos notebooks, tienes 4 modelos entrenados:
- `modelos/bkt_sintetico/`
- `modelos/bkt_real/`
- `modelos/dkt_sintetico/`
- `modelos/dkt_real/`

# 📊 Parte 6 — Tamaños de train/test (números exactos)

Estos números salen de los `config.json` reales:

## Dataset Sintético++
| | Valor | Detalle |
|---|---|---|
| Estudiantes totales | 1.000 | controlado por `N_ESTUDIANTES` |
| **Train (70%)** | **700 estudiantes** | usado para `model.fit()` |
| **Test (30%)** | **300 estudiantes** | usado para `model.predict()` |
| Filas totales | 29.994 interacciones | depende del power-law en sesiones |
| Skills | 3 | derivada_seno, derivada_coseno, regla_cadena |

## Dataset Real (ASSISTments top-10)
| | Valor | Detalle |
|---|---|---|
| Estudiantes totales | 2.177 | después de filtrar a top-10 skills |
| **Train (70%)** | **1.523 estudiantes** | |
| **Test (30%)** | **654 estudiantes** | |
| Filas totales | 81.550 interacciones | de los 225.000 originales |
| Skills usados | 10 | los más frecuentes de 110 |

## ⚠️ Detalle crítico: el split es POR ESTUDIANTE

```python
users = df['user_id'].unique()
u_tr, u_te = train_test_split(users, test_size=0.30, random_state=42)
df_tr = df[df['user_id'].isin(u_tr)]
df_te = df[df['user_id'].isin(u_te)]
```

**Un estudiante NUNCA aparece en train Y test al mismo tiempo.** Si dividiéramos por interacción (algunas filas en train, otras en test del mismo estudiante), habría **data leakage** y el AUC saldría falsamente inflado.

# 🔢 Parte 7 — Parámetros que aprende cada modelo

## BKT — Pocos parámetros, INTERPRETABLES

Cada skill tiene 4 parámetros (`p_init`, `p_learn`, `p_guess`, `p_slip`).

| Dataset | Skills | Parámetros totales |
|---------|--------|---------------------|
| Sintético | 3 | **12** (4 × 3) |
| Real | 10 | **40** (4 × 10) |

Ejemplo real (de `modelos/bkt_sintetico/config.json`):
```json
"derivada_seno": {
  "p_init": 0.001,
  "p_learn": 0.19833,
  "p_guess": 0.29264,
  "p_slip": 0.23907
}
```

**Cada uno significa algo concreto:** un humano puede leer esta tabla y entender el modelo.

## DKT — Muchos parámetros, NO interpretables

El número depende de `hidden_dim` (64 en nuestro caso) y `n_skills`:

```
Total LSTM ≈ 4 × (input_dim + hidden_dim + 1) × hidden_dim
            = 4 × (2K + 64 + 1) × 64

Capa final lineal = (hidden_dim + 1) × n_skills
                  = 65 × K
```

| Dataset | K (skills) | input_dim (2K) | Params LSTM | Capa final | **TOTAL** |
|---------|-----------|----------------|-------------|------------|-----------|
| Sintético | 3 | 6 | ~17.000 | 195 | **~17.200** |
| Real | 10 | 20 | ~22.000 | 650 | **~22.650** |

**Estos pesos NO son interpretables** (no sabes cuál peso controla qué). Son una caja negra que la red ajusta durante backpropagation.

# 🎨 Parte 8 — Qué hace CADA gráfica del notebook

Cada notebook (01_bkt y 02_dkt) genera 4 gráficas:

## Celda 10 — Evolución de P(dominado) de UN estudiante

**Qué se ve:**
- Eje X: número de interacción (orden temporal)
- Eje Y: probabilidad de dominio (0 a 1)
- Una línea de color por concepto/skill
- Línea horizontal roja en 0.80 (umbral de dominio)

**Qué explica:**
- Cómo el modelo va **actualizando su creencia** sobre el dominio paso a paso
- En BKT: las líneas se escalonan hacia arriba (sube si acierta, baja si falla)
- En DKT: las líneas pueden bajar también (porque LSTM modela olvido)
- Los conceptos fáciles llegan al umbral antes que los difíciles

**Patrón ideal:**
- Empieza cerca de 0 (no domina nada)
- Conforme acierta, sube
- Cruza el umbral 0.80 alrededor del intento 5-10
- Termina cerca de 1.0 en los skills que dominó

## Celda 11 — DIFIERE entre BKT y DKT

### En `01_bkt.ipynb`: **Heatmap de parámetros**

Tabla coloreada (paleta YlGnBu):
```
                  p_init  p_learn  p_guess  p_slip
derivada_seno     0.001   0.198    0.293    0.239
derivada_coseno   0.001   0.180    0.292    0.254
regla_cadena      0.001   0.186    0.295    0.239
```

**Qué explica:**
- `p_init` ~ 0.001 → casi nadie domina los skills al empezar
- `p_learn` ~ 0.18 → 18% de probabilidad de aprender en cada intento
- `p_guess` ~ 0.29 → 29% de probabilidad de adivinar sin saber
- `p_slip` ~ 0.24 → 24% de probabilidad de fallar sabiendo (descuido)

**Verificación crítica:** debajo de la gráfica se imprimen los checks `p_guess < 0.5` y `p_slip < 0.5` (identifiability constraints).

### En `02_dkt.ipynb`: **Curva de loss durante entrenamiento**

Línea descendente:
- Eje X: época (1 a 30)
- Eje Y: loss (Binary Cross-Entropy)

**Qué explica:**
- Cómo el error va **bajando** mientras entrena
- Si la curva **se aplana** → el modelo convergió ✓
- Si **sigue bajando rápido al final** → necesitas más épocas
- Si **sube** → algo está mal (LR alto o overfitting)

## Celda 12 — Histograma de dominio final por concepto

**Qué se ve:**
- Una sub-gráfica por concepto (3 paneles en sintético, 10 en real)
- Cada panel: histograma de P(dominado) al final de las interacciones
- Eje X: P(dominado) final, de 0 a 1
- Eje Y: cantidad de estudiantes
- Línea roja vertical en 0.80 (umbral)

**Qué explica:**
- **Distribución bimodal** (dos picos en 0 y 1) = el modelo discrimina bien
- **Distribución plana** = el modelo no discrimina
- **Pico solo a la derecha** = todos dominan (concepto fácil)
- **Pico solo a la izquierda** = pocos dominan (concepto difícil)

Debajo se imprime el porcentaje de estudiantes que alcanzaron el umbral por concepto.

## Celda 17 — Comparativa final entre fuentes (y modelos)

### En `01_bkt.ipynb`: barras agrupadas (Sintético++ vs Real)

4 grupos en X (AUC, Accuracy, F1, RMSE), 2 barras por grupo:
- 🟦 Sintético++
- 🟧 Real (ASSISTments)
- ⋯ Línea gris punteada en AUC=0.67 (referencia BKT literatura)

### En `02_dkt.ipynb`: barras agrupadas (BKT-sint, BKT-real, DKT-sint, DKT-real)

4 grupos en X, **4 barras** por grupo:
- 🟦 BKT - Sintético
- 🟦 BKT - Real (oscuro)
- 🟧 DKT - Sintético
- 🟧 DKT - Real (oscuro)
- ⋯ Línea gris en AUC=0.67 (BKT literatura)
- ⋯ Línea verde en AUC=0.82 (DKT literatura, Piech 2015)

**Qué explica (la conclusión central del proyecto):**
- Si DKT > BKT → la red neuronal vale la pena vs baseline
- Si están cerca de las líneas de literatura → tu implementación es correcta
- Si DKT en sintético >> DKT en real → el generador tiene patrones más explotables

# 🏁 Resumen visual completo

```
┌─────────────────────────────────────────────────────────────────┐
│  PROYECTO LAIRN - MICROSERVICIO ML                              │
│                                                                 │
│  DATOS                                                          │
│  ├─ Sintético++:  1.000 estudiantes / 30.000 interacciones      │
│  │                3 skills, generado por nosotros con           │
│  │                7 fuentes de variabilidad                     │
│  │                                                              │
│  └─ Real (ASSISTments): 2.177 estudiantes / 81.550 inter.       │
│                         10 skills (top-10 de 110)               │
│                                                                 │
│  SPLIT (mismo para ambos modelos, semilla 42)                   │
│  ├─ Sintético: 700 train / 300 test                             │
│  └─ Real:     1.523 train / 654 test                            │
│                                                                 │
│  MODELOS                                                        │
│  ├─ BKT (HMM)                                                   │
│  │   ├─ 12 params en sintético, 40 en real                      │
│  │   ├─ Entrena con EM (Baum-Welch), 5 restarts                 │
│  │   ├─ AUC sintético: ~0.71                                    │
│  │   └─ AUC real:      ~0.71  ✓ coincide con literatura         │
│  │                                                              │
│  └─ DKT (LSTM)                                                  │
│      ├─ 17.000 params en sintético, 22.000 en real              │
│      ├─ Entrena con Adam, 30 epochs, hidden_dim=64              │
│      ├─ AUC sintético: ~0.80                                    │
│      └─ AUC real:      ~0.74                                    │
│                                                                 │
│  GRÁFICAS POR NOTEBOOK                                          │
│  ├─ Cell 10: evolución P(L) en 1 estudiante                     │
│  ├─ Cell 11: heatmap params (BKT) | curva loss (DKT)            │
│  ├─ Cell 12: histograma de dominio final                        │
│  └─ Cell 17: comparativa de barras entre fuentes                │
└─────────────────────────────────────────────────────────────────┘
```
