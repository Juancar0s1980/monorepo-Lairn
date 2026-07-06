# Documento 4 — Definición del Modelo de Predicción de Riesgo Académico

**Proyecto**: Lairn — Sistema Inteligente de Aprendizaje Adaptativo
**Tipo de documento**: Investigación exploratoria
**Versión**: 0.3 (borrador inicial)
**Estado de avance reportado**: 30 %
**Fecha de última actualización**: 2026-05-24

> **Nota sobre el estado del documento.** Este documento se encuentra en etapa exploratoria. Su objetivo es construir la fundamentación teórica del módulo de predicción de riesgo académico, identificar las variables relevantes y enumerar los enfoques candidatos. El diseño formal del modelo (arquitectura, hiperparámetros, métricas finales) se desarrollará en una versión posterior, una vez consolidadas las decisiones de los Documentos 1 y 2, y disponibles los campos definidos en el Documento 3.

---

## 1. Introducción

La predicción de riesgo académico es un campo establecido dentro de la *Educational Data Mining* (EDM) y el *Learning Analytics* (LA). Su objetivo es identificar de manera temprana a estudiantes con alta probabilidad de fracaso, abandono o bajo rendimiento, con el fin de habilitar intervenciones pedagógicas oportunas (Romero & Ventura, 2020).

En el contexto de Lairn, el módulo de predicción de riesgo cumplirá dos funciones complementarias:

1. **Alerta temprana al docente**: identificar qué estudiantes del curso muestran señales de riesgo, antes de que el problema se vuelva irreversible.
2. **Insumo para la personalización**: alimentar al motor de recomendación adaptativa (Documento 5) con información sobre qué estudiantes requieren contenidos de refuerzo o cambios en la secuencia.

Este documento no propone aún un modelo concreto. Su alcance es construir la base teórica que justifique la elección y diseño del modelo en una iteración posterior.

### 1.1 Objetivos del documento

1. Revisar el estado del arte en predicción de riesgo académico, con énfasis en enfoques basados en redes neuronales.
2. Identificar las variables predictoras relevantes documentadas en la literatura y disponibles (o capturables) en Lairn.
3. Enumerar los enfoques candidatos para el modelo (tipo de problema, familias de algoritmos).
4. Explicitar las dependencias con los demás entregables del proyecto.

### 1.2 Alcance y limitaciones

A este nivel de avance (30 %), el documento es de naturaleza exploratoria. No incluye:
- Diseño detallado de la arquitectura del modelo.
- Hiperparámetros.
- Resultados experimentales.
- Métricas finales de evaluación.

Estos elementos se incorporarán cuando el avance alcance al menos el 70 %.

---

## 2. Estado del Arte

La predicción de riesgo académico ha evolucionado a través de tres olas metodológicas: estadística clásica, machine learning tradicional y deep learning.

### 2.1 Métodos estadísticos clásicos

Los primeros enfoques se basaron en regresión logística y análisis discriminante. Tinto (1975) propuso uno de los primeros modelos teóricos de abandono estudiantil, sentando las bases conceptuales que aún se usan. Posteriormente, Lykourentzou et al. (2009) aplicaron regresión logística para predecir abandono en cursos en línea, alcanzando precisiones del orden del 75 % en MOOCs tempranos.

**Características**:
- Alta interpretabilidad (cada variable tiene un coeficiente explícito).
- Bajo costo computacional.
- Limitaciones para captar relaciones no lineales y secuenciales.

### 2.2 Machine learning clásico

La segunda ola incorporó algoritmos más sofisticados: árboles de decisión, *Random Forest*, *Support Vector Machines* (SVM) y *Gradient Boosting* (XGBoost, LightGBM).

- Marbouti et al. (2016) compararon múltiples clasificadores para detección temprana en un curso de ingeniería, encontrando que ensambles como Random Forest superaban consistentemente a métodos individuales (F1 ≈ 0.84 al inicio del curso, llegando a 0.90 a mitad del curso).
- Costa et al. (2017) evaluaron técnicas de EDM para predicción de fracaso en cursos de programación, reportando que *Decision Trees* y *SVM* eran las más efectivas con datos tempranos.

**Características**:
- Excelente desempeño con tabulares de tamaño moderado.
- Robustez ante variables heterogéneas.
- Interpretabilidad intermedia (importancia de variables, SHAP values).

### 2.3 Deep learning

La tercera ola, vigente, aplica redes neuronales profundas, especialmente cuando los datos tienen componente secuencial (clickstreams, historiales de interacción).

- Waheed et al. (2020) usaron una red neuronal profunda (MLP) sobre datos de un *Virtual Learning Environment* (VLE), obteniendo AUC ≈ 0.93 y superando a Random Forest y SVM.
- Aljohani et al. (2019) utilizaron LSTM sobre clickstreams para predecir riesgo, demostrando que el componente temporal aportaba mejoras significativas (5-10 puntos de AUC) sobre modelos no secuenciales.
- Hassan et al. (2019) compararon LSTM, MLP y modelos clásicos en distintos puntos del semestre, mostrando que LSTM ganaba ventaja conforme aumentaba la cantidad de datos secuenciales disponibles por estudiante.

**Características**:
- Capta dependencias temporales y no lineales complejas.
- Requiere volúmenes de datos significativos.
- Menor interpretabilidad sin técnicas auxiliares (Attention, SHAP, LIME).

### 2.4 Síntesis del estado del arte

| Generación | Métodos | AUC típico reportado | Volumen de datos | Interpretabilidad |
|---|---|---|---|---|
| Estadísticos | Regresión logística | 0.70-0.80 | Pequeño | Alta |
| ML clásico | Random Forest, XGBoost, SVM | 0.80-0.90 | Moderado | Media |
| Deep learning | MLP, LSTM, Transformers | 0.88-0.95 | Grande | Baja |

**Tendencia**: la literatura reciente (2020-2025) muestra una convergencia hacia arquitecturas híbridas que combinan ML clásico para baseline e interpretabilidad, con redes neuronales secuenciales para capturar dinámica temporal cuando hay suficientes datos.

---

## 3. Variables Predictoras Relevantes

Las variables predictoras del riesgo académico se agrupan en cinco categorías documentadas en la literatura. Para cada una se indica disponibilidad actual en Lairn.

### 3.1 Variables demográficas y de contexto

| Variable | Documentada en | Disponible en Lairn |
|---|---|---|
| Edad | Hu et al. (2014) | Parcial (no se captura aún explícitamente) |
| Nivel educativo previo | Tinto (1975) | No |
| Carrera / programa | Marbouti et al. (2016) | No |
| Trabajo paralelo | Romero & Ventura (2020) | No |

**Observación**: las variables demográficas son útiles pero introducen riesgos éticos (sesgos por edad, género, condición socioeconómica). Se evaluará su inclusión en función del marco ético del proyecto.

### 3.2 Variables académicas históricas

| Variable | Documentada en | Disponible en Lairn |
|---|---|---|
| Notas previas | Marbouti et al. (2016) | Sí, en `Resultado.nota` |
| Promedio acumulado | Hassan et al. (2019) | Calculable desde `Resultado` |
| Número de cursos aprobados | Costa et al. (2017) | Calculable desde `Inscripcion` y `Resultado` |
| Patrón de fracaso histórico | Romero & Ventura (2020) | Calculable |

### 3.3 Variables de desempeño en evaluaciones

| Variable | Documentada en | Disponible en Lairn |
|---|---|---|
| Puntaje en exámenes | Marbouti et al. (2016) | Sí, en `Resultado.puntaje` |
| Número de aciertos | Lykourentzou et al. (2009) | Sí, en `Resultado.correctas` |
| Tiempo de respuesta | Waheed et al. (2020) | Sí, en `RespuestaEstudiante.tiempo_por_pregunta` |
| Dificultad enfrentada | Pandey & Karypis (2019) | Sí, en `RespuestaEstudiante.dificultad` |
| Probabilidad de dominio por concepto | Piech et al. (2015) | Sí, en `ModeloConocimiento.conceptos` |

**Esta categoría es la más rica en Lairn**, dado que el motor adaptativo ya captura información granular por respuesta.

### 3.4 Variables de comportamiento en la plataforma (engagement)

| Variable | Documentada en | Disponible en Lairn |
|---|---|---|
| Frecuencia de acceso | Aljohani et al. (2019) | No capturada explícitamente |
| Tiempo total en plataforma | Waheed et al. (2020) | Derivable parcialmente |
| Número de sesiones iniciadas | Romero & Ventura (2020) | Sí, contando `SesionExamen` |
| Sesiones abandonadas | Lykourentzou et al. (2009) | Sí, vía `SesionExamen.estado` |
| Días desde última interacción | Hassan et al. (2019) | Calculable |
| Cumplimiento de plazos | Marbouti et al. (2016) | No aplica directamente |

**Observación**: parte de esta categoría requiere captura adicional. Los campos faltantes se proponen en el Documento 3.

### 3.5 Variables derivadas del motor adaptativo

Estas son **específicas de Lairn** y constituyen una ventaja competitiva del sistema frente a estudios tradicionales que solo cuentan con clickstreams o notas finales.

| Variable | Disponibilidad | Justificación |
|---|---|---|
| Distribución de conceptos débiles/dominados | Sí (`ModeloConocimiento`) | Permite detectar perfiles cognitivos en riesgo |
| Tendencia de la dificultad a lo largo de la sesión | Calculable | Indicador de adaptación correcta o frustración |
| Tasa de mejora intra-sesión | Calculable | Mide curva de aprendizaje del estudiante |
| Estabilidad del dominio (varianza de niveles) | Calculable | Estudiantes erráticos suelen estar en riesgo |

### 3.6 Tabla resumen de variables candidatas

| Categoría | # Variables | Disponibilidad inmediata en Lairn |
|---|---|---|
| Demográficas | 4 | Baja (1/4) |
| Académicas históricas | 4 | Alta (3/4) |
| Desempeño en evaluaciones | 5 | Total (5/5) |
| Comportamiento (engagement) | 6 | Media (3/6) |
| Derivadas del motor adaptativo | 4 | Total (4/4) |

**Conclusión preliminar**: Lairn ya cuenta con la mayoría de variables ricas de las dos categorías más predictivas (desempeño y derivadas del motor adaptativo). La brecha principal está en variables de engagement, que se cubrirán con los campos a agregar identificados en el Documento 3.

---

## 4. Enfoques Posibles para el Modelo

### 4.1 Tipo de problema

El problema de predicción de riesgo puede formularse de varias maneras, cada una con implicaciones distintas:

| Formulación | Salida | Pros | Contras |
|---|---|---|---|
| **Clasificación binaria** | en_riesgo / no_en_riesgo | Simple, fácil de comunicar al docente | Pierde matiz |
| **Clasificación multi-clase** | alto / medio / bajo riesgo | Más informativa | Requiere definir umbrales pedagógicos |
| **Regresión** | Probabilidad continua [0, 1] | Máxima flexibilidad | Más difícil de interpretar para usuarios finales |
| **Predicción temporal** | Riesgo proyectado a 1, 2, 4 semanas | Permite intervención escalonada | Requiere series temporales largas |

**Inclinación preliminar**: empezar con **clasificación binaria** como baseline, y migrar a **clasificación multi-clase** una vez validado el binario, ya que es lo que aporta más valor pedagógico al docente.

### 4.2 Familias de modelos candidatos

| Familia | Modelo representativo | Adecuación a Lairn | Prioridad |
|---|---|---|---|
| Estadístico | Regresión Logística | Baseline interpretable, indispensable | **Obligatorio** |
| ML clásico | Random Forest | Robusto, buen desempeño esperado | **Obligatorio** |
| ML clásico | XGBoost / LightGBM | Estado del arte tabular | Recomendado |
| Deep learning | MLP (Multi-Layer Perceptron) | Si Random Forest no alcanza | Opcional |
| Deep learning secuencial | LSTM | Si se tiene volumen y secuencias largas | Opcional, a futuro |

### 4.3 Estrategia incremental propuesta

Análoga a la estrategia adoptada en el Documento 2 para Knowledge Tracing:

1. **Baseline obligatorio**: Regresión Logística + Random Forest, con todas las variables disponibles.
2. **Modelo principal**: XGBoost, ajustado con búsqueda de hiperparámetros.
3. **Comparación experimental**: MLP, evaluado contra los anteriores para determinar si la complejidad adicional se justifica.

LSTM y modelos basados en Transformers para riesgo se contemplan como trabajo futuro, condicionados a disponer de un volumen mínimo de datos longitudinales.

### 4.4 Consideraciones de diseño

- **Frecuencia de predicción**: se evaluará si el modelo debe predecir riesgo por sesión, por examen, por semana o por curso.
- **Definición de "en riesgo"**: requiere consenso pedagógico. Posibilidades: nota proyectada < 3.0 (escala 1-5), abandono de más del 50 % de exámenes asignados, dominio promedio < 0.4.
- **Punto temporal de evaluación**: muy temprano (semana 1-2) produce baja precisión; muy tarde no permite intervenir. La literatura sugiere ~25-50 % del curso como ventana óptima (Marbouti et al., 2016).

---

## 5. Métricas de Evaluación Previstas

Aunque la definición final se incorporará en versiones posteriores, las métricas candidatas son:

| Métrica | Justificación |
|---|---|
| AUC-ROC | Métrica estándar para clasificación binaria |
| F1-score | Equilibrio entre precisión y recall, importante por desbalance esperado |
| Recall (sensibilidad) | Crítica: no se quiere perder estudiantes realmente en riesgo |
| Precisión | Importante para no saturar al docente con falsos positivos |
| Matriz de confusión | Visualización para discusión con docentes |
| Curva de calibración | Para evaluar si las probabilidades son confiables |

**Nota**: en riesgo académico, el costo de un falso negativo (no detectar un estudiante en riesgo) suele ser mayor que el de un falso positivo. Esto debe reflejarse en la elección del umbral de decisión.

---

## 6. Pendientes y Próximos Pasos

Este documento está al 30 %. Para alcanzar el 70 % se requiere:

| Pendiente | Resultado esperado |
|---|---|
| Definir formalmente "en riesgo" en consulta con docentes asesores | Definición operativa documentada |
| Identificar dataset público de referencia para pre-validación | OULAD (Kuzilek et al., 2017) es el principal candidato |
| Diseño formal del pipeline de datos (extracción y feature engineering) | Pipeline análogo al del Documento 2 |
| Selección final de modelos a entrenar | Conjunto reducido y justificado |
| Diseño de experimento de evaluación | Protocolo de validación cruzada y métricas |
| Análisis de sesgos potenciales en las variables demográficas | Documento ético derivado |

Para alcanzar el 100 % se requiere adicionalmente:
- Implementación y entrenamiento de los modelos seleccionados.
- Resultados empíricos con métricas reportadas.
- Comparación entre modelos.
- Validación con docentes de la utilidad práctica de las predicciones.

---

## 7. Dependencias con otros entregables

Este documento es uno de los **más dependientes** del proyecto, por estar en etapa inicial:

- **Documento 1 (Investigación de agentes de IA)**: la familia de modelos candidatos a usar aquí (Random Forest, XGBoost, MLP, LSTM) será coherente con las decisiones tecnológicas tomadas en aquel documento.
- **Documento 2 (Entrenamiento de redes neuronales)**: el modelo de riesgo usará como entrada las **probabilidades de dominio conceptual** producidas por el modelo de Knowledge Tracing entrenado en el Documento 2. Esto significa que el avance del Documento 4 está bloqueado parcialmente por el avance del Documento 2.
- **Documento 3 (Esquema de base de datos)**: las variables que se identifican aquí en la sección 3 requieren campos adicionales en la base de datos (por ejemplo, `frecuencia_acceso`, `dias_desde_ultima_interaccion`). Esos campos deben incorporarse en el Documento 3.
- **Documento 5 (Personalización del aprendizaje)**: el módulo de personalización **consume** las predicciones de riesgo producidas aquí. Por tanto, el Documento 5 depende de la maduración de este.

```
Documento 1 ─┐
             ├─► Documento 2 ─┐
Documento 3 ─┘                 ├─► Documento 4 ─► Documento 5
                               │
                  (variables) ─┘
```

---

## 8. Referencias

Aljohani, N. R., Fayoumi, A., & Hassan, S. U. (2019). Predicting at-risk students using clickstream data in the virtual learning environment. *Sustainability*, *11*(24), 7238. https://doi.org/10.3390/su11247238

Costa, E. B., Fonseca, B., Santana, M. A., de Araújo, F. F., & Rego, J. (2017). Evaluating the effectiveness of educational data mining techniques for early prediction of students' academic failure in introductory programming courses. *Computers in Human Behavior*, *73*, 247-256. https://doi.org/10.1016/j.chb.2017.01.047

Hassan, S. U., Waheed, H., Aljohani, N. R., Ali, M., Ventura, S., & Herrera, F. (2019). Virtual learning environment to predict withdrawal by leveraging deep learning. *International Journal of Intelligent Systems*, *34*(8), 1935-1952. https://doi.org/10.1002/int.22129

Hu, Y. H., Lo, C. L., & Shih, S. P. (2014). Developing early warning systems to predict students' online learning performance. *Computers in Human Behavior*, *36*, 469-478. https://doi.org/10.1016/j.chb.2014.04.002

Kuzilek, J., Hlosta, M., & Zdrahal, Z. (2017). Open University Learning Analytics dataset. *Scientific Data*, *4*, 170171. https://doi.org/10.1038/sdata.2017.171

Lykourentzou, I., Giannoukos, I., Nikolopoulos, V., Mpardis, G., & Loumos, V. (2009). Dropout prediction in e-learning courses through the combination of machine learning techniques. *Computers & Education*, *53*(3), 950-965. https://doi.org/10.1016/j.compedu.2009.05.010

Marbouti, F., Diefes-Dux, H. A., & Madhavan, K. (2016). Models for early prediction of at-risk students in a course using standards-based grading. *Computers & Education*, *103*, 1-15. https://doi.org/10.1016/j.compedu.2016.09.005

Pandey, S., & Karypis, G. (2019). A self-attentive model for knowledge tracing. *Proceedings of the 12th International Conference on Educational Data Mining*, 384-389.

Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep knowledge tracing. *Advances in Neural Information Processing Systems*, *28*, 505-513.

Romero, C., & Ventura, S. (2020). Educational data mining and learning analytics: An updated survey. *Wiley Interdisciplinary Reviews: Data Mining and Knowledge Discovery*, *10*(3), e1355. https://doi.org/10.1002/widm.1355

Tinto, V. (1975). Dropout from higher education: A theoretical synthesis of recent research. *Review of Educational Research*, *45*(1), 89-125. https://doi.org/10.3102/00346543045001089

Waheed, H., Hassan, S. U., Aljohani, N. R., Hardman, J., Alelyani, S., & Nawaz, R. (2020). Predicting academic performance of students from VLE big data using deep learning models. *Computers in Human Behavior*, *104*, 106189. https://doi.org/10.1016/j.chb.2019.106189

---

**Control de versiones**

| Versión | Fecha | Cambios |
|---|---|---|
| 0.1 | 2026-05-10 | Estructura inicial y planteamiento del problema |
| 0.3 | 2026-05-24 | Estado del arte, identificación de variables, enfoques candidatos |
| 0.7 | Pendiente | Diseño formal del modelo y pipeline |
| 1.0 | Pendiente | Resultados empíricos y selección final |
