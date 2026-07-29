"""
Serializers del recurso `Pregunta`.

`SerializadorPreguntaDocente` acepta `casos_test` anidados en el mismo
POST/PATCH (solo relevantes si `tipo='codigo'`): el docente manda el
conjunto completo de casos en cada edición y este serializer los reemplaza
enteros (borrar + recrear) en vez de hacer diffing por id — más simple y
predecible, y el frontend siempre tiene el conjunto completo en memoria de
todas formas. Valida que `tipo='respuesta_libre'` traiga `criterios_ia` no
vacío (es la rúbrica obligatoria con la que la IA califica, ver
`services/agente_evaluador.py`).

`SerializadorPreguntaEstudiante` filtra los casos ocultos: nunca deben
llegar al navegador del estudiante antes de que envíe su solución.
"""

from rest_framework import serializers
from apps.laboratorios.models import Pregunta, CasoTest
from .serializador_caso_test import SerializadorCasoTest, SerializadorCasoTestPublico


class SerializadorPreguntaDocente(serializers.ModelSerializer):
    casos_test = SerializadorCasoTest(many=True, required=False)

    class Meta:
        model = Pregunta
        fields = [
            'id', 'tipo', 'enunciado', 'lenguaje', 'codigo_inicial', 'setup_sql',
            'criterios_ia', 'puntos', 'orden', 'creado_en', 'casos_test',
        ]
        read_only_fields = ['id', 'creado_en']

    def validate(self, datos):
        tipo = datos.get('tipo', getattr(self.instance, 'tipo', 'codigo'))
        criterios_ia = datos.get('criterios_ia', getattr(self.instance, 'criterios_ia', ''))
        if tipo == 'respuesta_libre' and not str(criterios_ia).strip():
            raise serializers.ValidationError({
                'criterios_ia': 'Obligatorio para preguntas de tipo "Respuesta abierta": es la rúbrica con la que la IA califica.'
            })
        return datos

    def create(self, validated_data):
        casos_data = validated_data.pop('casos_test', [])
        pregunta = Pregunta.objects.create(**validated_data)
        for caso in casos_data:
            CasoTest.objects.create(pregunta=pregunta, **caso)
        return pregunta

    def update(self, instance, validated_data):
        casos_data = validated_data.pop('casos_test', None)
        for atributo, valor in validated_data.items():
            setattr(instance, atributo, valor)
        instance.save()

        if casos_data is not None:
            instance.casos_test.all().delete()
            for caso in casos_data:
                CasoTest.objects.create(pregunta=instance, **caso)

        return instance


class SerializadorPreguntaEstudiante(serializers.ModelSerializer):
    casos_test = serializers.SerializerMethodField()

    class Meta:
        model = Pregunta
        fields = [
            'id', 'tipo', 'enunciado', 'lenguaje', 'codigo_inicial', 'setup_sql',
            'puntos', 'orden', 'casos_test',
        ]
        read_only_fields = fields

    def get_casos_test(self, pregunta):
        publicos = pregunta.casos_test.filter(es_publico=True)
        return SerializadorCasoTestPublico(publicos, many=True).data
