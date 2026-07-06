# Documento 5 — Personalización del Aprendizaje mediante IA

**Proyecto**: Lairn — Sistema Inteligente de Aprendizaje Adaptativo
**Tipo de documento**: Investigación de referentes
**Versión**: 0.2 (borrador exploratorio inicial)
**Estado de avance reportado**: 20 %
**Fecha de última actualización**: 2026-05-24

> **Nota sobre el estado del documento.** Este es el entregable más exploratorio del proyecto. Su propósito en esta etapa es construir una base sólida de referentes y enfoques teóricos sobre los cuales decidir, en iteraciones posteriores, qué estrategia de personalización implementar en Lairn. El diseño técnico concreto del módulo de recomendación queda explícitamente fuera del alcance de esta versión y depende de la maduración del Documento 4 (Predicción de riesgo).

---

## 1. Introducción

La **personalización del aprendizaje** mediante inteligencia artificial es el componente que distingue a una plataforma educativa moderna de un simple repositorio de contenidos. Su objetivo es ajustar dinámicamente *qué* se le presenta a cada estudiante, *cuándo* y *de qué forma*, en función de su nivel de dominio actual, su ritmo de progreso y sus dificultades específicas (Murray & Pérez, 2015).

En el contexto de Lairn, la personalización opera sobre tres ejes:

1. **Dificultad**: ajustar el nivel de las preguntas que se generan en cada momento.
2. **Contenido**: decidir qué concepto o subconcepto presentar a continuación.
3. **Soporte**: decidir cuándo activar explicaciones guiadas, ejemplos resueltos o retroalimentación expandida.

El primer eje ya está parcialmente implementado en el motor adaptativo actual mediante reglas. Los ejes 2 y 3 son los que motivan este documento.

### 1.1 Objetivos del documento

1. Revisar plataformas educativas reales que implementan personalización con IA, identificando sus enfoques distintivos.
2. Presentar los marcos teóricos pedagógicos y técnicos pertinentes.
3. Extraer lecciones aprendidas aplicables a Lairn.
4. Enumerar las implicaciones de diseño que se derivan de esta investigación.
5. Documentar las dependencias con los demás entregables del proyecto.

### 1.2 Alcance y limitaciones

Como entregable al 20 %, este documento es **estrictamente exploratorio**. No incluye:
- Diseño técnico del módulo de personalización.
- Selección final del algoritmo de recomendación.
- Arquitectura del componente.
- Métricas de evaluación.
- Resultados experimentales.

La investigación se basa en literatura académica peer-reviewed, documentación oficial de las plataformas estudiadas y reportes técnicos publicados por sus equipos de investigación.

---

## 2. Marco Teórico

### 2.1 Aprendizaje adaptativo

El aprendizaje adaptativo es el conjunto de métodos pedagógicos y tecnológicos que adaptan el contenido y la secuencia educativa al perfil individual del estudiante (Brusilovsky & Peylo, 2003). Sus raíces teóricas se encuentran en tres marcos clásicos:

- **Zona de Desarrollo Próximo (ZDP)** de Vygotsky (1978): el aprendizaje óptimo ocurre cuando la tarea está apenas por encima del nivel actual del estudiante.
- **Aprendizaje para el dominio (Mastery Learning)** de Bloom (1968): no avanzar al siguiente concepto hasta dominar el anterior.
- **Teoría de la Carga Cognitiva** de Sweller (1988): no sobrecargar al estudiante con demanda cognitiva más allá de su capacidad de procesamiento.

Estos marcos sugieren tres principios operativos directamente aplicables a Lairn:

| Principio | Implicación para Lairn |
|---|---|
| ZDP | Mantener la dificultad ligeramente superior al dominio actual |
| Mastery learning | No avanzar a un concepto cuyo prerrequisito no está dominado |
| Carga cognitiva | Limitar el número de conceptos nuevos por sesión |

### 2.2 Sistemas de recomendación en educación

Los sistemas de recomendación educativa se diferencian de los recomendadores tradicionales (productos, películas) por dos razones:

1. **El objetivo no es satisfacción inmediata sino aprendizaje a largo plazo.** Un recomendador de Netflix premia el clic; un recomendador educativo debe premiar el dominio.
2. **La secuencia importa.** El orden en que se presentan los contenidos afecta el resultado pedagógico.

Las familias técnicas relevantes son (Su & Khoshgoftaar, 2009; Drachsler et al., 2015):

- **Filtrado colaborativo**: recomienda lo que estudiantes similares encontraron útil.
- **Basado en contenido**: recomienda según similitud entre los atributos del contenido y el perfil del estudiante.
- **Híbrido**: combina ambos enfoques.
- **Basado en grafos de conocimiento**: usa relaciones explícitas de prerrequisitos entre conceptos.
- **Aprendizaje por refuerzo**: modela la decisión como un problema de toma de decisiones secuencial.

### 2.3 Personalización vs adaptación

Conviene distinguir dos términos que suelen usarse como sinónimos pero no lo son:

- **Personalización**: ajuste *explícito* a partir de preferencias declaradas por el estudiante o configuradas por el docente.
- **Adaptación**: ajuste *implícito* derivado del comportamiento observado del estudiante.

Lairn opera principalmente bajo el segundo paradigma. La personalización propiamente dicha (configuración del docente sobre rutas, dificultad inicial, modalidades) se complementa con la adaptación automática del motor.

---

## 3. Casos de Uso Reales

A continuación se revisan siete plataformas que implementan personalización con IA en producción a escala. Para cada una se identifica su enfoque distintivo, su mecanismo técnico documentado y las lecciones aplicables a Lairn.

### 3.1 Duolingo — Birdbrain

**Enfoque**: predecir la probabilidad de que el estudiante recuerde una palabra en un momento dado y programar repaso óptimo basado en repetición espaciada.

**Mecanismo técnico**: el modelo *Half-Life Regression* (HLR), propuesto por Settles y Meeder (2016), estima el "tiempo de vida media" del conocimiento de cada elemento y agenda repasos antes de que el estudiante olvide. Posteriormente Duolingo migró a un modelo más sofisticado llamado *Birdbrain*, basado en Item Response Theory extendida (Duolingo, 2020).

**Lección para Lairn**: la repetición espaciada es un mecanismo de personalización temporal poderoso. Lairn podría incorporar agendamiento de repaso de conceptos débiles después de N días sin práctica.

### 3.2 Khan Academy — Mapa de conocimiento + Khanmigo

**Enfoque**: organizar todo el contenido en un grafo de habilidades con prerrequisitos explícitos, y permitir al estudiante avanzar a su ritmo bajo el paradigma de *mastery learning*. Recientemente se ha incorporado un tutor conversacional impulsado por GPT-4 (Khanmigo).

**Mecanismo técnico**: históricamente usaron Bayesian Knowledge Tracing para estimar dominio por skill, con visualización en el "knowledge map". Khanmigo emplea LLM con *retrieval-augmented generation* sobre el contenido pedagógico estructurado.

**Lección para Lairn**: la visualización del mapa de conocimiento al estudiante es un factor clave de engagement. La incorporación de un tutor conversacional vía LLM es una extensión natural compatible con el agente generativo de Lairn ya en operación.

### 3.3 Knewton (ahora parte de Wiley)

**Enfoque**: plataforma adaptativa de propósito general para educación superior, con énfasis en granularidad fina (cada interacción ajusta el modelo del estudiante).

**Mecanismo técnico**: combinación de Knowledge Tracing extendido, *Item Response Theory* multidimensional y un grafo de prerrequisitos curado manualmente por expertos en cada materia (Knewton, 2017).

**Lección para Lairn**: el grafo de prerrequisitos curado por el docente es un activo de alto valor. Mientras los datos no alcancen para descubrir relaciones entre conceptos automáticamente, la curaduría humana es el mejor proxy.

### 3.4 Carnegie Learning — MATHia

**Enfoque**: tutor cognitivo para matemáticas, basado en la arquitectura cognitiva ACT-R desarrollada en Carnegie Mellon University desde los años 1990.

**Mecanismo técnico**: combina *Model Tracing* (sigue el razonamiento del estudiante paso a paso) y *Knowledge Tracing* (BKT) para decidir cuándo intervenir con pistas, ejemplos o pasos resueltos.

**Lección para Lairn**: la **micro-intervención** (pistas o pasos al detectar atasco) es una forma de personalización subutilizada. Lairn podría agregar pistas adaptativas en preguntas guiadas cuando el estudiante demora más allá de un umbral.

### 3.5 ALEKS — Knowledge Space Theory

**Enfoque**: representar el conocimiento de un dominio como un *espacio de estados de conocimiento*, donde cada estado es el subconjunto de conceptos que el estudiante domina.

**Mecanismo técnico**: basado en *Knowledge Space Theory* (Doignon & Falmagne, 1985; Falmagne et al., 2006). Calcula el estado actual del estudiante mediante una evaluación inicial probabilística y elige el siguiente concepto a aprender según el "borde exterior" del estado actual.

**Lección para Lairn**: el concepto de "borde exterior" (conceptos cuyos prerrequisitos ya están dominados pero el concepto en sí aún no) es una heurística poderosa para recomendación, y puede implementarse incluso sin Knowledge Tracing avanzado si existe un grafo de prerrequisitos.

### 3.6 Coursera

**Enfoque**: recomendación a nivel de curso (no de tema dentro de un curso). Usa filtrado colaborativo y basado en contenido para sugerir cursos completos al estudiante en función de su carrera, intereses y cursos completados.

**Mecanismo técnico**: recomendador híbrido (Coursera, 2019), con énfasis en *learning paths* multi-curso.

**Lección para Lairn**: el caso de Coursera muestra un nivel de granularidad complementario al de Lairn. Si Lairn crece a soportar múltiples cursos por institución, podría incorporar recomendaciones de curso siguiente además de las recomendaciones intra-curso actuales.

### 3.7 Smart Sparrow

**Enfoque**: plataforma de autoría de "courseware adaptativo" donde los docentes definen reglas de adaptación visualmente y la plataforma las ejecuta.

**Mecanismo técnico**: motor de reglas declarativas con condiciones sobre el desempeño y acciones de adaptación (mostrar/ocultar contenido, cambiar de pista, redirigir).

**Lección para Lairn**: la adaptación basada en reglas es complementaria a la basada en ML. Permite al docente capturar conocimiento pedagógico explícito que el modelo no aprende. Lairn ya opera bajo reglas básicas; podría exponerlas como motor configurable por el docente.

### 3.8 Síntesis comparativa

| Plataforma | Enfoque distintivo | Tipo de modelo | Aplicabilidad a Lairn |
|---|---|---|---|
| Duolingo | Repetición espaciada | HLR / IRT extendido | Alta — incorporar repaso temporal |
| Khan Academy | Mapa visual + LLM tutor | BKT + LLM | Alta — visualización + tutor |
| Knewton | Adaptación granular fina | KT + IRT + grafo | Media — grafo curado |
| Carnegie Learning | Tutor cognitivo paso a paso | Model Tracing + BKT | Media — pistas adaptativas |
| ALEKS | Estados de conocimiento | KST | Alta — heurística del borde exterior |
| Coursera | Recomendación a nivel curso | Híbrido (CF + CB) | Baja a corto plazo |
| Smart Sparrow | Reglas declarativas autorables | Motor de reglas | Media — exponer reglas al docente |

---

## 4. Enfoques Técnicos para el Módulo de Recomendación

Esta sección enumera, sin seleccionar aún, las familias técnicas que podrían implementar el componente de personalización en Lairn.

### 4.1 Heurísticas basadas en grafo de prerrequisitos

Recomendar el siguiente concepto buscando aquellos cuyo prerrequisito ya está dominado.

- **Ventajas**: simple, interpretable, no requiere datos.
- **Limitaciones**: requiere que el docente o el sistema definan el grafo.

### 4.2 Filtrado colaborativo

Recomendar lo que estudiantes similares encontraron útil.

- **Ventajas**: explota patrones implícitos del grupo.
- **Limitaciones**: requiere muchos estudiantes para funcionar (problema de *cold start* poblacional).

### 4.3 Basado en contenido

Recomendar conceptos similares a los que el estudiante ha trabajado bien o necesita reforzar.

- **Ventajas**: funciona desde el primer estudiante.
- **Limitaciones**: limitado por la calidad de la representación del contenido.

### 4.4 Bandits contextuales

Tratar la recomendación como un problema de exploración / explotación: cada decisión tiene una recompensa (¿mejoró el dominio?), y el sistema aprende a equilibrar entre lo conocido bueno y lo aún por explorar.

- **Ventajas**: aprende online sin necesidad de un dataset histórico grande.
- **Limitaciones**: complejidad de implementación; difícil de explicar al docente.

### 4.5 Aprendizaje por refuerzo

Modelar la secuencia completa de recomendaciones como un proceso de decisión de Markov (MDP) y aprender una política óptima.

- **Ventajas**: maximiza el resultado a largo plazo, no la siguiente respuesta.
- **Limitaciones**: requiere mucha data, riesgo de inestabilidad. Doroudi, Aleven y Brunskill (2019) revisaron el campo y concluyeron que RL para secuenciación educativa sigue siendo área activa de investigación, con resultados mixtos en aplicaciones reales.

### 4.6 Modelos neuronales secuenciales

Usar redes neuronales (LSTM, Transformers) entrenadas sobre secuencias de interacciones para predecir cuál sería la siguiente actividad óptima (Hidasi et al., 2016).

- **Ventajas**: alta capacidad expresiva.
- **Limitaciones**: requiere grandes volúmenes de datos y compite directamente con los modelos de KT del Documento 2 (la línea entre KT y recomendación se vuelve borrosa).

---

## 5. Lecciones Aprendidas

De la revisión anterior se extraen siete lecciones aplicables a Lairn:

1. **El grafo de prerrequisitos es el activo más valioso a corto plazo.** Tanto Knewton como ALEKS lo demuestran. Lairn debería habilitar al docente para declarar dependencias entre conceptos al crear el curso.
2. **La repetición espaciada es un mecanismo de personalización temporal de alto retorno.** Duolingo lo demuestra a escala. Es relativamente simple de implementar.
3. **La visualización al estudiante de su propio mapa de conocimiento aumenta engagement.** Khan Academy y MATHia lo respaldan.
4. **Las pistas adaptativas y micro-intervenciones son personalización subutilizada.** MATHia demuestra su valor.
5. **No empezar con Reinforcement Learning.** La literatura es entusiasta pero los casos productivos exitosos son escasos. Empezar con heurísticas o bandits.
6. **Combinar reglas explícitas (autoría del docente) con ML (adaptación automática) es lo que mejor funciona en producción.** Smart Sparrow y Knewton lo confirman.
7. **El recomendador debe optimizar dominio a largo plazo, no precisión inmediata.** La métrica de éxito no es "% de aciertos" sino "tiempo hasta dominio" o "retención a 30 días".

---

## 6. Implicaciones para Lairn

A partir de las lecciones, se identifican los siguientes elementos a considerar en el diseño formal posterior:

### 6.1 Pre-requisitos como ciudadano de primera clase

Agregar al modelo `Concepto` (a definirse en versiones futuras del Documento 3) un campo de dependencias explícitas entre conceptos. Esto habilita:

- La heurística del "borde exterior" inspirada en ALEKS.
- Validación de que el docente no asigne preguntas de un concepto cuyo prerrequisito el estudiante no domina.
- Visualización tipo "knowledge map" inspirada en Khan Academy.

### 6.2 Repaso espaciado

Calcular para cada estudiante y cada concepto débil cuándo es el momento óptimo de proponer una pregunta de repaso. La fórmula inicial puede ser simple (intervalos crecientes: 1d, 3d, 7d, 14d) y evolucionar a un modelo HLR si se justifica.

### 6.3 Recomendación adaptativa

El motor de recomendación combinará tres fuentes:

1. **Reglas del docente** (qué objetivos cubrir, qué orden mínimo respetar).
2. **Grafo de prerrequisitos** (qué conceptos son alcanzables dado el estado actual).
3. **Modelo de Knowledge Tracing** (qué concepto necesita más práctica según el dominio estimado).

Y opcionalmente:

4. **Predicción de riesgo** (priorizar refuerzo en estudiantes en riesgo).

### 6.4 Visualización al estudiante

Incorporar (en una fase posterior) una vista de "mi mapa de conocimiento" que muestre los conceptos dominados, en desarrollo y débiles, similar al *knowledge map* de Khan Academy.

### 6.5 Tutor conversacional

A largo plazo, evaluar si el agente generativo actual de Lairn puede expandirse a un rol de tutor conversacional al estilo de Khanmigo. Esto sería una iniciativa derivada, no parte del scope inicial del módulo de personalización.

---

## 7. Pendientes y Próximos Pasos

Este documento está al 20 %. Para alcanzar el 50 % se requiere:

| Pendiente | Resultado esperado |
|---|---|
| Selección preliminar del enfoque técnico principal (heurística vs bandit vs neuronal) | Justificación basada en datos disponibles |
| Definición de la métrica de éxito del recomendador | Métrica medible (por ejemplo, "tiempo hasta dominio" o "conceptos dominados por sesión") |
| Boceto del modelo de datos para representar el grafo de prerrequisitos | DER preliminar |
| Boceto del flujo de decisión del recomendador | Diagrama de actividad |

Para alcanzar el 100 % se requiere adicionalmente:

- Diseño formal del modelo (arquitectura, hiperparámetros si aplica).
- Pipeline de evaluación.
- Resultados experimentales (al menos en simulación con estudiantes sintéticos).
- Validación con docentes evaluadores.

---

## 8. Dependencias con otros entregables

Este documento es **el más dependiente** del proyecto, dado su estado inicial:

- **Documento 1 (Investigación de agentes de IA)**: la elección del enfoque técnico del recomendador será coherente con la familia de modelos seleccionada en aquel documento.
- **Documento 2 (Entrenamiento de redes neuronales)**: el recomendador consumirá las probabilidades de dominio producidas por el modelo de Knowledge Tracing. La calidad del recomendador depende directamente de la calidad del KT.
- **Documento 3 (Esquema de base de datos)**: la implementación de la sección 6.1 (prerrequisitos como ciudadano de primera clase) requiere agregar tablas o campos al esquema.
- **Documento 4 (Predicción de riesgo académico)**: el riesgo identificado en el Documento 4 alimenta al recomendador para priorizar refuerzo en estudiantes vulnerables. El avance de este documento depende de la consolidación del Documento 4.

```
Documento 1 ────────┐
                    ├──► Documento 2 ──┐
Documento 3 ────────┘                  │
                                       ├──► Documento 4 ──► Documento 5
                                       │                   ▲
                                       └───────────────────┘
                                          (KT alimenta directamente)
```

---

## 9. Referencias

Bloom, B. S. (1968). *Learning for mastery*. UCLA Center for the Study of Evaluation of Instructional Programs.

Brusilovsky, P., & Peylo, C. (2003). Adaptive and intelligent web-based educational systems. *International Journal of Artificial Intelligence in Education*, *13*(2-4), 159-172.

Coursera. (2019). *Recommendation systems in Coursera: A technical overview*. Coursera Engineering Blog.

Doignon, J. P., & Falmagne, J. C. (1985). Spaces for the assessment of knowledge. *International Journal of Man-Machine Studies*, *23*(2), 175-196. https://doi.org/10.1016/S0020-7373(85)80031-6

Doroudi, S., Aleven, V., & Brunskill, E. (2019). Where's the reward? A review of reinforcement learning for instructional sequencing. *International Journal of Artificial Intelligence in Education*, *29*(4), 568-620. https://doi.org/10.1007/s40593-019-00187-x

Drachsler, H., Verbert, K., Santos, O. C., & Manouselis, N. (2015). Panorama of recommender systems to support learning. In *Recommender Systems Handbook* (pp. 421-451). Springer. https://doi.org/10.1007/978-1-4899-7637-6_12

Duolingo. (2020). *How Duolingo's Birdbrain models work*. Duolingo Engineering Blog.

Falmagne, J. C., Cosyn, E., Doignon, J. P., & Thiéry, N. (2006). The assessment of knowledge, in theory and in practice. *Formal Concept Analysis*, 61-79. https://doi.org/10.1007/11671404_4

Hidasi, B., Karatzoglou, A., Baltrunas, L., & Tikk, D. (2016). Session-based recommendations with recurrent neural networks. *International Conference on Learning Representations (ICLR)*.

Knewton. (2017). *Knewton adaptive learning: Building the world's most powerful education recommendation engine*. Knewton White Paper.

Murray, M. C., & Pérez, J. (2015). Informing and performing: A study comparing adaptive learning to traditional learning. *Informing Science: The International Journal of an Emerging Transdiscipline*, *18*, 111-125.

Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics*, 1848-1858. https://doi.org/10.18653/v1/P16-1174

Su, X., & Khoshgoftaar, T. M. (2009). A survey of collaborative filtering techniques. *Advances in Artificial Intelligence*, 2009, 1-19. https://doi.org/10.1155/2009/421425

Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science*, *12*(2), 257-285. https://doi.org/10.1207/s15516709cog1202_4

Vygotsky, L. S. (1978). *Mind in society: The development of higher psychological processes*. Harvard University Press.

---

**Control de versiones**

| Versión | Fecha | Cambios |
|---|---|---|
| 0.1 | 2026-05-15 | Estructura inicial y planteamiento del problema |
| 0.2 | 2026-05-24 | Casos de uso, marco teórico, lecciones aprendidas |
| 0.5 | Pendiente | Selección preliminar de enfoque técnico y métrica de éxito |
| 1.0 | Pendiente | Diseño formal del módulo, resultados empíricos |
