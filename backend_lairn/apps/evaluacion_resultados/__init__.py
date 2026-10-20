"""
Paquete de la app `evaluacion_resultados`.

Módulo 1 (Configuración e Información Académica) + base del Módulo 2
(Evaluación de RAs) bajo Diseño Centrado en Evidencias (DCE - Icfes 2018):

  Dominio -> Programa / Asignatura
  Afirmación -> Competencia / Resultado de Aprendizaje
  Evidencia -> conducta observable + rúbrica que soporta la afirmación
  Tarea -> Pregunta / Laboratorio / Examen que pide la evidencia

Triple vía de carga para TODO (sin romper lo existente):
  1. manual (formulario UI),
  2. documento + IA (pensum / resolución / plan de aula PDF, nunca se persiste),
  3. API institucional NOVA (mock hoy, real mañana vía `external_id`).

No modifica tablas de `examenes`, `laboratorios` ni `users`: solo las
referencia con FKs nulables para trazabilidad hacia adelante.
"""
