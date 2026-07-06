# Anexo Técnico — Modelos de IA y Redes Neuronales para Lairn

**Proyecto**: Lairn — Sistema Inteligente de Aprendizaje Adaptativo
**Tipo de documento**: Anexo técnico complementario a los Documentos 1, 2, 4 y 5
**Versión**: 1.0
**Fecha de última actualización**: 2026-05-24

> **Propósito de este anexo.** Este documento explica en profundidad cada uno de los modelos de IA candidatos para Lairn, organizados por caso de uso. Sirve como **glosario técnico extendido** para complementar las decisiones tomadas en los documentos principales y como base para la defensa de tesis. Incluye modelos clásicos, intermedios y de estado del arte, con explicación de su funcionamiento interno, fortalezas, debilidades y aplicabilidad concreta a Lairn.

---

## Cómo Leer Este Anexo

Los modelos se organizan en **4 familias** según su rol en Lairn:

1. **Knowledge Tracing** — modelan qué sabe el estudiante.
2. **Predicción de Riesgo Académico** — predicen abandono o reprobación.
3. **Recomendación / Personalización** — deciden qué presentar a continuación.
4. **NLP y Validación Semántica** — comprenden y comparan texto.

Cada modelo se presenta con la siguiente estructura:

- **Identidad**: año, autores, paper original.
- **Idea central**: qué problema resuelve.
- **Cómo funciona**: explicación intuitiva + arquitectura/fórmula clave.
- **Ventajas**.
- **Limitaciones**.
- **¿Aplica a Lairn?**: veredicto pragmático.

---

# FAMILIA 1 — Knowledge Tracing

El **Knowledge Tracing (KT)** es el problema de estimar, en cada momento, qué conceptos domina un estudiante a partir de su historial de respuestas. Es el núcleo del motor adaptativo: sin saber qué domina el estudiante, no se puede decidir qué pregunta hacerle a continuación.

## 1.1 BKT — Bayesian Knowledge Tracing

**Identidad**: Corbett & Anderson, 1995. Es el modelo fundacional de KT, sigue siendo referencia obligada en cualquier estudio de la materia.

**Idea central**: representar el dominio de cada concepto como una variable binaria latente (`dominado` / `no dominado`) que evoluciona según una cadena de Markov de dos estados.

**Cómo funciona**:

Cada concepto tiene **cuatro parámetros**:

- **p(L₀)** = probabilidad inicial de dominio (antes de cualquier práctica).
- **p(T)** = probabilidad de transitar de "no dominado" a "dominado" tras una práctica (probabilidad de aprender).
- **p(G)** = probabilidad de acertar a pesar de no dominar (probabilidad de adivinar bien).
- **p(S)** = probabilidad de fallar a pesar de dominar (probabilidad de equivocarse por descuido).

Tras cada respuesta del estudiante, BKT actualiza la probabilidad de dominio usando el teorema de Bayes:

```
Si acertó:
P(L_{n+1} | correcta) = P(L_n) × (1 - p(S))
                        ──────────────────────────────
                        P(L_n) × (1 - p(S)) + (1 - P(L_n)) × p(G)

Si falló:
P(L_{n+1} | incorrecta) = P(L_n) × p(S)
                          ──────────────────────────────
                          P(L_n) × p(S) + (1 - P(L_n)) × (1 - p(G))
```

Luego se aplica la transición de aprendizaje:

```
P(L_{n+1}) = P(L_{n+1} | resultado) + (1 - P(L_{n+1} | resultado)) × p(T)
```

**Ventajas**:
- Cada parámetro tiene **interpretación pedagógica directa**.
- Funciona con poquísimos datos (menos de 100 respuestas por concepto pueden bastar).
- Implementaciones maduras (`pyBKT`).
- Ideal como baseline para comparar modelos más complejos.

**Limitaciones**:
- Asume **independencia entre conceptos** (saber A no afecta saber B).
- El dominio es **binario**: no captura niveles intermedios.
- Cada concepto se modela por separado; no aprovecha la estructura del conocimiento.

**¿Aplica a Lairn?**: **Sí, como baseline obligatorio**. Es la referencia contra la que cualquier modelo neuronal debe demostrar mejora.

---

## 1.2 PFA — Performance Factor Analysis

**Identidad**: Pavlik, Cen & Koedinger, 2009.

**Idea central**: predecir el acierto futuro a partir del **número de intentos previos correctos e incorrectos** sobre el mismo concepto, mediante regresión logística.

**Cómo funciona**: para un estudiante respondiendo una pregunta del concepto k:

```
logit(P(correcto)) = β_k + γ_k × s_k + ρ_k × f_k
```

Donde:
- `β_k` = dificultad base del concepto k.
- `s_k` = número de aciertos previos del estudiante en k.
- `f_k` = número de errores previos.
- `γ_k`, `ρ_k` = pesos aprendidos.

**Ventajas**:
- Más interpretable que BKT al exponer explícitamente "aprender por acertar" vs "aprender por equivocarse".
- Más simple de implementar.
- En varios datasets supera a BKT.

**Limitaciones**:
- Sigue siendo independiente entre conceptos.
- No modela orden temporal (no le importa si los aciertos fueron al principio o al final).

**¿Aplica a Lairn?**: **Sí, como baseline alternativo a BKT**. Podría reportarse junto a BKT en la tesis para enriquecer la comparación.

---

## 1.3 IRT — Item Response Theory

**Identidad**: Rasch, 1960 (modelo 1PL); Birnbaum, 1968 (modelos 2PL y 3PL). Base de los exámenes adaptativos clásicos (CAT — Computerized Adaptive Testing).

**Idea central**: modelar la probabilidad de que un estudiante con **habilidad latente θ** responda correctamente una pregunta con **dificultad latente β**.

**Cómo funciona** (modelo 1PL / Rasch):

```
P(correcta | θ, β) = exp(θ - β)
                    ───────────────
                    1 + exp(θ - β)
```

Es una función sigmoide centrada en β. Si la habilidad del estudiante coincide con la dificultad de la pregunta, la probabilidad de acierto es 50 %.

**Variantes**:
- **1PL (Rasch)**: solo dificultad.
- **2PL**: añade **discriminación** (qué tan bien discrimina la pregunta entre estudiantes hábiles y no).
- **3PL**: añade **probabilidad de adivinanza** (útil en multiple choice).

**Ventajas**:
- Fundamento estadístico riguroso, ampliamente validado desde hace 60+ años.
- Permite **calibrar preguntas y estudiantes en la misma escala**.
- Base de los exámenes estandarizados internacionales (GRE, TOEFL).

**Limitaciones**:
- En su forma básica modela **una sola habilidad por estudiante** (no por concepto).
- Requiere **calibración previa** de las preguntas: un examen nuevo necesita validarse con muchos estudiantes antes de usarse. Esto choca con Lairn, donde las preguntas se generan dinámicamente.

**¿Aplica a Lairn?**: **Parcialmente**. Útil como referencia teórica y como modelo de la sesión completa (estimar habilidad global del estudiante en el tema del examen). No es viable como evaluador de cada pregunta individual porque las preguntas son únicas.

---

## 1.4 KT-IDEM — Knowledge Tracing - Item Difficulty Effect Model

**Identidad**: Pardos & Heffernan, 2011.

**Idea central**: extensión de BKT que añade un parámetro de dificultad por **pregunta individual**, no solo por concepto.

**Cómo funciona**: BKT estándar usa `p(G)` y `p(S)` por concepto. KT-IDEM los reemplaza por `p(G_i)` y `p(S_i)` **por pregunta i**. Una pregunta fácil tiene `p(G)` alto y `p(S)` bajo; una difícil al revés.

**Ventajas**:
- Captura que dentro de un mismo concepto hay preguntas más difíciles que otras.
- Mejora moderada sobre BKT (~3-5 % en AUC en ASSISTments).

**Limitaciones**:
- Requiere muchos intentos por pregunta para estimar bien sus parámetros.
- En Lairn las preguntas se generan dinámicamente y rara vez se repiten, por lo que el modelo no tiene cómo calibrar.

**¿Aplica a Lairn?**: **No directamente**, por la generación dinámica. Mencionable como contexto teórico.

---

## 1.5 DKT — Deep Knowledge Tracing

**Identidad**: Piech, Bassen, Huang et al., 2015 (Stanford). El paper que abrió la era del deep learning aplicado a KT.

**Idea central**: usar una **red neuronal recurrente (LSTM)** para aprender automáticamente la dinámica del aprendizaje a partir del historial completo de interacciones, sin asumir independencia entre conceptos.

**Cómo funciona**:

Entrada en el paso t:
```
x_t = one_hot(concepto_t, correcto_t)   ∈ ℝ^(2M)
```
donde M es el número de conceptos. Si el estudiante respondió al concepto 5 correctamente y hay 100 conceptos, x_t es un vector de 200 dimensiones con un 1 en la posición 105 (concepto 5 + offset por "correcto").

Arquitectura:

```
x_t ──► Embedding ──► LSTM ──► h_t ──► Linear+Sigmoid ──► y_t ∈ ℝ^M
                       ▲                                    │
                       │                                    │
                    h_{t-1}                                 ▼
                                              P(acertar concepto k en t+1)
```

El estado oculto `h_t` de la LSTM resume todo el historial. La salida `y_t` da la probabilidad de acertar la próxima pregunta de cada concepto.

**Entrenamiento**: predecir la respuesta del paso t+1 a partir del historial hasta t. Loss: binary cross-entropy.

**Ventajas**:
- **Captura automáticamente relaciones entre conceptos** (saber DFS afecta la predicción de grafos).
- Mejora significativa sobre BKT (~0.86 vs ~0.67 AUC en ASSISTments 2009).
- Una sola red modela todos los conceptos en lugar de tener un BKT por concepto.

**Limitaciones**:
- **Caja negra**: difícil explicar al docente por qué predice lo que predice.
- Requiere volumen de datos (>10 000 secuencias para entrenar bien).
- Sensible a hiperparámetros.

**¿Aplica a Lairn?**: **Sí, modelo principal de la tesis**. Es el balance ideal entre potencia y madurez para el alcance del trabajo de grado.

---

## 1.6 DKVMN — Dynamic Key-Value Memory Networks

**Identidad**: Zhang, Shi, King & Yeung, 2017.

**Idea central**: mejorar DKT introduciendo una **memoria explícita** de conceptos. Separa dos cosas: las claves (conceptos, fijas) y los valores (dominio del estudiante por concepto, dinámicos).

**Cómo funciona**:
- Una matriz **clave** M_k almacena embeddings fijos de cada concepto.
- Una matriz **valor** M_v almacena el estado de dominio del estudiante por concepto (se actualiza con cada respuesta).
- Al recibir una pregunta nueva, se calcula su similitud con los conceptos (atención sobre M_k) y se lee/escribe en M_v acorde.

**Ventajas**:
- Más interpretable que DKT (se puede inspeccionar M_v).
- Modela explícitamente los conceptos como entidades.
- Suele superar a DKT en datasets medianos.

**Limitaciones**:
- Más complejo de implementar y entrenar.
- Hiperparámetros adicionales (tamaño de memoria).

**¿Aplica a Lairn?**: **Opcional**. Si DKT funciona bien y queda tiempo, vale la pena como punto de comparación. No es prioritario.

---

## 1.7 SAKT — Self-Attentive Knowledge Tracing

**Identidad**: Pandey & Karypis, 2019.

**Idea central**: reemplazar la LSTM de DKT por un mecanismo de **auto-atención** (el mismo del Transformer). Permite que el modelo atienda selectivamente a interacciones pasadas relevantes para predecir la actual.

**Cómo funciona**:

La idea clave del **mecanismo de atención** es: en lugar de comprimir todo el historial en un estado oculto (lo que hace LSTM), el modelo aprende **qué interacciones pasadas mirar** para predecir la actual.

Para cada nueva pregunta q_t, el modelo calcula:

```
Atención(q_t, interacciones_pasadas) = softmax( q_t · K^T / √d ) · V
```

donde Q, K, V son proyecciones de las interacciones. El resultado es una combinación ponderada de las interacciones pasadas, donde el peso de cada una refleja su relevancia.

**Arquitectura**:

```
secuencia interacciones
       │
       ▼
   Embeddings + Posicional
       │
       ▼
   Multi-Head Self-Attention
       │
       ▼
   Feed-Forward + LayerNorm
       │
       ▼
   Linear + Sigmoid
       │
       ▼
   Predicción de acierto
```

**Ventajas**:
- Supera a DKT en datasets grandes.
- Más paralelizable durante entrenamiento que LSTM.
- **Interpretabilidad parcial**: los pesos de atención muestran qué interacciones pasadas pesaron más.

**Limitaciones**:
- Más complejo de implementar.
- Requiere aún más datos para evitar sobreajuste.

**¿Aplica a Lairn?**: **Sí, como extensión opcional**. Si los tiempos lo permiten, sirve para comparar arquitectura recurrente vs basada en atención.

---

## 1.8 AKT — Context-aware Attentive Knowledge Tracing

**Identidad**: Ghosh, Heffernan & Lan, 2020.

**Idea central**: mejorar SAKT añadiendo **monotonic attention** (la atención decae con la distancia temporal, modelando el olvido) y embeddings más ricos para preguntas y conceptos.

**Cómo funciona**:

Modificaciones clave sobre SAKT:
- **Monotonic attention**: el peso de cada interacción pasada se multiplica por un factor de decaimiento exponencial. Modelar olvido.
- **Embeddings duales**: separa el embedding del concepto del embedding de la respuesta (correcta/incorrecta).
- **Rasch embeddings**: aplica IRT a los embeddings, capturando dificultad de la pregunta.

**Ventajas**:
- Mejora consistente sobre SAKT en múltiples datasets (~1-2 puntos AUC).
- Modela explícitamente el olvido.

**Limitaciones**:
- Más complejo arquitectónicamente.
- Requiere metadata rica de preguntas (dificultad, concepto, etc.).

**¿Aplica a Lairn?**: **No en alcance de tesis**. Queda como trabajo futuro.

---

## 1.9 SAINT y SAINT+

**Identidad**: Choi et al., 2020 (Riiid, equipo del dataset EdNet).

**Idea central**: aplicar la arquitectura **Transformer encoder-decoder completa** al problema de KT, separando preguntas y respuestas en dos flujos.

**Cómo funciona**:
- Un **encoder** procesa la secuencia de preguntas.
- Un **decoder** procesa la secuencia de respuestas, atendiendo al encoder.
- Esta separación permite que el modelo aprenda representaciones independientes de "qué pregunta es" y "cómo respondió".

**SAINT+** añade features temporales: tiempo entre respuestas, tiempo en cada respuesta.

**Ventajas**:
- Estado del arte en EdNet al momento de publicación.
- Captura interacciones complejas pregunta-respuesta-tiempo.

**Limitaciones**:
- Es el modelo más exigente computacionalmente de la familia.
- Diseñado para volúmenes de **millones** de interacciones.
- Para datasets pequeños se sobreajusta.

**¿Aplica a Lairn?**: **No en alcance de tesis**. Queda como trabajo futuro, solo viable cuando Lairn tenga decenas de miles de estudiantes activos.

---

## 1.10 GKT — Graph Knowledge Tracing

**Identidad**: Nakagawa, Iwasawa & Matsuo, 2019.

**Idea central**: representar las relaciones entre conceptos como un **grafo** y propagar información de dominio a través de él usando una **Graph Neural Network (GNN)**.

**Cómo funciona**: cada concepto es un nodo. Las aristas representan dependencias o similitudes. Al actualizar el dominio de un concepto, la actualización se propaga a sus vecinos en el grafo.

**Ventajas**:
- Modela explícitamente la estructura del conocimiento.
- Funciona bien cuando hay un grafo de prerrequisitos definido.

**Limitaciones**:
- Requiere que el grafo esté disponible (curado por expertos o aprendido).
- Implementación compleja.

**¿Aplica a Lairn?**: **Interesante a largo plazo**, especialmente si Lairn implementa el grafo de prerrequisitos propuesto en el Documento 5. No en alcance de tesis.

---

## 1.11 Otros modelos de KT mencionables

- **CL4KT** (Lee et al., 2022): aplica **contrastive learning** al KT, mejora sobre AKT.
- **simpleKT** (Liu et al., 2023): variante simplificada que muestra que mucha de la complejidad de SAINT/AKT es innecesaria.
- **DTransformer** (Yin et al., 2023): Transformer especializado para sesiones largas.

Estos modelos son investigación reciente y representan la frontera del campo. **Para la tesis no son recomendables** porque la madurez de implementación y reproducibilidad es menor que la de DKT/SAKT.

---

# FAMILIA 2 — Predicción de Riesgo Académico

El problema de predicción de riesgo busca identificar a estudiantes con alta probabilidad de fracasar o abandonar, **antes** de que el problema sea irreversible. A diferencia del KT (que se enfoca en conceptos), el riesgo se enfoca en el estudiante como un todo.

## 2.1 Regresión Logística

**Identidad**: Verhulst, 1838 (origen matemático); aplicación moderna desde mediados del siglo XX.

**Idea central**: modelar la probabilidad de un evento binario (en riesgo / no en riesgo) como una función sigmoide de una combinación lineal de variables predictoras.

**Cómo funciona**:

```
logit(P(en_riesgo)) = β_0 + β_1·x_1 + β_2·x_2 + ... + β_n·x_n
```

Donde `x_i` son las variables predictoras (promedio, asistencia, etc.) y `β_i` los pesos aprendidos.

**Ventajas**:
- **Máxima interpretabilidad**: cada coeficiente dice exactamente cuánto contribuye cada variable.
- Muy rápido de entrenar e inferir.
- Baseline indispensable en cualquier estudio.

**Limitaciones**:
- Asume relaciones lineales entre variables y log-odds.
- No captura interacciones complejas automáticamente.

**¿Aplica a Lairn?**: **Sí, como baseline obligatorio**.

---

## 2.2 Árboles de Decisión

**Identidad**: Quinlan, 1986 (ID3); 1993 (C4.5).

**Idea central**: dividir recursivamente el espacio de variables en regiones que maximicen la pureza de la clase predicha.

**Cómo funciona**: cada nodo del árbol pregunta algo como "¿promedio < 3.5?". Las hojas son las predicciones.

**Ventajas**:
- **Interpretabilidad visual** (literalmente un diagrama).
- Captura no linealidades.

**Limitaciones**:
- Tendencia al sobreajuste si crecen mucho.
- Inestables: pequeños cambios en los datos cambian la estructura del árbol.

**¿Aplica a Lairn?**: **Como componente de ensambles** (Random Forest, XGBoost) sí. Solo no es ideal.

---

## 2.3 Random Forest

**Identidad**: Breiman, 2001.

**Idea central**: entrenar **muchos árboles de decisión** sobre subconjuntos aleatorios de los datos y combinar sus predicciones por voto mayoritario.

**Cómo funciona**:
- Se entrenan N árboles (típicamente N=100-500).
- Cada árbol ve un subconjunto aleatorio de filas (bootstrap) y de columnas (feature subsampling).
- La predicción final es el promedio (regresión) o voto mayoritario (clasificación).

**Ventajas**:
- Excelente desempeño "out of the box".
- Robusto, poco sensible a hiperparámetros.
- Provee **importancia de variables** automáticamente.
- Maneja bien variables heterogéneas (numéricas, categóricas, escalas distintas).

**Limitaciones**:
- Menos interpretable que un solo árbol (aunque herramientas como SHAP lo mitigan).
- Más lento en inferencia que regresión logística.

**¿Aplica a Lairn?**: **Sí, fuertemente recomendado** como modelo principal para riesgo. Probable ganador del benchmark.

---

## 2.4 Gradient Boosting (XGBoost, LightGBM, CatBoost)

**Identidad**: Friedman, 2001 (Gradient Boosting); Chen & Guestrin, 2016 (XGBoost); Ke et al., 2017 (LightGBM); Prokhorenkova et al., 2018 (CatBoost).

**Idea central**: entrenar árboles **secuencialmente**, donde cada árbol nuevo corrige los errores del anterior.

**Cómo funciona**:
1. Se entrena un árbol simple.
2. Se calcula el error (residuo) del árbol.
3. Se entrena otro árbol para predecir ese residuo.
4. Se suma al modelo.
5. Se repite hasta convergencia.

Las tres variantes (XGBoost, LightGBM, CatBoost) son optimizaciones de la misma idea con diferencias prácticas:
- **XGBoost**: el más maduro, balance general.
- **LightGBM**: el más rápido en entrenar, mejor para datasets grandes.
- **CatBoost**: maneja mejor variables categóricas sin one-hot encoding.

**Ventajas**:
- Estado del arte para datos tabulares en la mayoría de competencias (Kaggle).
- Suele superar a Random Forest por 1-3 puntos AUC.

**Limitaciones**:
- Más sensible a hiperparámetros que Random Forest.
- Riesgo de sobreajuste si no se regulariza.

**¿Aplica a Lairn?**: **Sí, fuertemente recomendado**. XGBoost o LightGBM como el modelo principal de riesgo.

---

## 2.5 SVM — Support Vector Machines

**Identidad**: Cortes & Vapnik, 1995.

**Idea central**: encontrar el hiperplano que **maximiza el margen** entre las clases.

**Cómo funciona**: en su forma básica busca un hiperplano lineal. Con el **truco del kernel** (RBF, polinómico) puede capturar fronteras no lineales.

**Ventajas**:
- Excelente desempeño con datasets pequeños y de alta dimensionalidad.
- Fundamento teórico sólido.

**Limitaciones**:
- Se vuelve lento con muchos datos (>100 000 muestras).
- Menos interpretable que árboles.
- Suele ser superado por gradient boosting en datos tabulares.

**¿Aplica a Lairn?**: **Opcional**. Considerarlo como comparación si los datos son pequeños.

---

## 2.6 MLP — Multi-Layer Perceptron

**Identidad**: Rosenblatt, 1958 (Perceptron); Rumelhart, Hinton & Williams, 1986 (backpropagation moderna).

**Idea central**: una red neuronal **densa** con capas ocultas que aplican transformaciones no lineales sucesivas.

**Cómo funciona**:

```
Entrada → Capa Densa + ReLU → Capa Densa + ReLU → ... → Salida + Sigmoid
```

Cada capa densa es una multiplicación de matrices seguida de una activación no lineal. La red aprende los pesos mediante backpropagation.

**Ventajas**:
- Captura cualquier función continua si tiene suficientes neuronas (teorema de aproximación universal).
- Base de todas las arquitecturas modernas.

**Limitaciones**:
- **Suele ser superado por XGBoost en datos tabulares**.
- Requiere ajuste cuidadoso de hiperparámetros (capas, neuronas, dropout, lr).
- Menos interpretable.

**¿Aplica a Lairn?**: **Como comparación experimental**. La hipótesis razonable es que XGBoost gane; documentar esto como hallazgo de la tesis tiene valor.

---

## 2.7 LSTM y GRU para series temporales

**Identidad**: Hochreiter & Schmidhuber, 1997 (LSTM); Cho et al., 2014 (GRU).

**Idea central**: redes recurrentes capaces de manejar dependencias temporales largas en datos secuenciales.

**Cómo funciona** (LSTM):

La LSTM tiene tres "puertas" que controlan el flujo de información:
- **Forget gate**: decide qué olvidar del estado anterior.
- **Input gate**: decide qué información nueva guardar.
- **Output gate**: decide qué información usar para la predicción.

GRU es una simplificación que combina forget e input gate.

**Aplicación a riesgo**: si tenemos la evolución semanal de cada estudiante (notas, asistencia, engagement), una LSTM puede predecir el riesgo proyectado, capturando si la tendencia es a mejorar o empeorar.

**Ventajas**:
- Captura dinámica temporal.
- LSTM es estándar consolidado.

**Limitaciones**:
- Requiere datos longitudinales (no solo "snapshot" actual del estudiante).
- Más datos requeridos que tabulares clásicos.

**¿Aplica a Lairn?**: **Como trabajo futuro**, cuando Lairn tenga datos longitudinales de varias semanas/meses.

---

## 2.8 1D CNN para series temporales

**Identidad**: LeCun et al., 1989 (CNNs); aplicación a series temporales desde ~2014.

**Idea central**: aplicar **convoluciones** sobre series temporales para capturar patrones locales (picos, tendencias cortas).

**Ventajas**:
- Más rápida de entrenar que LSTM.
- Buena para detectar patrones locales.

**Limitaciones**:
- Menos buena para dependencias largas que LSTM/Transformers.

**¿Aplica a Lairn?**: **Mención como alternativa a LSTM**, no prioridad.

---

## 2.9 TabTransformer

**Identidad**: Huang et al., 2020 (AWS).

**Idea central**: aplicar self-attention sobre los **embeddings de columnas categóricas** de un dataset tabular.

**Ventajas**:
- Estado del arte tabular cuando hay muchas variables categóricas.

**Limitaciones**:
- Aún emergente. Suele ser comparable a XGBoost, no claramente superior.

**¿Aplica a Lairn?**: **Mención, no prioridad** para tesis.

---

# FAMILIA 3 — Recomendación / Personalización

Los modelos de recomendación deciden **qué presentar a continuación** al estudiante.

## 3.1 Filtrado Colaborativo (Collaborative Filtering)

**Identidad**: Goldberg et al., 1992 (concepto); Sarwar et al., 2001 (item-based).

**Idea central**: "estudiantes parecidos a vos encontraron útil X, así que te recomiendo X".

**Variantes**:
- **User-based**: encuentra usuarios similares y recomienda lo que ellos consumieron.
- **Item-based**: encuentra ítems similares a los que el usuario ya consumió.

**Ventajas**:
- Captura patrones implícitos del grupo.
- Conceptualmente simple.

**Limitaciones**:
- **Cold start poblacional**: necesita muchos usuarios para funcionar.
- **Cold start de ítems**: ítems nuevos no se recomiendan.

**¿Aplica a Lairn?**: **No en fase actual**. Lairn tiene pocos usuarios; cuando crezca, podría usarse.

---

## 3.2 Matrix Factorization (SVD, NMF)

**Identidad**: SVD (Singular Value Decomposition) — algoritmo clásico de álgebra lineal; aplicación moderna a recomendación desde Koren et al., 2009 (Netflix Prize).

**Idea central**: aproximar la matriz de interacciones usuario-ítem como producto de dos matrices más pequeñas (embeddings de usuarios y embeddings de ítems).

**Cómo funciona**:

```
R (n_users × n_items)  ≈  U (n_users × k) · V^T (k × n_items)
```

Cada usuario y cada ítem se representan como vectores en un espacio latente de dimensión k. La predicción de "interacción usuario u con ítem i" es el producto punto u·v.

**Ventajas**:
- Captura factores latentes que explican preferencias.
- Eficiente en cómputo e inferencia.

**Limitaciones**:
- Lineal (NMF / SVD básico).
- Requiere reentrenamiento periódico.

**¿Aplica a Lairn?**: **Como referencia teórica**, no prioritario.

---

## 3.3 Neural Collaborative Filtering (NCF)

**Identidad**: He et al., 2017.

**Idea central**: reemplazar el producto punto de Matrix Factorization por una **red neuronal MLP** que aprende interacciones no lineales entre embeddings de usuario e ítem.

**Arquitectura**:

```
usuario_id ──► Embedding ──┐
                            ├──► Concat ──► MLP ──► Sigmoid ──► P(interacción)
ítem_id ──► Embedding ──────┘
```

**Ventajas**:
- Mejora sobre Matrix Factorization clásica.
- Flexible: puede incorporar features adicionales.

**Limitaciones**:
- Requiere más datos que MF clásica.
- Mismo problema de cold start.

**¿Aplica a Lairn?**: **No en fase actual**. Útil cuando haya volumen.

---

## 3.4 GRU4Rec — Session-based Recommendation con RNN

**Identidad**: Hidasi et al., 2016.

**Idea central**: usar una **GRU** para predecir el siguiente ítem en una **sesión** del usuario (sin necesidad de ID de usuario persistente).

**Ventajas**:
- No necesita historial largo del usuario, solo la sesión actual.
- Adecuado para usuarios anónimos o sin historial.

**Limitaciones**:
- Pierde información de preferencias persistentes.

**¿Aplica a Lairn?**: **Interesante**. Cada sesión de examen es una sesión natural; podría usarse para recomendar la siguiente pregunta dentro del examen, complementando al KT.

---

## 3.5 SASRec — Self-Attentive Sequential Recommendation

**Identidad**: Kang & McAuley, 2018.

**Idea central**: análogo a SAKT pero para recomendación. Usa self-attention sobre la secuencia de ítems consumidos para predecir el siguiente.

**Ventajas**:
- Estado del arte en recomendación secuencial.
- Más paralelizable que GRU4Rec.

**Limitaciones**:
- Requiere muchas sesiones para entrenar bien.

**¿Aplica a Lairn?**: **Trabajo futuro**.

---

## 3.6 BERT4Rec

**Identidad**: Sun et al., 2019.

**Idea central**: aplicar **BERT** (encoder bidireccional) a recomendación secuencial.

**Diferencia con SASRec**: SASRec es unidireccional (solo mira hacia atrás); BERT4Rec es bidireccional con tarea de "masked item prediction" (similar al masked language modeling de BERT).

**Ventajas**:
- Suele superar a SASRec.

**Limitaciones**:
- Más complejo y costoso.

**¿Aplica a Lairn?**: **Trabajo futuro**.

---

## 3.7 Graph Neural Networks (GNN) para recomendación

**Identidad**: Berg et al., 2017 (GC-MC); Wang et al., 2019 (NGCF); He et al., 2020 (LightGCN).

**Idea central**: modelar la relación usuario-ítem como un **grafo bipartito** y aprender representaciones propagando información a través de las aristas.

**Ventajas**:
- Captura estructura de relaciones de orden superior (amigos de amigos, productos relacionados).
- Estado del arte en muchos benchmarks de recomendación.

**Limitaciones**:
- Implementación compleja.
- Requiere infraestructura de grafos.

**¿Aplica a Lairn?**: **Mención, no prioritario**. Si en algún momento Lairn modela el grafo de conceptos explícitamente, los GNN serían naturales.

---

## 3.8 Contextual Bandits

**Identidad**: Auer et al., 2002 (UCB); Li et al., 2010 (LinUCB, contextual).

**Idea central**: marco de **exploración vs explotación** donde el sistema balancea entre recomendar lo que ya sabe que funciona (explotación) y probar opciones nuevas (exploración).

**Cómo funciona**:
- Cada decisión es un "bandit arm" (un brazo de una máquina tragamonedas).
- El sistema observa el contexto (estado del estudiante), elige un brazo, observa la recompensa.
- Actualiza la política para mejorar.

**Ventajas**:
- Aprende **online** sin necesidad de un dataset histórico grande.
- Buen balance entre simplicidad y poder.

**Limitaciones**:
- Más difícil de explicar al docente.
- Requiere definir bien la recompensa.

**¿Aplica a Lairn?**: **Opción interesante** como alternativa a las heurísticas, especialmente cuando todavía hay pocos datos.

---

## 3.9 Deep Reinforcement Learning para recomendación

**Identidad**: Mnih et al., 2015 (DQN); aplicación a recomendación desde Zhao et al., 2018 y posteriores.

**Idea central**: modelar la recomendación como un **proceso de decisión de Markov** y aprender una **política óptima** mediante RL profundo.

**Ventajas**:
- Maximiza recompensa a **largo plazo**, no solo el siguiente clic.
- En educación esto significa optimizar el aprendizaje del semestre, no solo la siguiente respuesta.

**Limitaciones**:
- Requiere **muchos** datos.
- Inestable durante entrenamiento.
- Difícil de explicar.
- Riesgo de comportamiento errático en producción.

**¿Aplica a Lairn?**: **Trabajo futuro, lejano**. Doroudi, Aleven y Brunskill (2019) revisaron RL para secuenciación educativa y concluyeron que el campo aún tiene resultados mixtos.

---

# FAMILIA 4 — NLP y Validación Semántica

Esta familia es **distinta** a las anteriores. No modela aprendizaje; modela **comprensión de lenguaje**. Es relevante si Lairn evoluciona a aceptar respuestas abiertas o si quiere validar semánticamente que la respuesta correcta marcada por la IA es realmente correcta.

## 4.1 TF-IDF + Similitud Coseno

**Identidad**: Spärck Jones, 1972 (IDF).

**Idea central**: representar textos como vectores de frecuencia de palabras ponderadas por su rareza (TF-IDF) y comparar por similitud coseno.

**Ventajas**:
- Trivial de implementar.
- Sin entrenamiento.
- Interpretable.

**Limitaciones**:
- No captura significado, solo coincidencia léxica.
- "Felino" y "gato" son completamente distintos para TF-IDF.

**¿Aplica a Lairn?**: **Como baseline trivial** si se implementa validación semántica.

---

## 4.2 Word2Vec, GloVe, FastText

**Identidad**: Mikolov et al., 2013 (Word2Vec); Pennington et al., 2014 (GloVe); Bojanowski et al., 2017 (FastText).

**Idea central**: representar cada palabra como un vector denso donde la cercanía vectorial refleja cercanía semántica.

**Ventajas**:
- Captura significado básico.
- "Rey - hombre + mujer ≈ reina".

**Limitaciones**:
- Una palabra tiene un solo vector independiente del contexto.
- Superados por BERT y posteriores.

**¿Aplica a Lairn?**: **Mención histórica**, no prioritario.

---

## 4.3 BERT — Bidirectional Encoder Representations from Transformers

**Identidad**: Devlin et al., 2018 (Google).

**Idea central**: pre-entrenar un Transformer bidireccional sobre grandes corpus de texto, y luego fine-tunearlo para tareas específicas (clasificación, NLI, similitud).

**Cómo funciona**:
- Arquitectura: **Transformer encoder** con atención bidireccional.
- Pre-entrenamiento: **Masked Language Modeling** (predecir palabras enmascaradas) + **Next Sentence Prediction**.
- Genera embeddings de palabras **contextuales**: la misma palabra tiene distinto embedding según el contexto.

**Ventajas**:
- Revolucionó el NLP. Estado del arte en muchas tareas hasta hoy.
- Comprensión profunda del lenguaje.

**Limitaciones**:
- Pesado (~110M parámetros base, ~340M large).
- Inferencia más lenta que modelos clásicos.

**¿Aplica a Lairn?**: **Sí, base para validación semántica si se necesita**. Versión multilingüe (mBERT, XLM-R) para español.

---

## 4.4 Sentence-BERT / Sentence Transformers

**Identidad**: Reimers & Gurevych, 2019.

**Idea central**: adaptar BERT para producir **embeddings de oraciones completas** que sean directamente comparables por similitud coseno.

**Cómo funciona**: se entrena BERT con una arquitectura siamesa sobre pares de oraciones etiquetadas como similares/no similares. El resultado son embeddings de oración optimizados para comparación.

**Ventajas**:
- Permite **buscar oraciones similares de manera eficiente** (comparación coseno entre embeddings).
- Existen modelos pequeños y rápidos (MiniLM, ~22M parámetros).

**Limitaciones**:
- Las versiones más pequeñas pierden precisión.

**¿Aplica a Lairn?**: **Sí, ideal para validación semántica de respuestas abiertas**. Si el estudiante responde "DFS usa pila" y la respuesta correcta es "El recorrido en profundidad usa una estructura LIFO", Sentence-BERT detecta que son semánticamente equivalentes.

---

## 4.5 MiniLM, DistilBERT, TinyBERT

**Identidad**: MiniLM (Wang et al., 2020); DistilBERT (Sanh et al., 2019); TinyBERT (Jiao et al., 2020).

**Idea central**: versiones **destiladas** de BERT que son 2-10× más pequeñas y rápidas, manteniendo 95-97 % del desempeño.

**Cómo funcionan**: se entrena un modelo "estudiante" pequeño para imitar las predicciones del modelo "maestro" (BERT grande).

**Ventajas**:
- Aptas para producción.
- Inferencia rápida en CPU.

**Limitaciones**:
- Pequeña pérdida de precisión.

**¿Aplica a Lairn?**: **Sí, alta prioridad** si se hace validación semántica en producción.

---

## 4.6 Cross-Encoder de NLI (Natural Language Inference)

**Identidad**: Conneau et al., 2017 (NLI moderna); aplicación a sistemas de evaluación desde varios trabajos posteriores.

**Idea central**: en lugar de comparar embeddings, alimentar **dos textos juntos** a un Transformer entrenado para clasificar si uno **implica** al otro.

**Cómo funciona**: el modelo recibe (respuesta_correcta, respuesta_estudiante) y devuelve una de tres etiquetas: `entailment` (la respuesta del estudiante implica la correcta), `neutral`, `contradiction`.

**Ventajas**:
- Más preciso que Sentence-BERT para verificar implicación lógica.

**Limitaciones**:
- Más lento (no escalable a comparaciones masivas).

**¿Aplica a Lairn?**: **Sí, para evaluar respuestas abiertas individuales** (una llamada por respuesta).

---

## 4.7 LaBSE — Language-Agnostic BERT Sentence Embedding

**Identidad**: Feng et al., 2020 (Google).

**Idea central**: Sentence-BERT entrenado en 109 lenguajes para producir embeddings comparables **cross-lingually**.

**Ventajas**:
- Útil si Lairn maneja múltiples idiomas.
- Permite comparar una respuesta en español con la correcta en inglés.

**Limitaciones**:
- Modelo grande.

**¿Aplica a Lairn?**: **Mención**, en caso de extensión multilingüe.

---

## 4.8 LLM como juez (GPT-4o, Claude 3.5 Sonnet, etc.)

**Identidad**: enfoque emergente desde 2023 ("LLM-as-a-Judge", Zheng et al., 2023).

**Idea central**: dar la pregunta, la respuesta correcta y la respuesta del estudiante a un LLM grande, y pedirle que evalúe.

**Cómo funciona**: prompt estructurado:

```
"Tarea: Evaluar si la respuesta del estudiante es correcta.
Pregunta: {pregunta}
Respuesta correcta: {respuesta_correcta}
Respuesta del estudiante: {respuesta_estudiante}

Responde JSON: {"correcta": bool, "razon": "...", "confianza": 0-1}"
```

**Ventajas**:
- **Capacidad de razonamiento**: puede evaluar respuestas matemáticas, código, ensayos.
- Provee feedback en lenguaje natural.

**Limitaciones**:
- **Costo y latencia**: cada evaluación cuesta dinero.
- Dependencia de proveedor externo.
- Posibles sesgos del LLM.

**¿Aplica a Lairn?**: **Opción de alto valor para validación de respuestas abiertas complejas**, y para generar el feedback narrativo que hoy no existe.

---

# Tabla Maestra Comparativa

## Resumen por caso de uso

| Caso de uso | Modelo recomendado para tesis | Mejor a largo plazo | Trabajo futuro |
|---|---|---|---|
| **Knowledge Tracing** | DKT (LSTM) | SAKT o AKT | SAINT, GKT, CL4KT |
| **Riesgo académico** | XGBoost o Random Forest | TabTransformer o MLP | LSTM con datos longitudinales |
| **Recomendación** | Heurística + grafo de prerrequisitos | NCF o SASRec | GNN o Deep RL |
| **Validación semántica** | Sentence-BERT (MiniLM) | Cross-encoder NLI | LLM como juez |

## Tabla maestra completa: 30+ modelos comparados

| # | Modelo | Familia | Tipo | Año | Aplica a tesis | Prioridad |
|---|---|---|---|---|---|---|
| 1 | BKT | KT | Probabilístico | 1995 | ✅ Sí | Alta (baseline) |
| 2 | PFA | KT | Regresión logística | 2009 | ✅ Sí | Media (baseline alterno) |
| 3 | IRT (1PL/2PL/3PL) | KT | Estadístico | 1960 | 🔵 Parcial | Media |
| 4 | KT-IDEM | KT | Probabilístico | 2011 | ❌ No | — |
| 5 | DKT | KT | LSTM | 2015 | ✅ Sí | **Principal** |
| 6 | DKVMN | KT | Memory Network | 2017 | 🔵 Opcional | Baja |
| 7 | SAKT | KT | Transformer (atención) | 2019 | 🔵 Opcional | Media |
| 8 | AKT | KT | Transformer + olvido | 2020 | ❌ No | Trabajo futuro |
| 9 | SAINT / SAINT+ | KT | Transformer enc-dec | 2020 | ❌ No | Trabajo futuro |
| 10 | GKT | KT | Graph Neural Network | 2019 | ❌ No | Trabajo futuro |
| 11 | CL4KT | KT | Contrastive learning | 2022 | ❌ No | Trabajo futuro |
| 12 | Regresión Logística | Riesgo | Lineal | 1838 | ✅ Sí | Alta (baseline) |
| 13 | Árboles de Decisión | Riesgo | No lineal | 1986 | 🔵 Vía Random Forest | — |
| 14 | Random Forest | Riesgo | Ensamble | 2001 | ✅ Sí | Alta |
| 15 | XGBoost | Riesgo | Gradient Boosting | 2016 | ✅ Sí | **Principal** |
| 16 | LightGBM | Riesgo | Gradient Boosting | 2017 | ✅ Sí | Alta (alternativa) |
| 17 | CatBoost | Riesgo | Gradient Boosting | 2018 | 🔵 Opcional | Baja |
| 18 | SVM | Riesgo | Margen máximo | 1995 | 🔵 Opcional | Baja |
| 19 | MLP | Riesgo | Red neuronal densa | 1986 | 🔵 Comparación | Media |
| 20 | LSTM / GRU | Riesgo | Red neuronal recurrente | 1997/2014 | ❌ No | Trabajo futuro |
| 21 | 1D CNN | Riesgo | Convolucional | 1989 | ❌ No | Trabajo futuro |
| 22 | TabTransformer | Riesgo | Transformer tabular | 2020 | ❌ No | Trabajo futuro |
| 23 | Filtrado Colaborativo | Recom | Memory-based | 1992 | ❌ No | Trabajo futuro |
| 24 | Matrix Factorization | Recom | Álgebra lineal | 2009 | ❌ No | Trabajo futuro |
| 25 | NCF | Recom | MLP + embeddings | 2017 | ❌ No | Trabajo futuro |
| 26 | GRU4Rec | Recom | RNN secuencial | 2016 | 🔵 Interesante | Baja |
| 27 | SASRec | Recom | Self-attention | 2018 | ❌ No | Trabajo futuro |
| 28 | BERT4Rec | Recom | BERT bidireccional | 2019 | ❌ No | Trabajo futuro |
| 29 | GNN para recomendación | Recom | Graph Neural Network | 2019 | ❌ No | Trabajo futuro |
| 30 | Contextual Bandits | Recom | RL clásico | 2010 | 🔵 Opción | Media |
| 31 | Deep RL | Recom | NN + policy | 2018 | ❌ No | Trabajo futuro lejano |
| 32 | TF-IDF + coseno | NLP | Estadístico | 1972 | 🔵 Baseline trivial | Baja |
| 33 | Word2Vec / GloVe | NLP | Embedding de palabras | 2013-2014 | ❌ No | — |
| 34 | BERT base | NLP | Transformer | 2018 | 🔵 Vía S-BERT | — |
| 35 | Sentence-BERT (MiniLM) | NLP | Embedding de oraciones | 2019 | 🔵 Si hay abiertas | Media |
| 36 | Cross-Encoder NLI | NLP | Transformer + clasif. | 2017 | 🔵 Si hay abiertas | Media |
| 37 | LaBSE | NLP | Embeddings multilingüe | 2020 | ❌ No | Trabajo futuro |
| 38 | LLM como juez (GPT-4o, Claude) | NLP | LLM | 2023 | 🔵 Para feedback | Media |

---

# Recomendación Final por Caso

## Lo que SÍ va en la tesis (8 semanas, 2 personas)

### Knowledge Tracing
- **BKT** (baseline) — vía `pyBKT`.
- **DKT** (modelo neuronal principal) — implementación en PyTorch.
- **SAKT** (opcional, comparación con atención) — si los tiempos lo permiten.

### Riesgo Académico
- **Regresión Logística** (baseline).
- **Random Forest** o **XGBoost** (modelo principal).
- **MLP** (comparación con red neuronal simple).

### Recomendación
- **Heurística** sobre grafo de prerrequisitos + predicciones de KT.

### Validación Semántica
- **Sin cambios** respecto al sistema actual (string match).

## Lo que queda como Trabajo Futuro

- AKT, SAINT, SAINT+, GKT (modelos avanzados de KT).
- LSTM/GRU/Transformer para riesgo.
- Recomendación neuronal (NCF, SASRec, GNN, Deep RL).
- Validación semántica con Sentence-BERT / Cross-encoder / LLM como juez.

---

# Por Qué los Modelos Seleccionados Son los "Mejores" para Lairn

La palabra "mejor" es engañosa en ML. **No hay un modelo universalmente mejor**, hay modelos mejor adaptados a un contexto. Los criterios concretos por los que los modelos seleccionados son los mejores **para el contexto específico de Lairn en una tesis de 8 semanas** son:

1. **Madurez de implementación**: hay código abierto reproducible para BKT, DKT, SAKT, RF y XGBoost. No hay que reinventar la rueda.

2. **Volumen de datos requerido**: BKT y RF funcionan con cientos de muestras. DKT requiere miles, pero ASSISTments aporta cientos de miles. SAINT requeriría millones que Lairn no tiene.

3. **Interpretabilidad**: BKT y RF son interpretables, lo que es crucial para defender la tesis ante un jurado y para que el docente confíe en el sistema.

4. **Tiempo de entrenamiento**: BKT entrena en segundos; DKT en horas con GPU. SAINT requiere días.

5. **Capacidad del equipo**: 2 personas con experiencia limitada en deep learning pueden manejar DKT con la documentación disponible. SAINT y modelos contemporáneos requieren expertise mayor.

6. **Riesgo de defensa**: implementar BKT + DKT permite responder con seguridad cualquier pregunta de jurado. Implementar SAINT mal genera riesgo de no poder defender.

7. **Contribución medible**: comparar BKT vs DKT en datasets públicos + simulación con estudiantes sintéticos da una contribución empírica clara y publicable.

---

# Referencias

Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time analysis of the multiarmed bandit problem. *Machine Learning*, *47*(2), 235-256.

Berg, R. v. d., Kipf, T. N., & Welling, M. (2017). Graph convolutional matrix completion. *arXiv preprint arXiv:1706.02263*.

Birnbaum, A. (1968). Some latent trait models and their use in inferring an examinee's ability. In F. M. Lord & M. R. Novick, *Statistical Theories of Mental Test Scores*. Addison-Wesley.

Bojanowski, P., Grave, E., Joulin, A., & Mikolov, T. (2017). Enriching word vectors with subword information. *Transactions of the Association for Computational Linguistics*, *5*, 135-146.

Breiman, L. (2001). Random forests. *Machine Learning*, *45*(1), 5-32.

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD*, 785-794.

Cho, K., van Merriënboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder-decoder. *EMNLP 2014*.

Choi, Y., Lee, Y., Cho, J., Baek, J., Kim, B., Cha, Y., Shin, D., Bae, C., & Heo, J. (2020). Towards an appropriate query, key, and value computation for knowledge tracing. *L@S 2020*.

Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, *4*(4), 253-278.

Cortes, C., & Vapnik, V. (1995). Support-vector networks. *Machine Learning*, *20*(3), 273-297.

Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep bidirectional transformers for language understanding. *NAACL 2019*.

Doroudi, S., Aleven, V., & Brunskill, E. (2019). Where's the reward? A review of reinforcement learning for instructional sequencing. *IJAIED*, *29*(4), 568-620.

Feng, F., Yang, Y., Cer, D., Arivazhagan, N., & Wang, W. (2020). Language-agnostic BERT sentence embedding. *arXiv preprint arXiv:2007.01852*.

Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *Annals of Statistics*, 1189-1232.

Ghosh, A., Heffernan, N., & Lan, A. S. (2020). Context-aware attentive knowledge tracing. *KDD 2020*.

Goldberg, D., Nichols, D., Oki, B. M., & Terry, D. (1992). Using collaborative filtering to weave an information tapestry. *Communications of the ACM*, *35*(12), 61-70.

He, X., Liao, L., Zhang, H., Nie, L., Hu, X., & Chua, T. S. (2017). Neural collaborative filtering. *WWW 2017*.

Hidasi, B., Karatzoglou, A., Baltrunas, L., & Tikk, D. (2016). Session-based recommendations with recurrent neural networks. *ICLR 2016*.

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation*, *9*(8), 1735-1780.

Huang, X., Khetan, A., Cvitkovic, M., & Karnin, Z. (2020). TabTransformer: Tabular data modeling using contextual embeddings. *arXiv preprint arXiv:2012.06678*.

Kang, W. C., & McAuley, J. (2018). Self-attentive sequential recommendation. *ICDM 2018*.

Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *NeurIPS 2017*.

Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for recommender systems. *Computer*, *42*(8), 30-37.

LeCun, Y., Boser, B., Denker, J. S., Henderson, D., Howard, R. E., Hubbard, W., & Jackel, L. D. (1989). Backpropagation applied to handwritten zip code recognition. *Neural Computation*, *1*(4), 541-551.

Li, L., Chu, W., Langford, J., & Schapire, R. E. (2010). A contextual-bandit approach to personalized news article recommendation. *WWW 2010*.

Mikolov, T., Sutskever, I., Chen, K., Corrado, G. S., & Dean, J. (2013). Distributed representations of words and phrases. *NeurIPS 2013*.

Mnih, V., Kavukcuoglu, K., Silver, D., et al. (2015). Human-level control through deep reinforcement learning. *Nature*, *518*(7540), 529-533.

Nakagawa, H., Iwasawa, Y., & Matsuo, Y. (2019). Graph-based knowledge tracing. *Web Intelligence 2019*.

Pandey, S., & Karypis, G. (2019). A self-attentive model for knowledge tracing. *EDM 2019*, 384-389.

Pardos, Z. A., & Heffernan, N. T. (2011). KT-IDEM: Introducing item difficulty to the knowledge tracing model. *UMAP 2011*, 243-254.

Pavlik, P. I., Cen, H., & Koedinger, K. R. (2009). Performance factors analysis: A new alternative to knowledge tracing. *AIED 2009*.

Pennington, J., Socher, R., & Manning, C. (2014). GloVe: Global vectors for word representation. *EMNLP 2014*.

Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep knowledge tracing. *NeurIPS 2015*, 505-513.

Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). CatBoost: Unbiased boosting with categorical features. *NeurIPS 2018*.

Quinlan, J. R. (1986). Induction of decision trees. *Machine Learning*, *1*(1), 81-106.

Rasch, G. (1960). *Probabilistic models for some intelligence and attainment tests*. Danmarks Pædagogiske Institut.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. *EMNLP 2019*.

Rosenblatt, F. (1958). The perceptron: A probabilistic model for information storage and organization in the brain. *Psychological Review*, *65*(6), 386-408.

Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. *Nature*, *323*(6088), 533-536.

Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. *NeurIPS 2019 Workshop*.

Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). Item-based collaborative filtering recommendation algorithms. *WWW 2001*.

Spärck Jones, K. (1972). A statistical interpretation of term specificity and its application in retrieval. *Journal of Documentation*, *28*(1), 11-21.

Sun, F., Liu, J., Wu, J., Pei, C., Lin, X., Ou, W., & Jiang, P. (2019). BERT4Rec: Sequential recommendation with bidirectional encoder representations from transformer. *CIKM 2019*.

Verhulst, P. F. (1838). Notice sur la loi que la population suit dans son accroissement. *Correspondance Mathématique et Physique*, *10*, 113-121.

Wang, X., He, X., Wang, M., Feng, F., & Chua, T. S. (2019). Neural graph collaborative filtering. *SIGIR 2019*.

Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers. *NeurIPS 2020*.

Zhang, J., Shi, X., King, I., & Yeung, D. Y. (2017). Dynamic key-value memory networks for knowledge tracing. *WWW 2017*, 765-774.

Zhao, X., Xia, L., Zhang, L., Ding, Z., Yin, D., & Tang, J. (2018). Recommendations with negative feedback via pairwise deep reinforcement learning. *KDD 2018*.

Zheng, L., Chiang, W. L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *arXiv preprint arXiv:2306.05685*.

---

**Control de versiones**

| Versión | Fecha | Cambios |
|---|---|---|
| 0.5 | 2026-05-20 | Borrador inicial con 4 familias y ~20 modelos |
| 1.0 | 2026-05-24 | Versión completa con 38 modelos, tabla maestra, recomendación final, referencias |
