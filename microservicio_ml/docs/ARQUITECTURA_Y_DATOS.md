# Arquitectura técnica y datos — Explicación desde cero

Este documento explica con extremo detalle:
- **Cada término técnico** que aparece en el proyecto
- **Qué datos** usamos exactamente y **de dónde** vienen
- **Cómo está hecha la red neuronal** (capas, conexiones, por qué cada elección)
- **Si las decisiones del proyecto son viables** (con argumentos)

Asumimos que **no sabes nada de programación ni de inteligencia artificial**.

---

# PARTE 1 — Glosario completo (lee esto primero)

Antes de cualquier otra cosa, vamos a aclarar el vocabulario. Usaremos estos términos toda la documentación.

## Conceptos de programación

| Término | Qué es | Analogía simple |
|---------|--------|-----------------|
| **Variable** | Una caja con etiqueta donde guardas un valor | Una caja con la etiqueta "edad" que contiene el número 25 |
| **Función** | Una receta con un nombre que ejecuta instrucciones | Una receta llamada "saludar" que dice "imprime hola" |
| **Clase** | Un plano para crear muchos objetos del mismo tipo | El plano "Coche" puede crear muchos coches específicos |
| **Objeto** | Una instancia concreta de una clase | Tu coche concreto (rojo, año 2020) es un objeto de la clase Coche |
| **Método** | Una función que pertenece a una clase | El método `frenar()` del coche |
| **Módulo** | Un archivo `.py` que contiene código reutilizable | Una "caja de herramientas" |
| **Librería / paquete** | Conjunto de módulos | Un "ferretería completa" |
| **Import** | "Trae código de otro archivo" | Como prestar una herramienta del vecino |
| **String** | Texto entre comillas | `"hola"` |
| **Int / Float** | Número entero / número con decimales | `25` / `0.7906` |
| **Lista** | Colección ordenada de cosas | `[1, 2, 3]` o `["a", "b", "c"]` |
| **Diccionario** | Mapeo clave → valor | `{"nombre": "Juan", "edad": 25}` |
| **For loop** | Repite instrucciones por cada elemento de algo | "Por cada estudiante, hacer X" |
| **If / else** | Toma decisiones según una condición | "Si acertó, sube P(L); si no, baja" |
| **Return** | Devuelve un valor desde una función | El resultado final de la receta |
| **Assert** | Verifica que algo sea cierto, si no lo es, da error | "Asegura que no haya nulos" |

## Conceptos de manipulación de datos

| Término | Qué es | Analogía simple |
|---------|--------|-----------------|
| **DataFrame** | Tabla con filas y columnas (de la librería pandas) | Una hoja de Excel |
| **CSV** | Formato de archivo de texto con valores separados por coma | Excel guardado como texto |
| **JSON** | Formato de texto para estructuras de datos jerárquicas | Un menú con secciones y subsecciones |
| **Pickle (.pkl)** | Formato binario para guardar objetos de Python tal cual | Una "foto" del objeto en memoria |
| **NumPy array** | Una lista de números super optimizada para matemáticas | Tabla de números a velocidad de bala |
| **Tensor** | Lista de números multidimensional (de PyTorch) | Igual que array pero con superpoderes para redes neuronales |
| **Schema** | El "esquema" de columnas que debe tener una tabla | El formato esperado de las columnas |
| **Pipeline** | Secuencia de pasos de procesamiento | Una cadena de montaje |

## Conceptos estadísticos / matemáticos

| Término | Qué es | Analogía simple |
|---------|--------|-----------------|
| **Probabilidad** | Número entre 0 y 1 que mide qué tan probable es algo | 0.5 = mitad y mitad |
| **Distribución** | Cómo se reparten los valores posibles | Histograma de alturas en una clase |
| **Regla de Bayes** | Fórmula para actualizar creencias con evidencia | "Pensaba A, pero vi B, ahora pienso C" |
| **Verosimilitud (likelihood)** | Qué tan probable son los datos dado un modelo | "Si el modelo es así, ¿qué tan raros son los datos?" |
| **Log-likelihood** | Logaritmo de la verosimilitud (más estable numéricamente) | Misma medida pero en escala logarítmica |
| **Sigmoide** | Función matemática que aplasta cualquier número en (0, 1) | Una "S" que convierte rangos infinitos en probabilidades |
| **HMM** | Modelo de Markov Oculto (Hidden Markov Model) | "Estados que no veo y que cambian con el tiempo" |
| **EM (Expectation-Maximization)** | Algoritmo iterativo para estimar parámetros | "Adivino, mejoro, adivino, mejoro..." |
| **Baum-Welch** | Versión específica de EM para HMMs | El algoritmo EM aplicado a este tipo de modelo |

## Conceptos de machine learning / redes neuronales

| Término | Qué es | Analogía simple |
|---------|--------|-----------------|
| **Modelo** | Una "función matemática" que aprende a hacer una tarea | Como una caja que recibe datos y predice algo |
| **Entrenar (fit)** | Mostrarle datos al modelo para que ajuste sus parámetros | Practicar tirando tiros libres hasta dominar |
| **Predecir (predict)** | Usar el modelo entrenado para estimar algo nuevo | Tirar el tiro real después de practicar |
| **Train / Test split** | Dividir los datos: una parte para entrenar, otra para evaluar | Practicar con ejercicios pero examinarte con OTROS |
| **AUC** | Métrica entre 0.5 (azar) y 1.0 (perfecto) que mide discriminación | "Qué tan bien separa aciertos de fallos" |
| **Accuracy** | Proporción de predicciones correctas | "De 100 predicciones, acerté X" |
| **F1-score** | Balance entre precisión y recall | Métrica robusta cuando hay clases desbalanceadas |
| **RMSE** | Error promedio al cuadrado, raíz cuadrada | "Qué tan lejos están las predicciones del valor real" |
| **Loss** | Número que mide cuánto se equivoca el modelo (lo minimizamos) | Lo que queremos hacer chico |
| **Cross-entropy / BCE** | Tipo de loss para problemas de clasificación binaria | La función que mide error en preguntas tipo sí/no |
| **Hiperparámetro** | Configuración del modelo que tú decides (no se aprende) | "Cuántos epochs", "tamaño del batch" |
| **Parámetro** | Valor que el modelo aprende durante entrenamiento | Los pesos de la red, los 4 valores de BKT |
| **Epoch (época)** | Una pasada completa por todos los datos durante entrenamiento | "Repasé todos los ejercicios una vez" |
| **Batch** | Subconjunto de datos procesados juntos en un paso de entrenamiento | "Hago 32 ejercicios y luego ajusto" |
| **Learning rate (lr)** | Qué tan grandes son los pasos al ajustar los parámetros | Lr alto = pasos grandes (riesgoso); lr bajo = pasos chiquitos (lento) |
| **Optimizer (optimizador)** | Algoritmo que ajusta los parámetros (Adam, SGD, etc.) | El "entrenador" que decide cómo mejorar |
| **Gradient descent** | Algoritmo de optimización basado en cuesta abajo | Bajar una montaña paso a paso siempre en dirección más empinada |
| **Backpropagation** | Algoritmo para calcular cómo ajustar los pesos de una red | "Propagar el error hacia atrás" |
| **Overfitting** | Cuando el modelo memoriza train pero falla en test | Memorizar respuestas sin entender |
| **Regularización** | Técnicas para evitar overfitting | "Limitar al modelo para que no memorice" |
| **Dropout** | Técnica de regularización: apagar neuronas aleatoriamente | "Entrenarse con un brazo atado para no depender de él" |

## Conceptos específicos de Knowledge Tracing

| Término | Qué es |
|---------|--------|
| **Knowledge Tracing (KT)** | Tarea de modelar el conocimiento de un estudiante a lo largo del tiempo |
| **Skill / concepto** | Una habilidad a aprender (ej. derivada_seno) |
| **Interacción** | Una respuesta del estudiante a un ejercicio (acierto o fallo) |
| **P(L)** | Probabilidad de dominar un skill |
| **One-hot encoding** | Vector de ceros con un solo uno en una posición específica |
| **Embedding** | Representación numérica de algo discreto (skill, palabra) |

---

# PARTE 2 — Datos: qué tenemos y de dónde vienen

## 2.1 Las dos fuentes de datos

El proyecto usa **DOS fuentes**:

```
┌──────────────────────────────────────────────────────────────┐
│ FUENTE A: Sintético++ (datos generados por nosotros)         │
│ ├─ Archivo:  data/generador_datos.py                         │
│ ├─ Salida:   data/interacciones.csv (si FUENTE_DATOS=sint)   │
│ ├─ Tamaño:   1.000 estudiantes / ~30.000 interacciones       │
│ ├─ Skills:   3 (derivada_seno, derivada_coseno, regla_cadena)│
│ └─ Internet: NO necesita                                     │
│                                                              │
│ FUENTE B: ASSISTments 2009-2010 (datos REALES)               │
│ ├─ Origen:   estudiantes reales de secundaria USA (2009)     │
│ ├─ Descarga: data/descargar_assistments.py                   │
│ ├─ Salida:   data/assistments.csv (procesado)                │
│ ├─ Tamaño:   3.000 estudiantes / 225.000 interacciones       │
│ ├─ Skills:   110 originales (usamos top-10 más frecuentes)   │
│ └─ Internet: SÍ, primera vez (después queda en disco)        │
└──────────────────────────────────────────────────────────────┘
```

## 2.2 ASSISTments — ¿de dónde sale y qué es?

**ASSISTments** es una plataforma educativa de Estados Unidos para enseñanza de matemáticas. En el periodo 2009-2010, profesores la usaron con sus alumnos y recolectaron logs de interacciones. Ese dataset se hizo **público en 2012** para la investigación en Knowledge Tracing.

### URL oficial (con registro)
```
https://sites.google.com/site/assistmentsdata/datasets/2009-2010-assistment-data
```
La página oficial pide registro (gratis) para acceder al CSV original.

### URL del mirror que usamos automáticamente
```
https://raw.githubusercontent.com/jennyzhang0215/DKVMN/master/data/assist2009_updated/assist2009_updated_train.csv
```

Este es un **mirror público** del repositorio del paper *DKVMN (Zhang et al. 2017)*. Subió los datos ya procesados y son ampliamente usados en la comunidad de KT.

### ¿Por qué es importante este dataset?

Es el **estándar de facto** del campo. Casi todos los papers de KT (BKT, DKT, SAKT, DKVMN, AKT, SAINT, etc.) reportan sus AUC sobre ASSISTments. Esto significa que:
- ✅ Puedes **comparar tu modelo contra la literatura**
- ✅ Si tu AUC coincide con el reportado por Piech 2015, **tu implementación está bien**
- ✅ Tu defensa es más sólida porque usas el dataset esperado del campo

### Formato técnico

El archivo descargado está en **formato DKVMN** (no es un CSV tabular normal). Cada estudiante ocupa **3 líneas consecutivas**:

```
Linea 1:  número de interacciones del estudiante (ej. 64)
Linea 2:  skill_ids separados por coma (64 valores)
Linea 3:  correctness (0/1) separados por coma (64 valores)
```

Ejemplo real del archivo:
```
64
1,1,1,1,1,1,1,1,1,1,...,31,31,31,68,68,...
0,1,1,1,0,0,0,0,1,1,...,1,0,0,1,0,1,1,...
245
4,8,4,5,4,5,4,5,4,9,4,9,4,7,...
0,0,1,1,0,0,1,1,1,1,1,1,1,1,...
```

Nuestro script [data/descargar_assistments.py](../data/descargar_assistments.py) convierte ese formato a nuestro **schema estándar de 4 columnas**:

```
user_id | skill_name | correct | order_id
   0    |  skill_1   |    0    |    0
   0    |  skill_1   |    1    |    1
   0    |  skill_1   |    1    |    2
   ...
```

## 2.3 Datos sintéticos++ — qué simula y cómo

Generamos datos artificiales que **imitan el comportamiento real** de estudiantes. NO es azar puro: el generador modela 7 fenómenos observados en datos reales.

### Las 7 fuentes de variabilidad

#### 1. Perfiles de estudiante
```python
PERFILES = {
    'rapido':   {'alpha': 0.40, 'beta': -0.30, 'olvido': 0.020, 'prop': 0.15},
    'promedio': {'alpha': 0.25, 'beta': -1.00, 'olvido': 0.050, 'prop': 0.60},
    'lento':    {'alpha': 0.12, 'beta': -1.60, 'olvido': 0.090, 'prop': 0.20},
    'rinde':    {'alpha': 0.06, 'beta': -2.20, 'olvido': 0.150, 'prop': 0.05},
}
```
- 15% son rápidos (aprenden con `alpha=0.40` por paso)
- 60% promedio (`alpha=0.25`)
- 20% lentos
- 5% abandonadores

#### 2. Dificultad por concepto
```python
DIFICULTAD_CONCEPTO = {
    'derivada_seno':   0.0,   # base, fácil
    'derivada_coseno': 0.3,   # medio
    'regla_cadena':    1.0,   # difícil (resta 1.0 al logit)
}
```

#### 3. Dependencias curriculares
Si dominas `derivada_seno` (P > 0.70), recibes un **boost** al aprender los demás:
```python
DEPENDENCIAS = {
    'derivada_coseno': ('derivada_seno', 0.40),  # boost de +0.40
    'regla_cadena':    ('derivada_seno', 0.50),  # boost de +0.50
}
```

#### 4. Curva de olvido (Ebbinghaus)
Si no practicas un skill durante muchos pasos, `P(dominio) × (1 - olvido)^pasos`.

#### 5. Fatiga
A partir de 20 interacciones, baja la atención: `logit -= 0.04 × (paso - 20)`.

#### 6. Ruido puntual
~5% de las interacciones son aleatorias 50/50 (despiste, suerte, conexión).

#### 7. Sesiones variables (power-law)
Algunos estudiantes hacen 15 ejercicios, otros 90, siguiendo una distribución `power-law` (típica de comportamiento humano real).

### ¿Por qué esto es mejor que un generador simple?

Un generador trivial (solo sigmoide pura) genera datos que BKT puede modelar perfectamente porque BKT **asume** exactamente esa forma. DKT no encontraría nada extra.

Con las 7 fuentes:
- BKT solo capta el patrón sigmoidal básico (lo que sabe modelar) → AUC ~0.71
- DKT capta dependencias, olvido, perfiles, fatiga → AUC ~0.80

Esto **simula** el efecto que vemos en datos reales: DKT > BKT porque DKT captura fenómenos que BKT no.

## 2.4 ¿Por qué había `notebooks/data/`?

⚠️ **Era un bug que ya arreglé.**

**Causa:** el archivo [data/descargar_assistments.py](../data/descargar_assistments.py) usaba una ruta **relativa**:
```python
RUTA_DESTINO = Path('data/assistments.csv')
```

Una ruta relativa se interpreta **desde el directorio de trabajo actual**. Cuando ejecutas el notebook desde `notebooks/`, ese es el directorio de trabajo, entonces `data/...` se convierte en `notebooks/data/...`.

**Solución aplicada:** usar ruta absoluta basada en la ubicación del propio archivo `.py`:
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUTA_DESTINO = PROJECT_ROOT / 'data' / 'assistments.csv'
```

Esto garantiza que sin importar desde dónde se llame, siempre apunta a `raiz_proyecto/data/`.

---

# PARTE 3 — BKT en detalle (el modelo "clásico")

## 3.1 ¿Es una red neuronal?

**NO.** BKT es un **modelo probabilístico**, específicamente un **HMM (Hidden Markov Model)**. No tiene capas, ni neuronas, ni pesos en el sentido de las redes neuronales.

## 3.2 ¿Qué tiene entonces?

Tiene **4 parámetros por skill**:

| Parámetro | Símbolo en literatura | Rango | Significado |
|-----------|------------------------|-------|-------------|
| `p_init`  | P(L₀) | (0, 1) | Probabilidad inicial de dominar el skill |
| `p_learn` | P(T)  | (0, 1) | Probabilidad de aprender en cada intento |
| `p_guess` | P(G)  | (0, 0.5) | Probabilidad de acertar sin saber (suerte) |
| `p_slip`  | P(S)  | (0, 0.5) | Probabilidad de fallar sabiendo (descuido) |

Las restricciones `p_guess < 0.5` y `p_slip < 0.5` se llaman **identifiability constraints** (Beck & Chang 2007). Sin ellas, BKT puede "aprender al revés" porque el estado "no dominado" y "dominado" se vuelven intercambiables.

## 3.3 La máquina de 2 estados

```
        ┌──────────────────┐                    ┌──────────────────┐
        │                  │   p_learn          │                  │
        │  NO DOMINADO     │  ──────────────→   │   DOMINADO       │
        │                  │                    │                  │
        │ P(acertar) =     │                    │ P(acertar) =     │
        │   p_guess        │                    │   1 - p_slip     │
        │                  │                    │                  │
        │ ┌─ 1 - p_learn ─┐│                    │ ┌─ 1.0 ─────────┐│
        │ │  se queda     ↓│                    │ │ se queda     ↓│
        │ └───────────────┘│                    │ └───────────────┘│
        └──────────────────┘                    └──────────────────┘
```

**Una vez en "DOMINADO", no se sale.** Esa es la suposición clásica de BKT: no hay olvido.

## 3.4 ¿Cómo se entrena? — Algoritmo Baum-Welch

Es una **versión específica de EM (Expectation-Maximization)** adaptada a HMMs. Pasos:

1. **Inicializa** los 4 parámetros con valores aleatorios
2. **E-step (Expectation):** dadas las observaciones (aciertos/fallos), calcula probabilidades de estar en cada estado en cada paso (`gamma`)
3. **M-step (Maximization):** recalcula los 4 parámetros para maximizar la verosimilitud de los datos
4. **Repite** hasta que el cambio sea menor que `tol=1e-4` o se alcancen `max_iter=200`

### Reinicios (random restarts)

EM puede caer en **mínimos locales** (soluciones subóptimas). Para evitarlo:
- Hacemos **5 reinicios** (`num_fits=5`) con inicializaciones aleatorias diferentes
- Nos quedamos con el mejor (mayor log-likelihood)

## 3.5 ¿Cómo predice?

Para cada estudiante, en cada interacción:

**Paso 1 — Calcular probabilidad de acertar:**
```
P(acertar) = P(L) × (1 - p_slip) + (1 - P(L)) × p_guess
                ↑                        ↑
        "domina y no se equivoca"   "no domina pero adivina"
```

**Paso 2 — Update con la observación (Bayes):**
```
Si acertó:
  P(L | acertó) = P(L) × (1 - p_slip) / P(acertar)

Si falló:
  P(L | falló) = P(L) × p_slip / (1 - P(acertar))
```

**Paso 3 — Transición al siguiente paso:**
```
P(L_{t+1}) = P(L|obs) + (1 - P(L|obs)) × p_learn
```

---

# PARTE 4 — DKT en detalle (la red neuronal)

## 4.1 ¿Qué es una red neuronal? — Desde cero

### Una neurona artificial

Es una **función matemática simple**:
```
entradas:  x1, x2, x3        (números)
pesos:     w1, w2, w3        (números que la red APRENDE)
sesgo:     b                 (otro número que aprende)

resultado_intermedio = x1·w1 + x2·w2 + x3·w3 + b
salida = activación(resultado_intermedio)
```

La **función de activación** toma ese resultado y lo transforma. Las más comunes:

| Función | Fórmula | Rango de salida | Uso típico |
|---------|---------|------------------|------------|
| **Sigmoide** | `1 / (1 + e^(-x))` | (0, 1) | Probabilidades binarias |
| **Tanh** | `(e^x - e^(-x)) / (e^x + e^(-x))` | (-1, 1) | Estados internos de redes |
| **ReLU** | `max(0, x)` | [0, ∞) | Redes profundas modernas |

### Una red neuronal = muchas neuronas conectadas

Se organizan en **capas**:

```
ENTRADA       CAPA OCULTA 1     CAPA OCULTA 2     SALIDA
  x1 ─────┐       n1 ────────┐       m1 ───────┐    y1
          │↘                  │↘                │
  x2 ─────┼──→  n2 ──────────┼──→  m2 ─────────┼──→ y2
          │↗                  │↗                │
  x3 ─────┘       n3 ────────┘       m3 ───────┘    y3

  Cada flecha tiene un peso.
  La red tiene MILES de pesos.
```

**Las redes "profundas" (deep learning) tienen muchas capas.** "Profundo" significa eso: muchas capas apiladas.

## 4.2 ¿Cómo "aprende" una red? — Backpropagation

1. **Forward pass:** le metes datos, la red predice algo (con sus pesos actuales)
2. **Loss:** comparas la predicción con la respuesta real → te da un número (cuánto se equivocó)
3. **Backward pass (backpropagation):**
   - Calcula matemáticamente cómo debería cambiar **cada peso** para reducir el loss
   - Usa derivadas parciales (regla de la cadena del cálculo)
4. **Update:** un optimizador (Adam, SGD, etc.) actualiza todos los pesos un poquito
5. Repite **millones de veces**

**Analogía:** aprender a tirar tiros libres.
- Tiras → ves dónde cayó (loss) → ajustas el ángulo (update) → repites
- Después de miles de tiros, sabes lanzar

## 4.3 ¿Por qué LSTM y no una red normal?

Una red neuronal normal (feed-forward) procesa **una entrada aislada**. Ej: dada una imagen, predice si es perro o gato.

Pero un estudiante es una **secuencia temporal**:
```
t=1: respondió derivada_seno → falló
t=2: respondió derivada_seno → acertó
t=3: respondió derivada_coseno → falló
t=4: respondió derivada_seno → acertó
...
```

Para procesar secuencias necesitas una **red recurrente (RNN)**. Las RNN normales tienen problemas con secuencias largas (vanishing gradient). LSTM (Hochreiter & Schmidhuber 1997) las soluciona con su mecanismo de **compuertas (gates)**.

### LSTM — Las 3 compuertas

```
                       ┌─────────────────────────────────┐
                       │                                 │
                       │     ╔══════════════════╗        │
                       │     ║  ESTADO C        ║        │
                       │     ║  (memoria larga) ║        │
                       │     ╚════════╤═════════╝        │
                       │              │                  │
       x_t ────────┬──→│              │                  │
                   │   │   FORGET     │  INPUT           │
                   │   │   gate       │  gate            │
       h_{t-1} ────┴──→│   ──────→  ╳ │ ┌──→  +          │
                       │              │ │     │          │
                       │              ↓ │     ↓          │
                       │           nuevo estado C        │
                       │              │                  │
                       │              ↓                  │
                       │           tanh                  │
                       │              │                  │
                       │   OUTPUT     ↓                  │
                       │   gate ────╳                    │
                       │              │                  │
                       │              ↓                  │
                       └──────────────┴──→ h_t (output)──┘
```

Las **3 compuertas** son pequeñas redes neuronales internas:
- **Forget gate:** decide qué olvidar del estado anterior (0 = olvidar todo, 1 = recordar todo)
- **Input gate:** decide qué incorporar de la nueva entrada
- **Output gate:** decide qué revelar como salida

Cada compuerta tiene **sus propios pesos** que la red aprende.

## 4.4 Arquitectura DKT en nuestro proyecto

```
┌─────────────────────────────────────────────────────────────────┐
│                  ARQUITECTURA DKT (nuestro código)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ENTRADA:                                                      │
│     Vector one-hot 2K dims (K = número de skills)               │
│                                                                 │
│     Ejemplo con K=3:                                            │
│       (skill=0, correct=0) → [1, 0, 0, 0, 0, 0]                 │
│       (skill=1, correct=1) → [0, 0, 0, 1, 0, 0]                 │
│                              ↑                                  │
│                       Cada paso de la secuencia                 │
│                       es un vector de 6 numeros (con K=3)       │
│                       o 20 numeros (con K=10)                   │
│                                                                 │
│   ↓ ↓ ↓                                                         │
│                                                                 │
│   CAPA LSTM:                                                    │
│     - input_size = 2K (entrada: 6 o 20)                         │
│     - hidden_size = 64 (estado interno: 64 numeros)             │
│     - num_layers = 1 (una sola capa LSTM apilada)               │
│     - dropout = 0.2 (regularizacion)                            │
│                                                                 │
│     Procesa la secuencia paso a paso, manteniendo               │
│     un "estado oculto" de 64 numeros que resume                 │
│     todo lo aprendido sobre el estudiante.                      │
│                                                                 │
│     Salida: secuencia de vectores de 64 dims                    │
│             (uno por cada paso de tiempo)                       │
│                                                                 │
│   ↓ ↓ ↓                                                         │
│                                                                 │
│   CAPA LINEAL (fully-connected):                                │
│     - input  = 64 (estado LSTM)                                 │
│     - output = K (uno por skill)                                │
│                                                                 │
│     Proyecta los 64 numeros a K numeros (logits).               │
│     Es una multiplicacion de matrices simple:                   │
│         logit = estado × W + b                                  │
│     Donde W es matriz de 64×K y b es vector de K.               │
│                                                                 │
│   ↓ ↓ ↓                                                         │
│                                                                 │
│   ACTIVACION SIGMOIDE:                                          │
│     Aplica sigmoide(x) = 1/(1+e^-x) a cada logit                │
│     Convierte los K numeros en K probabilidades en (0, 1).      │
│                                                                 │
│   SALIDA:                                                       │
│     Vector de K probabilidades                                  │
│     P(correct) para CADA skill simultaneamente                  │
│                                                                 │
│     Ejemplo con K=3:                                            │
│       [0.85, 0.42, 0.30]                                        │
│        ↑     ↑     ↑                                            │
│        seno  cose  cad                                          │
└─────────────────────────────────────────────────────────────────┘
```

## 4.5 ¿Por qué estas elecciones específicas?

Cada decisión tiene una razón:

### Por qué `hidden_dim = 64`

| Valor | Pros | Contras |
|-------|------|---------|
| 32 | Más rápido, menos overfitting | Poca capacidad |
| **64** | **Balance bueno** | - |
| 128-200 | Más capacidad (paper original 200) | Más lento, riesgo de overfitting con poco data |

Elegimos 64 porque para 10 skills es suficiente. Piech 2015 usó 200 con 110 skills.

### Por qué `num_layers = 1`

Una sola capa LSTM. Apilar más (2, 3) capas captura patrones más complejos pero:
- Es más lento
- Necesita más datos para no sobreajustarse
- Para nuestro caso (3-10 skills) NO mejora notablemente

### Por qué `dropout = 0.2`

Dropout = apagar aleatoriamente 20% de las neuronas durante entrenamiento.
- Evita que el modelo dependa demasiado de una neurona específica
- Mejora la generalización (mejor AUC en test)
- 0.2 es el valor estándar; valores más altos (0.5) pueden ser demasiado agresivos

### Por qué `n_epochs = 30`

Una época = ver todos los datos una vez. ¿Cuántas necesitas?
- Muy pocas (5-10): no converge, AUC bajo
- Adecuadas (20-50): converge bien
- Muchas (100+): converge pero gasta tiempo, riesgo de overfit sin early stopping

30 es un balance. En producción usarías **early stopping** (parar cuando deja de mejorar en validation).

### Por qué `batch_size = 32`

Procesar 32 secuencias a la vez en cada update.
- Batch chico (8-16): updates más ruidosos, lento
- Batch normal (32-64): balance
- Batch grande (128+): updates más estables pero usa más memoria

### Por qué `lr = 1e-3` y optimizador Adam

- **Adam** combina momentum + adaptive learning rate. Es el estándar moderno (mejor que SGD vanilla).
- **`1e-3` = 0.001** es el learning rate por defecto de Adam. Funciona bien en 80% de casos.

### Por qué `max_len = 200`

Algunos estudiantes en ASSISTments tienen 500+ interacciones. Truncamos a 200 para:
- Limitar uso de memoria
- Que el batch entre en RAM
- 200 es suficiente para capturar la mayoría de los patrones

---

# PARTE 5 — ¿Es viable este proyecto?

Análisis técnico y académico honesto.

## 5.1 Viabilidad técnica

| Aspecto | Estado | Comentario |
|---------|--------|------------|
| **Funcionalidad** | ✅ Funciona | BKT y DKT entrenan y predicen end-to-end |
| **Reproducibilidad** | ✅ Garantizada | seeds fijas en numpy, torch, pyBKT |
| **Datos** | ✅ Híbrido | Sintético++ (offline) + ASSISTments (real) |
| **Validación** | ✅ Sí | AUC BKT real coincide con literatura |
| **Documentación** | ✅ Exhaustiva | Este doc + COMO_FUNCIONA.md + comments línea por línea |
| **Modularidad** | ✅ Buena | data/, src/, notebooks/, modelos/ separados |
| **Sin dependencias rotas** | ✅ Funciona en Python 3.14 / Windows | NumPy puro para BKT, PyTorch para DKT |

## 5.2 Viabilidad académica (defensa del proyecto)

### Fortalezas

1. **Evaluación cruzada:** entrenas con datos sintéticos Y reales. Esto es **mejor** que la mayoría de proyectos de pregrado.
2. **Validación contra literatura:** BKT-real AUC ~0.71 está en el rango de Piech 2015 (0.67-0.73). Demuestra que tu implementación es correcta.
3. **Generador realista:** con 7 fuentes de variabilidad, no es trivial.
4. **Comparación justa:** mismo split, mismas seeds para BKT y DKT.
5. **Documentación profunda:** tu defensa puede mostrar este documento.

### Debilidades honestas

1. **DKT en real no llega a 0.82 (Piech 2015):** llegamos a 0.74. Razones:
   - Top-10 skills en vez de 110
   - Pocas epochs (30 vs 100+)
   - Sin tuning de hiperparámetros
2. **No hay validation set:** train/test split sin un val intermedio para tuning sin contaminar test.
3. **Falta SAKT:** está pendiente (el modelo con transformer/self-attention).

## 5.3 ¿Cómo se mejoraría?

Si quisieras llevar este proyecto a "nivel papers":

| Mejora | Esfuerzo | Beneficio |
|--------|----------|-----------|
| Usar todos los 110 skills de ASSISTments | Bajo | AUC DKT subiría ~0.05 |
| Subir hidden_dim a 200 y n_epochs a 100 | Bajo | AUC DKT subiría ~0.03 |
| Implementar early stopping con val set | Medio | Robustez |
| Implementar DKT+ (Yeung 2018) | Alto | AUC DKT real ~0.82 |
| Agregar SAKT | Alto | Otro punto en la tabla comparativa |

## 5.4 Para tu defensa

**Frases que puedes decir con seguridad:**

> *"Implementé BKT en NumPy puro usando el algoritmo Baum-Welch para evitar dependencias C++ que fallan en Python 3.14 Windows. Implementé DKT en PyTorch con arquitectura LSTM de hidden_dim=64. Ambos modelos los evalúo sobre dos fuentes: un generador sintético con 7 fuentes de variabilidad y el dataset estándar ASSISTments 2009-2010. El AUC de BKT en ASSISTments (0.71) coincide con la literatura (Piech 2015 reporta 0.67-0.73), validando la implementación. DKT supera a BKT en ambas fuentes, con mayor margen en sintético (+0.09) por capturar dependencias y fatiga que BKT no modela."*

**Si te preguntan "¿por qué DKT no llega a 0.82?":**
> *"Por tres razones: filtramos a top-10 skills (Piech usó 110, donde DKT brilla más), no hicimos tuning extensivo de hiperparámetros, y la literatura reciente (Yeung 2018) documentó que DKT clásico solo supera a BKT marginalmente sin las mejoras de DKT+. Las elecciones se hicieron por tiempo de entrenamiento."*

---

# 📝 Cierre

Si te queda alguna duda sobre cualquier concepto de este documento (regla de Bayes, sigmoide, backpropagation, etc.), pregunta y lo expando. Este archivo es para que lo abras siempre que necesites recordar **qué hace el proyecto y por qué**.
