"""
Catálogo de indicadores con ficha técnica (ADR-015). Único lugar donde se
documenta qué mide cada cifra del reporte, cómo se calcula y con qué límites.

Reglas de gobierno del dato:
  - Todos los indicadores son INSTITUCIONALES PROPIOS de LAIRN. Ninguno es un
    indicador oficial del MEN, SNIES, SPADIES ni del CNA; algunos sirven de
    SOPORTE a la evaluación de resultados de aprendizaje que exige la
    normativa citada en `referente` (verificada el 2026-11-05).
  - Los que dependen de la definición pendiente con Vicerrectoría (ADR-006)
    llevan `provisional=True` y toman sus parámetros de
    `servicio_desempeno_ra.METRICA_PROVISIONAL`.
  - Indicadores oficiales que NO son calculables con los datos actuales se
    declaran en `NO_DISPONIBLES` con el dato que falta (no se aproximan).
  - Nivel: operativo (día a día), estratégico (decisiones directivas) o
    rendicion (información verificable para informes institucionales).
"""

from .servicio_desempeno_ra import METRICA_PROVISIONAL

FUENTE_OBS = ('ev_intentos_evaluacion (enviados, no anulados) × ev_evaluaciones_preguntas × '
              'ev_preguntas_banco → ev_resultados_aprendizaje / ev_competencias')
REF_RA = ('Soporte a la evaluación de RA exigida por el Decreto 1330 de 2019 (MEN, condiciones de calidad) y el '
          'Acuerdo CESU 02 de 2020 (Factor 5: aspectos académicos y resultados de aprendizaje); lineamientos '
          'institucionales: Resolución Uniautónoma 0125 de 2022 (por validar con Vicerrectoría).')
DESAG = 'Institución, programa, semestre, asignatura, RA, evaluación, momento, docente, competencia, fechas'


def _umbral() -> int:
    return METRICA_PROVISIONAL['umbral_logro_porcentaje']


def catalogo() -> list:
    u = _umbral()
    sin_resp = ('las preguntas sin responder cuentan como no acertadas' if METRICA_PROVISIONAL['sin_responder_es_fallo']
                else 'las preguntas sin responder se excluyen')
    niveles = ', '.join(f'{e} ≥ {m}' for _c, e, m in METRICA_PROVISIONAL['niveles'])
    comun_obs = {
        'periodicidad': 'Cada evaluación formal (momento) y a demanda con filtros',
        'desagregacion': DESAG,
        'fuente': FUENTE_OBS,
        'referente': REF_RA,
        'tipo': 'Institucional propio',
    }
    return [
        {
            'id': 'logro_general', 'nombre': '% de logro general', 'nivel': 'estrategico', 'provisional': True,
            'objetivo': 'Medir en qué proporción los estudiantes demuestran los RA evaluados.',
            'definicion': 'Respuestas acertadas sobre preguntas presentadas en evaluaciones formales tipo cuestionario.',
            'formula': 'Σ aciertos / Σ preguntas presentadas × 100',
            'numerador': f'Preguntas acertadas ({sin_resp}).',
            'denominador': 'Preguntas presentadas en intentos enviados y no anulados por fraude.',
            'unidad': 'Porcentaje (%)',
            'interpretacion': f'Mayor es mejor. Se considera logrado desde el {u} %.',
            'limitaciones': 'Ponderado por pregunta, no por estudiante. Excluye tareas. Con n < 30 la cifra es inestable.',
            **comun_obs,
        },
        {
            'id': 'ra_logrados', 'nombre': 'RA logrados', 'nivel': 'estrategico', 'provisional': True,
            'objetivo': 'Saber cuántos resultados de aprendizaje alcanzan el umbral institucional.',
            'definicion': f'RA evaluados cuyo % de logro es ≥ {u} %.',
            'formula': f'Conteo de RA con logro ≥ {u} % / RA con al menos una respuesta',
            'numerador': f'RA con % de logro ≥ {u} %.', 'denominador': 'RA con al menos una pregunta presentada.',
            'unidad': 'Cantidad (x / y)',
            'interpretacion': 'Indica amplitud del logro: muchos RA por debajo del umbral señalan brechas curriculares.',
            'limitaciones': 'El umbral es provisional. Un RA con muy pocas respuestas puede quedar arriba o abajo por azar.',
            **comun_obs,
        },
        {
            'id': 'logro_ra', 'nombre': '% de logro por RA', 'nivel': 'estrategico', 'provisional': True,
            'objetivo': 'Identificar qué resultados de aprendizaje se están logrando y cuáles no.',
            'definicion': 'Logro general calculado solo con las preguntas asociadas a cada RA.',
            'formula': 'Σ aciertos del RA / Σ preguntas presentadas del RA × 100',
            'numerador': 'Aciertos en preguntas del RA.', 'denominador': 'Preguntas del RA presentadas.',
            'unidad': 'Porcentaje (%) con n (respuestas)',
            'interpretacion': 'Comparar contra el umbral y entre RA del mismo programa.',
            'limitaciones': 'Las preguntas de cada evaluación pueden variar en dificultad: comparar RA de evaluaciones distintas con cautela.',
            **comun_obs,
        },
        {
            'id': 'logro_competencia', 'nombre': '% de logro por competencia', 'nivel': 'estrategico', 'provisional': True,
            'objetivo': 'Ver el logro agregado de competencias específicas y transversales.',
            'definicion': 'Logro de las preguntas de los RA que pertenecen a cada competencia.',
            'formula': 'Σ aciertos de los RA de la competencia / Σ preguntas presentadas × 100',
            'numerador': 'Aciertos en preguntas de RA de la competencia.', 'denominador': 'Preguntas presentadas de esos RA.',
            'unidad': 'Porcentaje (%)',
            'interpretacion': 'Brechas grandes entre transversales y específicas orientan el plan de mejora.',
            'limitaciones': 'Una competencia con un solo RA evaluado equivale al logro de ese RA.',
            **comun_obs,
        },
        {
            'id': 'aprobacion', 'nombre': '% de aprobación', 'nivel': 'estrategico', 'provisional': True,
            'objetivo': 'Proporción de resultados (notas 0-5) en niveles aprobatorios.',
            'definicion': 'Notas en nivel Suficiente o superior sobre el total de notas.',
            'formula': 'Notas en niveles aprobados / total de notas × 100',
            'numerador': f'Notas con nivel en {METRICA_PROVISIONAL["niveles_aprobados"]}.',
            'denominador': 'Notas: una por (intento, asignatura) de cuestionarios + entregas de tareas calificadas.',
            'unidad': 'Porcentaje (%)', 'periodicidad': 'Cada evaluación formal',
            'desagregacion': DESAG,
            'fuente': 'Notas recalculadas por asignatura de ev_intentos_evaluacion + ev_entregas_tarea (nota)',
            'interpretacion': f'Niveles provisionales: {niveles}.',
            'limitaciones': 'No es la nota oficial de la asignatura ni el promedio académico del estudiante.',
            'referente': REF_RA, 'tipo': 'Institucional propio',
        },
        {
            'id': 'participacion', 'nombre': '% de participación', 'nivel': 'operativo', 'provisional': False,
            'objetivo': 'Medir qué parte de los convocados presentó la evaluación formal.',
            'definicion': 'Convocatorias (estudiante × evaluación publicada) que terminaron en un intento enviado o una entrega.',
            'formula': 'Presentaron / convocados × 100',
            'numerador': 'Pares estudiante-evaluación con intento enviado (incluye anulados) o entrega.',
            'denominador': 'Inscritos en cursos vinculados a las asignaturas de la evaluación ∪ convocados por cargue.',
            'unidad': 'Porcentaje (%)', 'periodicidad': 'Por evaluación', 'desagregacion': 'Programa, momento, evaluación, curso',
            'fuente': 'inscripciones (examenes), ev_convocados_evaluacion, ev_intentos_evaluacion, ev_entregas_tarea',
            'interpretacion': 'Baja participación reduce la representatividad del logro.',
            'limitaciones': 'Depende de que las asignaturas tengan curso vinculado; sin vínculo no hay convocatoria por curso.',
            'referente': 'Indicador de gestión interna (no corresponde a un indicador del MEN).', 'tipo': 'Institucional propio',
        },
        {
            'id': 'asistencia_sala', 'nombre': 'Presentes en sala', 'nivel': 'operativo', 'provisional': False,
            'objetivo': 'Control de asistencia de las evaluaciones presenciales con supervisor (ADR-009).',
            'definicion': 'Convocados marcados presente o tarde en evaluaciones con supervisor.',
            'formula': 'Presentes + tarde / convocados de evaluaciones con supervisor × 100',
            'numerador': 'Asistencias presente/tarde.', 'denominador': 'Convocados de evaluaciones con supervisor.',
            'unidad': 'Cantidad y %', 'periodicidad': 'Por evaluación', 'desagregacion': 'Evaluación, momento, programa',
            'fuente': 'ev_asistencias_evaluacion', 'interpretacion': 'Solo aplica a evaluaciones con llamado a lista.',
            'limitaciones': 'Las evaluaciones sin supervisor no registran asistencia.',
            'referente': 'Indicador de gestión interna.', 'tipo': 'Institucional propio',
        },
        {
            'id': 'cobertura_ra', 'nombre': 'Cobertura de RA obligatorios', 'nivel': 'rendicion', 'provisional': False,
            'objetivo': 'Verificar que cada RA declarado obligatorio en un momento tenga una evaluación publicada.',
            'definicion': 'RA obligatorios del momento que aparecen en preguntas o tareas de evaluaciones publicadas.',
            'formula': 'RA obligatorios evaluados / RA obligatorios vinculados × 100',
            'numerador': 'RA obligatorios con evaluación publicada.', 'denominador': 'RA obligatorios vinculados al momento.',
            'unidad': 'Cantidad y %', 'periodicidad': 'Por momento', 'desagregacion': 'Momento, programa, semestre de referencia',
            'fuente': 'ev_momentos_resultados (obligatorio), ev_evaluaciones_formales, ev_evaluaciones_preguntas, ev_tareas',
            'interpretacion': 'Evidencia de que lo planeado se evaluó. Útil como soporte de autoevaluación.',
            'limitaciones': 'Mide que se evaluó, no que se logró.',
            'referente': REF_RA, 'tipo': 'Institucional propio',
        },
        {
            'id': 'evaluaciones_estado', 'nombre': 'Evaluaciones formales por estado', 'nivel': 'operativo', 'provisional': False,
            'objetivo': 'Seguimiento de la ejecución del plan de evaluación.',
            'definicion': 'Publicadas, con resultados, pendientes (publicadas sin resultados), abiertas y borradores.',
            'formula': 'Conteos', 'numerador': '—', 'denominador': '—', 'unidad': 'Cantidad',
            'periodicidad': 'Continua', 'desagregacion': 'Programa, momento, fechas',
            'fuente': 'ev_evaluaciones_formales, ev_intentos_evaluacion, ev_entregas_tarea',
            'interpretacion': 'Pendientes altas indican evaluaciones sin presentar o sin calificar.',
            'limitaciones': '—', 'referente': 'Indicador de gestión interna.', 'tipo': 'Institucional propio',
        },
        {
            'id': 'notas', 'nombre': 'Promedio y desviación de notas', 'nivel': 'estrategico', 'provisional': False,
            'objetivo': 'Resumir la distribución de resultados en la escala 0-5 (HU-11).',
            'definicion': 'Media y desviación estándar poblacional de las notas.',
            'formula': 'Media = Σ notas / n; desviación = √(Σ (nota − media)² / n)',
            'numerador': '—', 'denominador': 'n = notas registradas', 'unidad': 'Escala 0-5',
            'periodicidad': 'Por evaluación', 'desagregacion': 'Institución, programa, asignatura',
            'fuente': 'Notas por (intento, asignatura) + entregas de tareas calificadas',
            'interpretacion': 'Desviación alta = resultados heterogéneos.',
            'limitaciones': 'Excluye anulados por fraude. No es el promedio académico oficial.',
            'referente': REF_RA, 'tipo': 'Institucional propio',
        },
        {
            'id': 'alertas', 'nombre': 'Alertas tempranas abiertas', 'nivel': 'operativo', 'provisional': True,
            'objetivo': 'Detectar estudiantes o cursos con desempeño bajo repetido (HU-10).',
            'definicion': 'Alertas abiertas según la regla configurada (actividades bajo un % mínimo).',
            'formula': 'Conteo de alertas en estado abierta', 'numerador': '—', 'denominador': '—', 'unidad': 'Cantidad',
            'periodicidad': 'Al evaluar la regla', 'desagregacion': 'Programa, asignatura',
            'fuente': 'ev_alertas_desempeno, ev_regla_alerta', 'interpretacion': 'Requieren seguimiento del Coordinador.',
            'limitaciones': 'La regla (porcentaje y número de actividades) es configurable y provisional.',
            'referente': 'Indicador de gestión interna (permanencia académica).', 'tipo': 'Institucional propio',
        },
        {
            'id': 'integridad', 'nombre': 'Suspensiones y anulaciones por fraude', 'nivel': 'rendicion', 'provisional': False,
            'objetivo': 'Trazabilidad de la integridad académica en las evaluaciones formales (ADR-010).',
            'definicion': 'Incidentes que suspendieron un intento y decisiones de anulación/reactivación.',
            'formula': 'Conteos', 'numerador': '—', 'denominador': '—', 'unidad': 'Cantidad',
            'periodicidad': 'Continua', 'desagregacion': 'Programa, momento, evaluación',
            'fuente': 'ev_incidentes_intento, ev_resoluciones_integridad, ev_intentos_evaluacion',
            'interpretacion': 'Los anulados se excluyen del logro y de las notas.',
            'limitaciones': 'El navegador no puede impedir cambiar de pestaña; solo lo detecta.',
            'referente': 'Indicador de gestión interna.', 'tipo': 'Institucional propio',
        },
        {
            'id': 'preguntas_error', 'nombre': 'Preguntas con mayor % de error', 'nivel': 'operativo', 'provisional': True,
            'objetivo': 'Señalar preguntas a revisar (redacción, dificultad o enseñanza).',
            'definicion': 'Proporción de respuestas incorrectas por pregunta.',
            'formula': '(presentadas − aciertos) / presentadas × 100',
            'numerador': 'Respuestas incorrectas o sin responder.', 'denominador': 'Veces que se presentó la pregunta.',
            'unidad': 'Porcentaje (%) con n', 'periodicidad': 'Por evaluación', 'desagregacion': DESAG,
            'fuente': FUENTE_OBS, 'interpretacion': 'Con n pequeño, un solo error da 100 %.',
            'limitaciones': 'No distingue causa (pregunta mal formulada vs. contenido no aprendido).',
            'referente': 'Indicador de gestión interna (calidad del banco).', 'tipo': 'Institucional propio',
        },
    ]


# Indicadores de referentes oficiales que NO son calculables con los datos actuales.
NO_DISPONIBLES = [
    {'nombre': 'Matrícula / estudiantes matriculados por periodo', 'referente': 'SNIES (MEN)',
     'falta': 'La plataforma no registra matrícula académica por periodo; solo inscripciones a cursos.'},
    {'nombre': 'Deserción por cohorte y por periodo', 'referente': 'SPADIES (MEN)',
     'falta': 'No hay cohorte de ingreso ni historial de matrícula por periodo (PerfilAcademico vacío).'},
    {'nombre': 'Retención / permanencia', 'referente': 'SPADIES (MEN)',
     'falta': 'Mismo motivo que la deserción.'},
    {'nombre': 'Tasa de graduación', 'referente': 'SNIES / SPADIES (MEN)',
     'falta': 'No se registran grados.'},
    {'nombre': 'Aprobación / reprobación de asignaturas (nota final)', 'referente': 'Registro académico institucional',
     'falta': 'Las notas finales de asignatura viven en el sistema académico (NOVA), no en LAIRN.'},
]


def ficha(indicador_id: str) -> dict | None:
    return next((f for f in catalogo() if f['id'] == indicador_id), None)
