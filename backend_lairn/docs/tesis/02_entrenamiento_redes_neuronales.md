# Documento 2 — Proceso de Entrenamiento de Redes Neuronales

**Proyecto**: Lairn — Sistema Inteligente de Aprendizaje Adaptativo
**Tipo de documento**: Documento técnico-metodológico
**Versión**: 0.7 (borrador intermedio)
**Estado de avance reportado**: 70 %
**Fecha de última actualización**: 2026-05-24

> **Nota sobre el estado del documento.** Esta versión presenta el diseño de las arquitecturas neuronales seleccionadas y los hiperparámetros iniciales planeados. Los valores listados son preliminares y se ajustarán empíricamente durante la fase de experimentación. Las métricas reales de desempeño se incorporarán en la versión 1.0 una vez ejecutadas las pruebas con los datasets identificados.

---

## 1. Introducción

Este documento describe el plan de implementación y entrenamiento de los modelos de redes neuronales que conformarán el motor adaptativo de Lairn. La selección de modelos parte de las conclusiones del **Documento 1 — Investigación de agentes de IA**, donde se identificaron tres candidatos a implementar bajo una estrategia incremental:

1. **BKT (Bayesian Knowledge Tracing)** como baseline interpretable.
2. **DKT (Deep Knowledge Tracing)** basado en LSTM como modelo neuronal principal.
3. **SAKT (Self-Attentive Knowledge Tracing)** basado en Transformers como extensión experimental opcional.

El objetivo del entrenamiento es producir modelos capaces de estimar la probabilidad de dominio conceptual de cada estudiante a partir de su historial de respuestas, para alimentar al motor adaptativo en su decisión de qué pregunta presentar a continuación, con qué dificultad y cuándo dar por dominado un concepto.

### 1.1 Objetivos del documento

1. Detallar las arquitecturas neuronales seleccionadas y sus fundamentos teóricos.
2. Definir los hiperparámetros iniciales para cada modelo.
3. Especificar los datos de entrenamiento (públicos y propios) que se utilizarán.
4. Describir el pipeline completo de entrenamiento desde la extracción de datos hasta la persistencia del modelo.
5. Definir las métricas con las que se evaluará cada modelo.

### 1.2 Alcance y limitaciones

Este documento presenta el plan de entrenamiento, no los resultados. Los resultados empíricos (curvas de pérdida, métricas finales, comparativa entre modelos) se incorporarán en la versión 1.0 una vez completada la fase de experimentación. Las cifras de hiperparámetros aquí listadas son puntos de partida basados en literatura; se ajustarán durante el tuning.

---

## 2. Arquitecturas Seleccionadas

### 2.1 Resumen comparativo

| Modelo | Tipo | Función en Lairn | Prioridad |
|---|---|---|---|
| BKT | Probabilístico clásico | Baseline interpretable de referencia | **Obligatorio** |
| DKT | RNN (LSTM) | Modelo neuronal principal | **Obligatorio** |
| SAKT | Transformer (atención) | Comparación con arquitectura moderna | Opcional |

### 2.2 BKT (Bayesian Knowledge Tracing)

**Fundamento**: Modela el dominio de cada concepto como una variable binaria latente (`dominado` / `no dominado`) que evoluciona según una cadena de Markov de dos estados (Corbett & Anderson, 1995).

**Cuatro parámetros por concepto**:
- `p_init`: probabilidad de que el estudiante ya domine el concepto al inicio.
- `p_learn`: probabilidad de transitar de "no dominado" a "dominado" en un paso.
- `p_guess`: probabilidad de acertar a pesar de no dominar el concepto.
- `p_slip`: probabilidad de fallar a pesar de dominar el concepto.

**Implementación prevista**: librería `pyBKT` (Badrinath et al., 2021), que provee una implementación validada de BKT con ajuste por *Expectation-Maximization*.

**Ventajas para el proyecto**:
- No requiere GPU.
- Entrenable con menos de 1 000 secuencias.
- Cada parámetro tiene interpretación pedagógica clara, lo cual facilita su justificación ante docentes y jurado.

### 2.3 DKT (Deep Knowledge Tracing)

**Fundamento**: Red neuronal recurrente que aprende a predecir la probabilidad de acertar la siguiente pregunta de cada concepto, a partir de la secuencia completa de interacciones previas del estudiante (Piech et al., 2015).

**Topología propuesta**:

```
                Entrada: secuencia de interacciones
                  x_t = one_hot(concepto_t, correcto_t)
                       (dim = 2 × M, M = # conceptos)
                                   │
                                   ▼
                ┌─────────────────────────────────┐
                │   Capa de Embedding             │
                │   Linear(2M → 128)              │
                └─────────────────────────────────┘
                                   │
                                   ▼
                ┌─────────────────────────────────┐
                │   LSTM (2 capas)                │
                │   hidden_size = 200             │
                │   dropout = 0.3 entre capas     │
                └─────────────────────────────────┘
                                   │
                                   ▼
                ┌─────────────────────────────────┐
                │   Capa densa de salida          │
                │   Linear(200 → M)               │
                │   Activación: Sigmoid           │
                └─────────────────────────────────┘
                                   │
                                   ▼
              Salida: y_t ∈ [0,1]^M
              y_t[k] = P(acertar concepto k en t+1)
```

**Implementación prevista**: PyTorch (≥ 2.0). Ejecución sobre GPU local o Google Colab para entrenamiento; inferencia en CPU dentro del microservicio.

**Decisiones de diseño**:
- Se elige `LSTM` sobre `GRU` por mayor representación de literatura comparable y porque la diferencia de desempeño es marginal en este dominio (Yeung & Yeung, 2018).
- Se usan **2 capas** apiladas para captar dependencias temporales profundas; literatura sugiere que más capas no mejoran significativamente el desempeño en KT (Liu et al., 2019).
- La capa de salida produce una probabilidad por concepto en lugar de una probabilidad por pregunta, lo cual permite que el modelo generalice a preguntas nuevas del mismo concepto (relevante para Lairn, donde las preguntas se generan dinámicamente).

### 2.4 SAKT (Self-Attentive Knowledge Tracing) — opcional

**Fundamento**: Reemplaza la LSTM por un mecanismo de auto-atención inspirado en Transformers (Pandey & Karypis, 2019). El modelo aprende a "atender" a interacciones pasadas específicamente relevantes para predecir la actual.

**Topología propuesta**:

```
Entrada: secuencia de (concepto_t, correcto_t)
                  │
                  ▼
   ┌──────────────────────────────────┐
   │ Embedding de interacción (E_i)   │
   │ Embedding de pregunta (E_q)      │
   │ Embedding posicional (E_pos)     │
   │ dim = 64                         │
   └──────────────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────┐
   │ Multi-Head Self-Attention        │
   │ num_heads = 4                    │
   │ Mask causal (no mirar al futuro) │
   └──────────────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────┐
   │ Feed-Forward + Dropout(0.2)      │
   │ LayerNorm + skip connections     │
   └──────────────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────┐
   │ Linear(64 → M) + Sigmoid         │
   └──────────────────────────────────┘
                  │
                  ▼
       y_t[k] = P(acertar concepto k en t+1)
```

**Justificación**: Si los tiempos del cronograma permiten implementarlo, SAKT servirá como punto de comparación con DKT para evaluar si la arquitectura basada en atención supera a la recurrente en el dominio específico de Lairn.

---

## 3. Hiperparámetros Iniciales

> Los valores presentados son puntos de partida tomados de la literatura. Se ajustarán mediante búsqueda en grilla (*grid search*) o búsqueda aleatoria (*random search*) durante la fase de tuning.

### 3.1 BKT

| Parámetro | Valor inicial | Notas |
|---|---|---|
| Algoritmo de ajuste | Expectation-Maximization (EM) | Provisto por `pyBKT` |
| Iteraciones máximas EM | 200 | Convergencia típica entre 50-150 |
| Tolerancia de convergencia | 1e-4 | Criterio de parada |
| Valores iniciales aleatorios | 5 reinicios | Para evitar mínimos locales |

### 3.2 DKT (LSTM)

| Hiperparámetro | Valor inicial | Rango a explorar |
|---|---|---|
| Embedding size | 128 | {64, 100, 128, 200} |
| LSTM hidden size | 200 | {100, 200, 256} |
| Número de capas LSTM | 2 | {1, 2, 3} |
| Dropout | 0.3 | {0.1, 0.2, 0.3, 0.5} |
| Optimizador | Adam | {Adam, AdamW, RMSprop} |
| Tasa de aprendizaje (lr) | 1e-3 | {1e-4, 5e-4, 1e-3, 5e-3} |
| Batch size | 32 | {16, 32, 64, 128} |
| Épocas máximas | 100 | Con early stopping |
| Early stopping (patience) | 10 épocas | Sobre val_loss |
| Función de pérdida | Binary Cross-Entropy | Estándar para KT |
| Función de activación | Sigmoid en la salida | Probabilidades por concepto |
| Gradient clipping | 5.0 | Estabilidad numérica de LSTM |
| Longitud máxima de secuencia | 200 interacciones | Truncamiento + padding |

### 3.3 SAKT

| Hiperparámetro | Valor inicial | Rango a explorar |
|---|---|---|
| d_model | 64 | {64, 128, 256} |
| Número de heads | 4 | {2, 4, 8} |
| Número de bloques | 1 | {1, 2, 4} |
| Dropout | 0.2 | {0.1, 0.2, 0.3} |
| Tasa de aprendizaje | 1e-3 | {1e-4, 5e-4, 1e-3} |
| Optimizador | Adam con warmup | Programación lineal |
| Longitud máxima de secuencia | 100 | {50, 100, 200} |
| Épocas máximas | 100 | Con early stopping |

---

## 4. Datos de Entrenamiento

### 4.1 Estrategia de datos

Dado que Lairn se encuentra en fase de prototipo y aún no cuenta con volumen suficiente de interacciones propias para entrenar modelos neuronales (el llamado problema de *cold start*), se adopta una **estrategia híbrida en dos fases**:

- **Fase A — Pre-entrenamiento con datasets públicos**: se entrenan los modelos sobre datasets abiertos y consolidados de la literatura de KT.
- **Fase B — Fine-tuning con datos propios**: una vez Lairn acumule suficientes interacciones reales (umbral estimado: ≥ 10 000 secuencias), se ajustan los pesos a partir del modelo pre-entrenado.

### 4.2 Datasets públicos identificados

| Dataset | Fuente | Tamaño | Formato | Uso previsto |
|---|---|---|---|---|
| ASSISTments 2009-2010 | Heffernan et al. (2014), Worcester Polytechnic | ~525 000 interacciones, ~4 200 estudiantes, ~110 conceptos | CSV | Pre-entrenamiento BKT y DKT |
| ASSISTments 2015 | Heffernan & Heffernan (2014) | ~684 000 interacciones | CSV | Validación cruzada |
| EdNet KT1 | Choi et al. (2020), Riiid | ~95 000 000 interacciones, ~780 000 estudiantes | CSV particionado | Pre-entrenamiento SAKT (si se implementa) |
| Junyi Academy | Chang et al. (2015) | ~16 000 000 interacciones | CSV | Validación adicional opcional |

**Justificación**: ASSISTments es el dataset de referencia en la literatura de KT desde 2009. EdNet es el más grande disponible públicamente y permite entrenar modelos más complejos como SAKT/AKT/SAINT.

### 4.3 Datos propios de Lairn

**Origen**: tabla `respuestas_estudiante` (modelo `RespuestaEstudiante` en `apps/analitica/models/resultado.py`).

**Campos actualmente capturados**:
- `concepto` (string)
- `pregunta` (text)
- `respuesta_correcta` (text)
- `respuesta_incorrecta` (text)
- `tiempo_por_pregunta` (int, segundos)
- `dificultad` (int, 1-3)

**Campos identificados como faltantes para entrenamiento de KT** (a implementar en el Documento 3):

| Campo a agregar | Tipo | Justificación |
|---|---|---|
| `orden_en_sesion` | IntegerField | Necesario para preservar la secuencia temporal exacta dentro de una sesión |
| `intentos_previos_concepto` | IntegerField | Insumo directo de BKT y feature útil para DKT |
| `timestamp_respuesta` | DateTimeField | Granularidad mayor que el `creado_en` del Resultado |
| `dificultad_predicha` | IntegerField (null) | Para evaluar la calidad de la predicción del motor |
| `confidence_modelo` | FloatField (null) | Para evaluación posterior del modelo en producción |
| `correcto` | BooleanField | Hoy se infiere comparando textos; mejor capturarlo explícito |

### 4.4 Formato esperado por los modelos

Tras preprocesamiento, los datos deben transformarse a secuencias por estudiante:

```python
# Ejemplo de una secuencia para un estudiante
{
    "student_id": 42,
    "interactions": [
        {"concept_id": 5, "correct": 1, "timestamp": "..."},
        {"concept_id": 5, "correct": 1, "timestamp": "..."},
        {"concept_id": 7, "correct": 0, "timestamp": "..."},
        {"concept_id": 7, "correct": 1, "timestamp": "..."},
        ...
    ]
}
```

Los conceptos se mapean a índices enteros mediante un `concept_vocab` persistente que se guarda junto al modelo entrenado.

---

## 5. Pipeline de Entrenamiento

### 5.1 Visión general

```
┌─────────────────────┐
│ 1. Extracción       │  Datasets públicos (CSV) + BD Lairn (PostgreSQL)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Preprocesamiento │  Limpieza, encoding, agrupación por estudiante
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. Split            │  Train / Validation / Test (70 / 15 / 15)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. Entrenamiento    │  Forward + Backward + Optimizer step
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. Validación       │  Por cada época, AUC sobre conjunto de validación
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. Early stopping   │  Cortar si val_loss no mejora en N épocas
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 7. Evaluación final │  Métricas sobre conjunto de test
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 8. Persistencia     │  Guardar pesos + concept_vocab + hyperparams
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 9. Deploy           │  Subir al microservicio FastAPI
└─────────────────────┘
```

### 5.2 Detalle por etapa

#### 5.2.1 Extracción
- **Datasets públicos**: descarga directa de los repositorios oficiales (Worcester Polytechnic, Riiid). Cacheo local en disco.
- **Datos propios**: query a la tabla `respuestas_estudiante` filtrada por sesiones completadas. Export a CSV o parquet.

#### 5.2.2 Preprocesamiento
- Eliminación de estudiantes con menos de 5 interacciones (señal insuficiente).
- Mapeo de conceptos a índices enteros (`concept_vocab.json`).
- Ordenamiento por `student_id` y `timestamp`.
- Truncamiento o padding a longitud máxima definida en hiperparámetros.

#### 5.2.3 Split
- 70 % entrenamiento / 15 % validación / 15 % test.
- Split **por estudiante**, no por interacción, para evitar fuga de información.
- Semilla fija (`random_state=42`) para reproducibilidad.

#### 5.2.4 Entrenamiento
- Forward pass de batch.
- Cálculo de pérdida (Binary Cross-Entropy sobre las predicciones de la siguiente interacción).
- Backward pass.
- Gradient clipping (clip_norm = 5.0 para LSTM).
- Optimizer step.

#### 5.2.5 Validación
- Cada época: forward pass sobre conjunto de validación.
- Cálculo de AUC, accuracy y val_loss.
- Logging a TensorBoard o consola.

#### 5.2.6 Early stopping
- Si `val_loss` no mejora durante 10 épocas consecutivas, se detiene el entrenamiento.
- Se guarda el modelo correspondiente al mejor `val_loss` observado.

#### 5.2.7 Evaluación final
- Métricas calculadas sobre conjunto de test (no usado durante entrenamiento ni validación).
- Se reportan las métricas definidas en la sección 6.

#### 5.2.8 Persistencia
- Pesos: `model.pt` (formato PyTorch).
- Vocabulario de conceptos: `concept_vocab.json`.
- Hiperparámetros usados: `config.json`.
- Métricas finales: `metrics.json`.

#### 5.2.9 Deploy
- El microservicio ML (FastAPI) carga los artefactos persistidos al iniciar.
- Endpoint `POST /predict` recibe la secuencia de interacciones y devuelve la probabilidad de dominio.

### 5.3 Reproducibilidad

Para garantizar reproducibilidad:
- Semillas fijas (`random`, `numpy`, `torch`).
- Versionado de datasets (hash MD5 del CSV).
- Versionado de código (Git con tags por experimento).
- Archivo `requirements.txt` con versiones exactas.
- Tabla de experimentos: id, fecha, hiperparámetros, métricas obtenidas.

---

## 6. Métricas de Evaluación

### 6.1 Métricas técnicas estándar

| Métrica | Qué mide | Por qué se usa en KT |
|---|---|---|
| **AUC-ROC** | Capacidad del modelo de discriminar entre aciertos y errores futuros | Métrica estándar en la literatura de KT |
| **Accuracy** | Proporción de predicciones correctas a un umbral de 0.5 | Interpretable, fácil de comunicar |
| **F1-score** | Balance entre precisión y recall | Útil ante clases desbalanceadas |
| **RMSE** | Error cuadrático medio de las probabilidades predichas | Sensibilidad a la calibración del modelo |
| **Log Loss** | Pérdida durante el entrenamiento | Indica convergencia |

**Umbrales esperados según literatura**:
- BKT en ASSISTments 2009: AUC ≈ 0.67 (Corbett & Anderson, 1995; replicado por Piech et al., 2015).
- DKT en ASSISTments 2009: AUC ≈ 0.86 (Piech et al., 2015).
- SAKT en ASSISTments 2009: AUC ≈ 0.85 (Pandey & Karypis, 2019).

### 6.2 Métricas educativas (planeadas)

Estas métricas se calcularán sobre simulaciones con estudiantes sintéticos y, eventualmente, sobre interacciones reales:

| Métrica | Cálculo | Objetivo |
|---|---|---|
| **Tasa de dominio** | % de conceptos elevados a nivel 3 al finalizar el examen | Medir efectividad del adaptativo |
| **# preguntas hasta dominio** | Promedio de preguntas necesarias por concepto para alcanzar nivel 3 | Medir eficiencia del adaptativo |
| **Calibración de dificultad** | Correlación entre dificultad asignada y % de acierto real | Validar que el motor adapta bien |
| **Engagement simulado** | Distribución de longitudes de sesión | Detectar abandono temprano |

### 6.3 Comparativa esperada (a completar tras experimentos)

| Modelo | AUC | Accuracy | F1 | RMSE | # preguntas hasta dominio |
|---|---|---|---|---|---|
| Reglas actuales (Lairn baseline) | — | — | — | — | — |
| BKT | — | — | — | — | — |
| DKT | — | — | — | — | — |
| SAKT (opcional) | — | — | — | — | — |

> Esta tabla se completará en la versión 1.0 del documento.

---

## 7. Infraestructura de Entrenamiento

### 7.1 Hardware

- **Entrenamiento de BKT**: CPU (cualquier máquina con ≥ 4 GB RAM).
- **Entrenamiento de DKT**: GPU recomendada. Opción inicial: Google Colab Free (Tesla T4) o Colab Pro (A100).
- **Entrenamiento de SAKT con EdNet completo**: requiere GPU dedicada con ≥ 16 GB VRAM. Plan de contingencia: usar subset del dataset.

### 7.2 Software

| Dependencia | Versión planeada | Propósito |
|---|---|---|
| Python | 3.11 | Lenguaje base |
| PyTorch | ≥ 2.0 | DKT y SAKT |
| pyBKT | ≥ 1.4 | BKT |
| NumPy | ≥ 1.24 | Operaciones tensoriales auxiliares |
| Pandas | ≥ 2.0 | Manipulación de datasets |
| scikit-learn | ≥ 1.3 | Métricas y split |
| TensorBoard | ≥ 2.14 | Visualización de entrenamiento |
| FastAPI | ≥ 0.110 | Microservicio de inferencia |

---

## 8. Pendientes y Próximos Pasos

Este documento está al 70 %. Para alcanzar la versión final (100 %) se requiere:

| Pendiente | Resultado esperado |
|---|---|
| Implementación de los tres modelos en PyTorch / pyBKT | Código funcional reproducible |
| Ejecución de los entrenamientos sobre ASSISTments 2009 | Métricas finales por modelo |
| Búsqueda de hiperparámetros (grid o random search) | Hiperparámetros óptimos documentados |
| Validación con simulación de estudiantes sintéticos | Métricas educativas reales |
| Captura de los campos faltantes en la base de datos | Modelos del Documento 3 ampliados |
| Diseño del microservicio FastAPI de inferencia | API documentada con OpenAPI |
| Pruebas de latencia del endpoint de predicción | Latencia p50, p95 y p99 medidas |
| Estrategia de reentrenamiento periódico | Cronograma y mecanismo definido |

---

## 9. Dependencias con otros entregables

- **Documento 1 (Investigación de agentes de IA)**: provee la selección de modelos a entrenar. Si la decisión cambia, este documento se actualiza.
- **Documento 3 (Esquema de base de datos)**: debe incluir los campos faltantes identificados en la sección 4.3 para que los datos propios de Lairn sean utilizables.
- **Documento 4 (Predicción de riesgo académico)**: el modelo de riesgo se construirá sobre las predicciones de dominio que produce el modelo entrenado aquí. Hasta que este documento alcance versión 1.0, el Documento 4 no puede pasar a fase de implementación.
- **Documento 5 (Personalización del aprendizaje)**: el recomendador se alimenta de las predicciones del modelo entrenado aquí.

---

## 10. Referencias

Badrinath, A., Wang, F., & Pardos, Z. (2021). pyBKT: An accessible Python library of Bayesian Knowledge Tracing models. *Proceedings of the 14th International Conference on Educational Data Mining*, 468-474.

Chang, H. S., Hsu, H. J., & Chen, K. T. (2015). Modeling exercise relationships in e-learning: A unified approach. *Proceedings of the 8th International Conference on Educational Data Mining*, 532-535.

Choi, Y., Lee, Y., Cho, J., Baek, J., Kim, B., Cha, Y., Shin, D., Bae, C., & Heo, J. (2020). Towards an appropriate query, key, and value computation for knowledge tracing. *Proceedings of the Seventh ACM Conference on Learning @ Scale*, 341-344. https://doi.org/10.1145/3386527.3405945

Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, *4*(4), 253-278. https://doi.org/10.1007/BF01099821

Heffernan, N. T., & Heffernan, C. L. (2014). The ASSISTments Ecosystem: Building a platform that brings scientists and teachers together for minimally invasive research on human learning and teaching. *International Journal of Artificial Intelligence in Education*, *24*(4), 470-497. https://doi.org/10.1007/s40593-014-0024-x

Liu, Q., Huang, Z., Yin, Y., Chen, E., Xiong, H., Su, Y., & Hu, G. (2019). EKT: Exercise-aware knowledge tracing for student performance prediction. *IEEE Transactions on Knowledge and Data Engineering*, *33*(1), 100-115.

Pandey, S., & Karypis, G. (2019). A self-attentive model for knowledge tracing. *Proceedings of the 12th International Conference on Educational Data Mining*, 384-389.

Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep knowledge tracing. *Advances in Neural Information Processing Systems*, *28*, 505-513.

Yeung, C. K., & Yeung, D. Y. (2018). Addressing two problems in deep knowledge tracing via prediction-consistent regularization. *Proceedings of the Fifth Annual ACM Conference on Learning at Scale*, 1-10.

---

**Control de versiones**

| Versión | Fecha | Cambios |
|---|---|---|
| 0.1 | 2026-05-05 | Estructura inicial y selección preliminar |
| 0.4 | 2026-05-15 | Topologías de DKT y SAKT documentadas |
| 0.7 | 2026-05-24 | Hiperparámetros iniciales, pipeline completo, métricas |
| 1.0 | Pendiente | Resultados empíricos y selección final |
