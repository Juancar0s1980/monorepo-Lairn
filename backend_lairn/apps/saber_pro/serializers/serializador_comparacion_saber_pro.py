"""
Serializadores de la comparación de desempeño Saber Pro (HU-23).

Definen dos contratos distintos por rol:

- `SerializadorRankingCurso` (docente): listado nominal y ordenado de su curso,
  con posición, puntaje 0-100, calificación 0.0-5.0 e intentos considerados.
- `SerializadorDesempenoEstudiante` (estudiante): solo agregados propios y del
  grupo. No incluye nombres, correos ni posiciones de otros estudiantes
  (HU-23.4), de modo que el contrato mismo impide filtrar datos de terceros.
"""

from rest_framework import serializers

from apps.saber_pro.serializers.serializador_curso_saber_pro import (
    SerializadorAreaSaberPro,
)


class SerializadorCursoComparacion(serializers.Serializer):
    """Referencia mínima del curso comparado, sin código ni fechas."""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    area = SerializadorAreaSaberPro()


class SerializadorSimulacroFiltro(serializers.Serializer):
    """Simulacro aplicado como filtro (ausente cuando se compara todo el área)."""

    id = serializers.IntegerField()
    titulo = serializers.CharField(allow_blank=True)


class SerializadorFiltroComparacion(serializers.Serializer):
    """Filtro efectivo de la comparación: por simulacro o por área del curso."""

    tipo = serializers.ChoiceField(choices=['simulacro', 'area'])
    simulacro = SerializadorSimulacroFiltro(allow_null=True)


class SerializadorEstudianteRanking(serializers.Serializer):
    """Datos nominales del estudiante visibles solo para el docente del curso."""

    id = serializers.IntegerField()
    nombre_completo = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)


class SerializadorFilaRanking(serializers.Serializer):
    """Una fila del ranking docente."""

    posicion = serializers.IntegerField()
    estudiante = SerializadorEstudianteRanking()
    puntaje = serializers.FloatField()
    calificacion = serializers.FloatField()
    intentos_considerados = serializers.IntegerField()
    simulacros_considerados = serializers.IntegerField()


class SerializadorRankingCurso(serializers.Serializer):
    """Respuesta del ranking nominal del curso para el docente (HU-23.1/23.2)."""

    curso = SerializadorCursoComparacion()
    filtro = SerializadorFiltroComparacion()
    total_estudiantes = serializers.IntegerField()
    total_inscritos = serializers.IntegerField()
    ranking = SerializadorFilaRanking(many=True)


class SerializadorDesempenoEstudiante(serializers.Serializer):
    """Respuesta del desempeño propio del estudiante frente a su curso (HU-23.4)."""

    curso = SerializadorCursoComparacion()
    filtro = SerializadorFiltroComparacion()
    tiene_resultados = serializers.BooleanField()
    hay_comparacion = serializers.BooleanField()
    total_estudiantes = serializers.IntegerField()
    percentil = serializers.IntegerField(allow_null=True)
    mensaje = serializers.CharField()
    mi_puntaje = serializers.FloatField(allow_null=True)
    mi_calificacion = serializers.FloatField(allow_null=True)
    mis_intentos_considerados = serializers.IntegerField()
    mis_simulacros_considerados = serializers.IntegerField()
