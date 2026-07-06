# Documento 1 — Investigación y Selección de Agentes de Inteligencia Artificial

**Proyecto**: Lairn — Sistema Inteligente de Aprendizaje Adaptativo
**Tipo de documento**: Investigación técnica
**Versión**: 0.8 (borrador avanzado)
**Estado de avance reportado**: 80 %
**Fecha de última actualización**: 2026-05-24

> **Nota sobre el estado del documento.** Esta es una versión preliminar avanzada. La selección definitiva del o los agentes a integrar en producción depende de los experimentos de validación contemplados en los Documentos 2 (Entrenamiento) y 4 (Predicción de riesgo). La sección 7 enumera explícitamente los pendientes.

---

## 1. Introducción

Los sistemas tradicionales de evaluación educativa están limitados a registrar puntajes y calcular promedios. No comprenden *qué* sabe cada estudiante, no detectan vacíos conceptuales específicos y no personalizan la dificultad ni la secuencia de los contenidos. Este enfoque ignora décadas de evidencia en ciencias del aprendizaje que muestran que la práctica adaptativa, la retroalimentación oportuna y la secuenciación basada en el dominio mejoran significativamente los resultados (VanLehn, 2011).

En este contexto, los **agentes de inteligencia artificial** ofrecen herramientas para cerrar esa brecha. El término "agente de IA" en la literatura actual abarca un espectro amplio: modelos de lenguaje a gran escala (LLMs) capaces de generar contenido educativo, modelos secuenciales que rastrean el conocimiento del estudiante a lo largo del tiempo (Knowledge Tracing), sistemas de recomendación que sugieren la siguiente unidad a estudiar, y arquitecturas conversacionales que simulan un tutor uno-a-uno.

El sistema **Lairn** se concibe como una plataforma híbrida en la que conviven dos familias de IA con responsabilidades claramente diferenciadas:

- **IA generativa**: encargada de producir el contenido evaluativo (preguntas, retroalimentación textual, explicaciones).
- **IA de modelado del aprendizaje**: encargada de inferir, predecir y adaptar el flujo del examen a partir del historial del estudiante.

Este documento investiga los agentes candidatos para cada familia, compara sus características y propone los más adecuados para integrar en la arquitectura actual de Lairn, que ya cuenta con una primera implementación basada en la API de OpenAI para la generación de preguntas y un modelo de conocimiento por concepto almacenado en PostgreSQL.

### 1.1 Objetivos del documento

1. Identificar y describir los agentes y arquitecturas de IA pertinentes al dominio de evaluación adaptativa.
2. Definir criterios objetivos de comparación entre ellos.
3. Producir una tabla comparativa que sirva como insumo para la selección definitiva.
4. Emitir una conclusión preliminar sobre los agentes más prometedores para Lairn.
5. Documentar los pendientes para la versión final.

### 1.2 Alcance y limitaciones

Este documento se limita a una revisión técnica de agentes ya documentados en la literatura científica o por sus proveedores. No incluye benchmarks empíricos propios; estos se realizarán en el marco del Documento 2 sobre el proceso de entrenamiento. Tampoco incluye análisis financiero detallado del costo total de propiedad de cada solución; ese análisis se contemplará en la versión final una vez seleccionados los candidatos finalistas.

---

## 2. Marco Conceptual

### 2.1 Definición de agente de IA

En el contexto de este trabajo, se entiende por **agente de IA** todo sistema computacional que recibe información estructurada del entorno (en este caso, las interacciones del estudiante con la plataforma), realiza inferencias o produce contenido, y devuelve una decisión o un artefacto utilizable por el sistema mayor (Russell & Norvig, 2021).

Bajo esta definición caben tanto un modelo generativo como GPT-4 (que produce preguntas en texto natural) como un modelo estadístico como BKT (que produce una probabilidad de dominio). La heterogeneidad de candidatos es intencional: Lairn requiere agentes especializados para tareas distintas.

### 2.2 Taxonomía aplicable al proyecto

Para organizar la investigación, se distinguen cuatro familias de agentes relevantes:

| Familia | Función en Lairn | Ejemplos representativos |
|---|---|---|
| **LLMs generativos** | Generar preguntas, explicaciones y retroalimentación | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3 |
| **Frameworks de agentes con herramientas** | Orquestar llamadas a LLMs con memoria y acceso a la base de datos | OpenAI Agents SDK, LangChain, LlamaIndex |
| **Modelos de Knowledge Tracing** | Estimar el dominio del estudiante por concepto y predecir el desempeño futuro | BKT, IRT, DKT, SAKT, AKT, SAINT |
| **Sistemas de recomendación adaptativa** | Decidir qué concepto presentar a continuación | Bandits contextuales, modelos basados en grafos de dependencias |

Las secciones 3 a 3.4 desarrollan cada familia.

---

## 3. Revisión de Agentes Investigados

### 3.1 LLMs generativos

Los modelos de lenguaje a gran escala constituyen el núcleo de la IA generativa moderna. En el contexto educativo se utilizan principalmente para tres tareas: (a) generar preguntas alineadas a un concepto y nivel de dificultad, (b) producir retroalimentación textual personalizada y (c) evaluar respuestas abiertas.

#### 3.1.1 GPT-4o (OpenAI)

Modelo multimodal de OpenAI con capacidades de razonamiento, generación textual y comprensión visual. Actualmente es el agente generativo que Lairn utiliza en producción a través del módulo `apps/motor_adaptativo/services/agente_ia.py`.

**Ventajas:**
- Calidad de generación consistentemente alta en español académico.
- Soporte oficial para *function calling* y *structured outputs* (JSON Schema).
- Documentación madura y ecosistema amplio.

**Limitaciones:**
- Costo por token, no despreciable a escala.
- Latencia variable (300 ms a varios segundos por petición).
- Dependencia de proveedor externo (riesgo de cambios en pricing o disponibilidad).
- Datos enviados se procesan en infraestructura del proveedor (consideraciones de privacidad).

#### 3.1.2 Claude 3.5 Sonnet (Anthropic)

Familia de modelos desarrollada por Anthropic, con énfasis en seguridad y alineamiento. Destaca en tareas de razonamiento extenso y manejo de contextos largos (200 k tokens).

**Ventajas:**
- Mejor desempeño que GPT-4o en algunos benchmarks de razonamiento (Anthropic, 2024).
- Ventana de contexto amplia, útil para incluir historial completo del estudiante en cada llamada.
- Política de no entrenamiento sobre datos de clientes por defecto.

**Limitaciones:**
- Costo comparable al de GPT-4o.
- Ecosistema en torno a herramientas (*tool use*) menos maduro que el de OpenAI al momento de redacción.

#### 3.1.3 Gemini 1.5 Pro (Google)

Modelo multimodal de Google con énfasis en contexto extendido (hasta 2 M tokens en versión Pro).

**Ventajas:**
- Ventana de contexto extremadamente amplia.
- Integración nativa con servicios de Google Cloud (útil si la infraestructura migra a GCP).

**Limitaciones:**
- Calidad inferior a GPT-4o y Claude en evaluaciones de razonamiento en español académico (Chiang et al., 2024).
- Menor adopción en la comunidad EdTech.

#### 3.1.4 Llama 3 (Meta) — opción open source

Familia de modelos abiertos de Meta, disponibles en variantes de 8B, 70B y 405B parámetros. Permite *self-hosting*, lo que elimina la dependencia de proveedores externos.

**Ventajas:**
- Sin costos de API: solo costo de infraestructura propia.
- Privacidad total: los datos nunca salen de la infraestructura propia.
- Posibilidad de *fine-tuning* sobre el dominio educativo.

**Limitaciones:**
- Calidad inferior a los modelos propietarios en tareas de generación creativa en español (al momento del análisis).
- Requiere infraestructura con GPU para inferencia razonable (al menos una NVIDIA A100 para la versión de 70B).
- Costo de mantenimiento operativo (MLOps).

### 3.2 Frameworks de agentes con herramientas

Estos frameworks no son agentes en sí, sino capas de orquestación que permiten construir agentes complejos sobre los LLMs anteriores, dotándolos de memoria, planificación y acceso controlado a herramientas externas (como la base de datos).

#### 3.2.1 OpenAI Agents SDK

SDK lanzado por OpenAI para construir agentes con herramientas, memoria persistente y manejo nativo de *function calling*.

**Ventajas:**
- Integración inmediata con los modelos GPT.
- Patrones de diseño explícitos para agentes con herramientas.

**Limitaciones:**
- Acoplado al ecosistema OpenAI.
- En 2026 todavía es un SDK reciente; las mejores prácticas no están estabilizadas.

#### 3.2.2 LangChain

Framework de código abierto para construir aplicaciones con LLMs. Provee abstracciones para chains, agents, memoria y herramientas.

**Ventajas:**
- Agnóstico al proveedor del LLM.
- Ecosistema muy amplio de integraciones.

**Limitaciones:**
- Curva de aprendizaje pronunciada.
- Capas de abstracción que pueden complicar el debugging.

#### 3.2.3 LlamaIndex

Framework orientado a aplicaciones de *retrieval-augmented generation* (RAG) y bases de conocimiento.

**Ventajas:**
- Excelente para casos donde el agente debe consultar documentos académicos.

**Limitaciones:**
- Su valor principal está en RAG; para Lairn, donde la generación se basa en el modelo de conocimiento del estudiante y no en documentos externos, su aporte es marginal.

### 3.3 Modelos de Knowledge Tracing

Esta familia es el corazón pedagógico de Lairn. Los modelos de *Knowledge Tracing* (KT) estiman el dominio que un estudiante tiene sobre cada concepto, a partir de su historial de respuestas. Esa estimación se utiliza para decidir qué pregunta presentar a continuación, qué dificultad asignarle y cuándo dar por dominado un concepto.

#### 3.3.1 Bayesian Knowledge Tracing (BKT)

Modelo clásico introducido por Corbett y Anderson (1995). Modela el dominio de cada concepto como una variable binaria latente (dominado / no dominado) y utiliza cuatro probabilidades por concepto: probabilidad inicial de dominio, probabilidad de aprender (transición de no-dominado a dominado), probabilidad de acertar por suerte y probabilidad de fallar accidentalmente.

**Ventajas:**
- Altamente interpretable: cada parámetro tiene significado pedagógico claro.
- Requiere muy pocos datos para entrenarse.
- Ideal como *baseline* contra el cual comparar modelos más complejos.

**Limitaciones:**
- Asume independencia entre conceptos (no aprovecha relaciones entre ellos).
- Una sola variable binaria por concepto es simplista; ignora niveles intermedios.

#### 3.3.2 Item Response Theory (IRT)

Familia de modelos psicométricos cuya formulación más conocida es el *modelo de Rasch* (Rasch, 1960) y la extensión de dos parámetros (2PL). Modela la probabilidad de que un estudiante con habilidad latente θ acierte una pregunta con dificultad latente β.

**Ventajas:**
- Fundamento estadístico riguroso, ampliamente validado en psicometría educativa.
- Base de los exámenes adaptativos clásicos (CAT).

**Limitaciones:**
- En su forma básica modela una sola habilidad por estudiante (no por concepto).
- Requiere calibración previa de las preguntas, lo cual en Lairn es complicado porque las preguntas se generan dinámicamente.

#### 3.3.3 Deep Knowledge Tracing (DKT)

Modelo introducido por Piech et al. (2015), basado en redes neuronales recurrentes (LSTM). Recibe como entrada la secuencia de interacciones (concepto, acierto/error) y produce como salida la probabilidad de acertar la siguiente pregunta de cada concepto.

**Ventajas:**
- Capta dependencias temporales y entre conceptos automáticamente.
- Mejora significativamente sobre BKT en datasets grandes (AUC ~0.86 vs ~0.67 en ASSISTments 2009 según el paper original).
- Adecuado para el volumen de datos que Lairn espera generar a mediano plazo.

**Limitaciones:**
- Caja negra: difícil interpretar por qué predice lo que predice.
- Requiere volumen considerable de datos para entrenar bien (típicamente >10 000 secuencias).
- Sensible a hiperparámetros.

#### 3.3.4 Self-Attentive Knowledge Tracing (SAKT)

Propuesto por Pandey y Karypis (2019). Reemplaza la LSTM de DKT por un mecanismo de atención (Transformer simplificado). Permite que el modelo atienda selectivamente a interacciones pasadas relevantes para predecir la actual.

**Ventajas:**
- Mejor desempeño que DKT en datasets de gran escala.
- Más fácil de paralelizar en entrenamiento que LSTM.
- Interpretabilidad parcial a través de los pesos de atención.

**Limitaciones:**
- Más complejo de implementar que DKT.
- Requiere aún más datos para evitar sobreajuste.

#### 3.3.5 Attentive Knowledge Tracing (AKT)

Extensión de SAKT propuesta por Ghosh, Heffernan y Lan (2020). Añade *monotonic attention* (que decae con la distancia temporal) y embeddings ricos para preguntas y conceptos.

**Ventajas:**
- Modela explícitamente el olvido (decay con el tiempo).
- Reportes de mejora consistente sobre SAKT en múltiples datasets.

**Limitaciones:**
- Mayor complejidad arquitectónica.
- Requiere metadata rica de preguntas que Lairn aún no captura plenamente.

#### 3.3.6 SAINT (Separated Self-AttentIve Neural Knowledge Tracing)

Propuesto por Choi et al. (2020) en el contexto del dataset EdNet. Utiliza una arquitectura Transformer encoder-decoder separada para preguntas y respuestas.

**Ventajas:**
- Estado del arte en el dataset EdNet al momento de publicación.
- Bien documentado.

**Limitaciones:**
- Es el modelo más exigente computacionalmente de esta familia.
- Diseñado para volúmenes de datos del orden de millones de interacciones.

### 3.4 Sistemas adaptativos comerciales (referentes)

Estos no son agentes que se integren directamente, pero son referentes obligados para entender el estado del arte aplicado.

| Sistema | Característica destacada | Lo que aporta como referente |
|---|---|---|
| **Knewton** | Pionera en aprendizaje adaptativo institucional | Modelo de grafo de prerrequisitos entre conceptos |
| **Khan Academy** | Sistema de "mastery learning" con visualización por temas | Ejemplo de UX para representar dominio por concepto |
| **Duolingo (Birdbrain)** | Modelo propio basado en IRT extendido | Demuestra que IRT bien aplicado escala a millones de usuarios |
| **ASSISTments** | Plataforma académica con datasets abiertos | Provee los datasets `ASSISTments 2009/2015` para entrenar modelos KT |

---

## 4. Criterios de Comparación

Se definieron siete criterios para evaluar los agentes investigados. Los cuatro primeros responden al pedido explícito del seguimiento del proyecto (precisión, escalabilidad, facilidad de integración y recursos computacionales). Los tres restantes se agregaron por considerarse críticos en el contexto educativo.

| Criterio | Pregunta que responde | Escala |
|---|---|---|
| **Precisión / efectividad** | ¿Qué tan bien cumple su tarea? | Alta / Media / Baja |
| **Escalabilidad** | ¿Soporta crecimiento de usuarios y datos? | Alta / Media / Baja |
| **Facilidad de integración** | ¿Qué tan rápido se integra con Django + PostgreSQL? | Alta / Media / Baja |
| **Recursos computacionales** | ¿Requiere GPU? ¿Cuánta RAM? | Bajo / Medio / Alto |
| **Costo operativo** | API paga, infraestructura propia, ambos | $ / $$ / $$$ |
| **Interpretabilidad** | ¿Podemos explicar al docente por qué decidió lo que decidió? | Alta / Media / Baja |
| **Madurez del ecosistema** | ¿Existe documentación, comunidad, soporte? | Alta / Media / Baja |

---

## 5. Tabla Comparativa

### 5.1 LLMs generativos

| Modelo | Precisión | Escalabilidad | Integración | Recursos | Costo | Interpretabilidad | Madurez |
|---|---|---|---|---|---|---|---|
| GPT-4o | Alta | Alta | Alta | Bajo (API) | $$ | Baja | Alta |
| Claude 3.5 Sonnet | Alta | Alta | Media | Bajo (API) | $$ | Baja | Media-Alta |
| Gemini 1.5 Pro | Media-Alta | Alta | Media | Bajo (API) | $$ | Baja | Media |
| Llama 3 70B (self-hosted) | Media-Alta | Media | Baja | Alto (GPU) | $ (infra) | Baja | Media |

### 5.2 Modelos de Knowledge Tracing

| Modelo | Precisión | Escalabilidad | Integración | Recursos | Costo | Interpretabilidad | Madurez |
|---|---|---|---|---|---|---|---|
| BKT | Media | Alta | Alta | Bajo (CPU) | $ | **Alta** | Alta |
| IRT | Media-Alta | Alta | Media | Bajo (CPU) | $ | Alta | Alta |
| DKT (LSTM) | Alta | Media | Media | Medio (GPU recomendada) | $ | Baja | Alta |
| SAKT | Alta | Media | Media | Medio (GPU recomendada) | $ | Media | Media |
| AKT | Muy alta | Media | Baja | Alto (GPU) | $ | Media | Media |
| SAINT | Muy alta | Baja | Baja | Muy alto (GPU) | $$ | Baja | Media |

### 5.3 Frameworks de agentes

| Framework | Precisión | Escalabilidad | Integración | Recursos | Costo | Interpretabilidad | Madurez |
|---|---|---|---|---|---|---|---|
| OpenAI Agents SDK | N/A (orquestador) | Alta | Alta (con GPT) | Bajo | $$ (paga GPT) | Media | Media (reciente) |
| LangChain | N/A | Alta | Media | Bajo | $ (open source) | Media | Alta |
| LlamaIndex | N/A | Alta | Media | Bajo | $ | Media | Alta |

---

## 6. Conclusión Preliminar

Tras la revisión, se identifican **dos selecciones de agentes** que conformarían la arquitectura híbrida de Lairn:

### 6.1 Para la familia de IA generativa

Se mantiene la elección actual de **GPT-4o (OpenAI)** como agente generativo principal, por tres razones:

1. Ya está integrado y funcionando en `apps/motor_adaptativo/services/agente_ia.py`.
2. Soporta *structured outputs* nativos, lo cual garantiza la integridad del JSON que el backend espera.
3. La calidad de generación en español académico es la más alta de las opciones evaluadas en pruebas informales realizadas durante el desarrollo del prototipo.

**Como respaldo (fallback)**, se contempla **Claude 3.5 Sonnet** por su política de privacidad más estricta y su ventana de contexto amplia.

Se descarta **Llama 3 self-hosted** en esta fase del proyecto por el costo de infraestructura GPU requerido. Queda como opción de mediano plazo si la dependencia del proveedor externo se vuelve un problema.

### 6.2 Para la familia de Knowledge Tracing

Se propone una **estrategia incremental** con tres modelos:

1. **BKT como baseline obligatorio.** Permite comparar contra un método clásico, interpretable y de bajo costo. Es indispensable para que cualquier mejora reportada por modelos más complejos sea estadísticamente significativa.
2. **DKT (LSTM) como modelo propuesto principal.** Equilibrio adecuado entre potencia, madurez de implementación y exigencia computacional.
3. **SAKT como extensión experimental.** Se implementará si los tiempos del cronograma lo permiten, para evaluar si la arquitectura basada en atención supera a DKT en el dominio específico de Lairn.

Se descartan **AKT y SAINT** en el alcance de este trabajo. Quedan documentados como trabajo futuro, dado que su complejidad e ingesta de datos exceden las posibilidades del proyecto en su fase actual.

### 6.3 Orquestación

Para la orquestación de llamadas al LLM con función específica (generación de preguntas, evaluación, retroalimentación), se evaluará durante el Documento 2 si se justifica adoptar **OpenAI Agents SDK** o si la integración directa actual con `function calling` resulta suficiente. Por simplicidad y por mantener el control explícito del flujo, la inclinación preliminar es **no adoptar un framework de agentes** en esta etapa.

---

## 7. Pendientes y Próximos Pasos

Este documento está al 80 %. Para alcanzar la versión final (100 %) se requiere:

| Pendiente | Documento dependiente | Resultado esperado |
|---|---|---|
| Validación empírica de cada KT sobre datasets públicos (ASSISTments, EdNet) | Documento 2 | Métricas reales de AUC, accuracy y F1 para cada modelo |
| Comparación con simulación de estudiantes sintéticos | Documento 2 | Resultados de eficacia pedagógica simulada |
| Análisis financiero detallado del costo total (API vs self-hosted) | Versión final de este doc | Estimación mensual por escenarios de usuarios |
| Decisión sobre framework de agentes (OpenAI Agents SDK vs llamadas directas) | Documento 2 | Justificación técnica de la decisión |
| Pruebas de carga del agente generativo en condiciones de uso real | Documento 3 | Latencia p50, p95 y p99 por endpoint |
| Validación pedagógica de las preguntas generadas por dos docentes evaluadores | Etapa de evaluación | Coeficiente de acuerdo inter-evaluador |

Una vez completos estos pendientes, este documento pasará a versión 1.0 con la selección definitiva justificada empíricamente.

---

## 8. Dependencias con otros entregables

- **Documento 2 (Entrenamiento de redes neuronales)**: depende de las decisiones tomadas en las secciones 3.3 y 6.2 del presente documento. Los modelos a entrenar son los seleccionados aquí.
- **Documento 3 (Esquema de base de datos)**: debe incluir las tablas necesarias para almacenar las interacciones que alimentarán al agente de KT seleccionado.
- **Documento 4 (Predicción de riesgo académico)**: depende del agente de KT seleccionado, ya que las predicciones de dominio son insumo para el modelo de riesgo.
- **Documento 5 (Personalización del aprendizaje)**: depende del agente recomendador, cuya selección preliminar se difiere a un documento posterior.

---

## 9. Referencias

Anthropic. (2024). *Claude 3.5 Sonnet model card*. Anthropic. https://www.anthropic.com/claude

Chiang, W. L., Zheng, L., Sheng, Y., Angelopoulos, A. N., Li, T., Li, D., Zhang, H., Zhu, B., Jordan, M., Gonzalez, J. E., & Stoica, I. (2024). Chatbot Arena: An open platform for evaluating LLMs by human preference. *arXiv preprint arXiv:2403.04132*.

Choi, Y., Lee, Y., Cho, J., Baek, J., Kim, B., Cha, Y., Shin, D., Bae, C., & Heo, J. (2020). Towards an appropriate query, key, and value computation for knowledge tracing. *Proceedings of the Seventh ACM Conference on Learning @ Scale*, 341-344. https://doi.org/10.1145/3386527.3405945

Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, *4*(4), 253-278. https://doi.org/10.1007/BF01099821

Ghosh, A., Heffernan, N., & Lan, A. S. (2020). Context-aware attentive knowledge tracing. *Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining*, 2330-2339. https://doi.org/10.1145/3394486.3403282

Pandey, S., & Karypis, G. (2019). A self-attentive model for knowledge tracing. *Proceedings of the 12th International Conference on Educational Data Mining*, 384-389.

Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep knowledge tracing. *Advances in Neural Information Processing Systems*, *28*, 505-513.

Rasch, G. (1960). *Probabilistic models for some intelligence and attainment tests*. Danmarks Pædagogiske Institut.

Russell, S., & Norvig, P. (2021). *Artificial intelligence: A modern approach* (4th ed.). Pearson.

VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. *Educational Psychologist*, *46*(4), 197-221. https://doi.org/10.1080/00461520.2011.611369

---

**Control de versiones**

| Versión | Fecha | Cambios |
|---|---|---|
| 0.1 | 2026-05-01 | Estructura inicial y revisión de LLMs |
| 0.5 | 2026-05-10 | Sección de Knowledge Tracing y criterios |
| 0.8 | 2026-05-24 | Tabla comparativa, conclusión preliminar, pendientes |
| 1.0 | Pendiente | Versión final con validación empírica del Documento 2 |
