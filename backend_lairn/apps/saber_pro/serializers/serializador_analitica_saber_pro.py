"""
Serializadores de la analítica de resultados Saber Pro (HU-24).

Dan forma a los contratos de dos vistas:

- `SerializadorAnaliticaCurso` (docente): resumen, distribución, resultados
  individuales y desgloses del curso. Los nombres de estudiantes solo se
  exponen al docente propietario del curso (HU-24.1).
- `SerializadorAnaliticaInstitucional` (coordinación/vicerrectoría): indicadores
  consolidados, desgloses y comparativas por curso, carrera y periodo. No
  incluye resultados individuales (HU-24.3/24.4).

`SerializadorCatalogoInstitucional` alimenta los filtros de la vista
institucional con las áreas, carreras y cursos existentes.
"""

from rest_framework import serializers

from apps.saber_pro.serializers.serializador_comparacion_saber_pro import (
    SerializadorCursoComparacion,
    SerializadorEstudianteRanking,
    SerializadorSimulacroFiltro,
)
from apps.saber_pro.serializers.serializador_curso_saber_pro import (
    SerializadorAreaSaberPro,
)


class SerializadorReferenciaAnalitica(serializers.Serializer):
    """Referencia mínima a un criterio académico (competencia o afirmación)."""

    id = serializers.IntegerField()
    nombre = serializers.CharField(allow_blank=True)


class SerializadorProgramaReferencia(serializers.Serializer):
    """Referencia mínima al programa académico (carrera)."""

    id = serializers.IntegerField()
    nombre = serializers.CharField(allow_blank=True)


class SerializadorParteReferencia(serializers.Serializer):
    """Referencia a una parte del examen de Inglés (1 a 7)."""

    numero = serializers.IntegerField()
    nombre = serializers.CharField(allow_blank=True)


class SerializadorFiltroAnalitica(serializers.Serializer):
    """Filtros efectivamente aplicados a la consulta."""

    curso = SerializadorCursoComparacion(allow_null=True, required=False)
    programa = SerializadorProgramaReferencia(allow_null=True, required=False)
    area = SerializadorAreaSaberPro(allow_null=True, required=False)
    competencia = SerializadorReferenciaAnalitica(allow_null=True, required=False)
    afirmacion = SerializadorReferenciaAnalitica(allow_null=True, required=False)
    parte = SerializadorParteReferencia(allow_null=True, required=False)
    simulacro = SerializadorSimulacroFiltro(allow_null=True, required=False)
    periodo = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class SerializadorResumenAnalitica(serializers.Serializer):
    """Indicadores generales del conjunto consultado (HU-24.1.3/24.3.2)."""

    total_estudiantes = serializers.IntegerField()
    total_intentos = serializers.IntegerField()
    total_cursos = serializers.IntegerField()
    total_programas = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()
    promedio_puntaje = serializers.FloatField()
    promedio_calificacion = serializers.FloatField()
    aprobados = serializers.IntegerField()
    tasa_aprobacion = serializers.FloatField()


class SerializadorDistribucionCalificacion(serializers.Serializer):
    """Una franja de la distribución de calificaciones."""

    rango = serializers.CharField()
    cantidad = serializers.IntegerField()
    porcentaje = serializers.FloatField()


class SerializadorResultadoIndividualAnalitica(serializers.Serializer):
    """Resultado de un intento elegible, visible solo para el docente."""

    estudiante = SerializadorEstudianteRanking()
    curso = SerializadorCursoComparacion()
    simulacro = SerializadorSimulacroFiltro(allow_null=True)
    intento = serializers.IntegerField()
    puntaje = serializers.FloatField()
    calificacion = serializers.FloatField()
    correctas = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    total_evaluables = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()
    aprobado = serializers.BooleanField()
    anulada = serializers.BooleanField()
    finalizada_en = serializers.DateTimeField(allow_null=True)


class SerializadorDesgloseArea(serializers.Serializer):
    """Desempeño agregado de un área."""

    area = SerializadorAreaSaberPro()
    total_estudiantes = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()


class SerializadorDesgloseCompetencia(serializers.Serializer):
    """Desempeño agregado de una competencia de un área estructurada."""

    competencia = SerializadorReferenciaAnalitica()
    area = SerializadorAreaSaberPro()
    total_estudiantes = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()


class SerializadorDesgloseAfirmacion(serializers.Serializer):
    """Desempeño agregado de una afirmación y su competencia."""

    afirmacion = SerializadorReferenciaAnalitica()
    competencia = SerializadorReferenciaAnalitica()
    area = SerializadorAreaSaberPro()
    total_estudiantes = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()


class SerializadorDesgloseParte(serializers.Serializer):
    """Desempeño agregado de una parte del examen de Inglés."""

    parte = SerializadorParteReferencia()
    total_estudiantes = serializers.IntegerField()
    aciertos = serializers.IntegerField()
    total_preguntas = serializers.IntegerField()
    porcentaje_acierto = serializers.FloatField()


class SerializadorFocoBajo(serializers.Serializer):
    """Criterio con menor porcentaje de acierto (HU-24.2.5)."""

    tipo = serializers.ChoiceField(choices=['area', 'competencia', 'afirmacion', 'parte'])
    id = serializers.IntegerField()
    nombre = serializers.CharField(allow_blank=True)
    porcentaje_acierto = serializers.FloatField()
    total_preguntas = serializers.IntegerField()


class SerializadorAnaliticaCurso(serializers.Serializer):
    """Respuesta de la analítica de un curso para el docente."""

    curso = SerializadorCursoComparacion()
    filtro = SerializadorFiltroAnalitica()
    periodos_disponibles = serializers.ListField(child=serializers.CharField())
    partes_disponibles = SerializadorParteReferencia(many=True)
    resumen = SerializadorResumenAnalitica()
    distribucion_calificaciones = SerializadorDistribucionCalificacion(many=True)
    resultados_individuales = SerializadorResultadoIndividualAnalitica(many=True)
    por_area = SerializadorDesgloseArea(many=True)
    por_competencia = SerializadorDesgloseCompetencia(many=True)
    por_afirmacion = SerializadorDesgloseAfirmacion(many=True)
    por_parte = SerializadorDesgloseParte(many=True)
    focos_bajos = SerializadorFocoBajo(many=True)


class SerializadorMetricasGrupo(serializers.Serializer):
    """Métricas compartidas por las comparativas institucionales."""

    total_estudiantes = serializers.IntegerField()
    total_intentos = serializers.IntegerField()
    promedio_puntaje = serializers.FloatField()
    promedio_calificacion = serializers.FloatField()
    porcentaje_acierto = serializers.FloatField()
    aprobados = serializers.IntegerField()
    tasa_aprobacion = serializers.FloatField()


class SerializadorCursoInstitucional(SerializadorMetricasGrupo):
    """Comparativa de un curso dentro de la institución."""

    curso = SerializadorCursoComparacion()


class SerializadorProgramaInstitucional(SerializadorMetricasGrupo):
    """Comparativa de una carrera dentro de la institución."""

    programa = SerializadorProgramaReferencia()


class SerializadorPeriodoInstitucional(SerializadorMetricasGrupo):
    """Evolución de los indicadores en un periodo académico."""

    periodo = serializers.CharField()


class SerializadorAnaliticaInstitucional(serializers.Serializer):
    """Respuesta de la analítica consolidada de la institución."""

    filtro = SerializadorFiltroAnalitica()
    periodos_disponibles = serializers.ListField(child=serializers.CharField())
    partes_disponibles = SerializadorParteReferencia(many=True)
    resumen = SerializadorResumenAnalitica()
    distribucion_calificaciones = SerializadorDistribucionCalificacion(many=True)
    por_area = SerializadorDesgloseArea(many=True)
    por_competencia = SerializadorDesgloseCompetencia(many=True)
    por_afirmacion = SerializadorDesgloseAfirmacion(many=True)
    por_parte = SerializadorDesgloseParte(many=True)
    por_curso = SerializadorCursoInstitucional(many=True)
    por_programa = SerializadorProgramaInstitucional(many=True)
    por_periodo = SerializadorPeriodoInstitucional(many=True)
    focos_bajos = SerializadorFocoBajo(many=True)


class SerializadorCursoCatalogo(serializers.Serializer):
    """Curso disponible para filtrar la analítica institucional."""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    area = SerializadorAreaSaberPro()


class SerializadorCatalogoInstitucional(serializers.Serializer):
    """Catálogo de filtros de la vista institucional (áreas, carreras, cursos)."""

    areas = SerializadorAreaSaberPro(many=True)
    programas = SerializadorProgramaReferencia(many=True)
    cursos = SerializadorCursoCatalogo(many=True)
