"""
Serializers del catálogo académico de Saber Pro (HU-20.1).

Expone la jerarquía competencial y las partes de Inglés en el formato que
consume el formulario de generación de contenido del docente:

- `SerializadorCriteriosArea`: respuesta de `GET /docente/areas/<id>/criterios/`,
  que combina el área, la estructura que le corresponde (`competencias`,
  `partes` o `consigna`) y los criterios aplicables. En Comunicación Escrita
  `competencias` y `partes` vienen vacíos: esa área no usa ninguna de las dos
  estructuras.
"""

from rest_framework import serializers

from apps.saber_pro.serializers.serializador_curso_saber_pro import SerializadorAreaSaberPro


# Evidencia del catálogo anidada dentro de una afirmación.
class SerializadorEvidenciaCatalogo(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()


# Afirmación del catálogo anidada dentro de una competencia.
class SerializadorAfirmacionCatalogo(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    evidencias = SerializadorEvidenciaCatalogo(many=True)


# Competencia del catálogo con sus afirmaciones anidadas.
class SerializadorCompetenciaCatalogo(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    afirmaciones = SerializadorAfirmacionCatalogo(many=True)


# Parte del examen de Inglés (1 a 7) con su peso y cantidad de opciones.
class SerializadorParteCatalogo(serializers.Serializer):
    numero = serializers.IntegerField()
    nombre = serializers.CharField()
    peso = serializers.IntegerField(
        help_text='Peso porcentual de la parte en el examen de Inglés.',
    )
    opciones = serializers.IntegerField(
        help_text='Cantidad de opciones de respuesta de esta parte (3, 4 u 8 en la parte 1).',
    )
    descripciones = serializers.IntegerField(
        help_text='Descripciones a relacionar en la parte 1 (5); 0 en las demás partes.',
    )
    descripcion = serializers.CharField()


# Estructura de criterios de un área para el selector del docente (HU-20.1).
class SerializadorCriteriosArea(serializers.Serializer):
    area = SerializadorAreaSaberPro(read_only=True)
    tipo_estructura = serializers.ChoiceField(
        choices=['competencias', 'partes', 'consigna'],
        help_text='Estructura de evaluación del área; define qué criterios mostrar.',
    )
    competencias = SerializadorCompetenciaCatalogo(
        many=True,
        help_text='Jerarquía competencial; vacía en Inglés y Comunicación Escrita.',
    )
    partes = SerializadorParteCatalogo(
        many=True,
        help_text='Partes del examen de Inglés; vacías en las demás áreas.',
    )
