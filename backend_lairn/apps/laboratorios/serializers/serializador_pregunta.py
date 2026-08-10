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
llegar al navegador del estudiante antes de que envíe su solución. Para
`tipo='problema_visual'`, en vez de exponer todas las variantes expone solo
`mi_variante`: la asignada a ESE estudiante (`AsignacionVariante`, sorteada
la primera vez que la pide y fija desde entonces), sin `respuesta_correcta`.

Para `tipo='problema_visual'`, las variantes generadas por IA llegan desde
`VistaSugerirPreguntas` codificadas en base64 (es un borrador que aún no se
guarda en ningún lado — mismo patrón "generar → curar → guardar" de
siempre, solo que acá lo generado incluye imágenes además de texto). Al
aceptar el borrador, el POST normal manda ese mismo base64 en
`variantes_base64` (write-only) y este serializer decodifica cada una a un
`VarianteProblemaVisual` real recién en ese momento, cuando el docente ya
las aprobó. `imagen_referencia` es aparte: una imagen que el docente sube
directamente (sin pasar por IA), también en base64 por simplicidad
(`imagen_referencia_base64`, mismo mecanismo).
"""

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers
from apps.laboratorios.models import Pregunta, CasoTest, VarianteProblemaVisual, AsignacionVariante
from apps.laboratorios.services.agente_pronunciacion import generar_audio_referencia
from .serializador_caso_test import SerializadorCasoTest, SerializadorCasoTestPublico


class SerializadorVarianteProblemaVisualDocente(serializers.ModelSerializer):
    class Meta:
        model = VarianteProblemaVisual
        fields = ['id', 'imagen', 'opciones', 'respuesta_correcta', 'creado_en']
        read_only_fields = fields


class SerializadorVarianteProblemaVisualEstudiante(serializers.ModelSerializer):
    """Igual a la variante del docente pero SIN `respuesta_correcta`."""
    class Meta:
        model = VarianteProblemaVisual
        fields = ['id', 'imagen', 'opciones']
        read_only_fields = fields


def _decodificar_imagen(b64: str, extension: str = 'png'):
    return ContentFile(base64.b64decode(b64), name=f'{uuid.uuid4().hex}.{extension}')


class SerializadorPreguntaDocente(serializers.ModelSerializer):
    casos_test = SerializadorCasoTest(many=True, required=False)
    variantes = SerializadorVarianteProblemaVisualDocente(many=True, read_only=True)
    variantes_base64 = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    imagen_referencia_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Pregunta
        fields = [
            'id', 'tipo', 'enunciado', 'lenguaje', 'codigo_inicial', 'setup_sql',
            'criterios_ia', 'imagen_referencia', 'imagen_referencia_base64',
            'variantes', 'variantes_base64', 'texto_pronunciar', 'audio_referencia',
            'puntos', 'orden', 'creado_en', 'casos_test',
        ]
        read_only_fields = ['id', 'imagen_referencia', 'variantes', 'audio_referencia', 'creado_en']

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
        variantes_data = validated_data.pop('variantes_base64', [])
        imagen_ref_b64 = validated_data.pop('imagen_referencia_base64', None)

        pregunta = Pregunta.objects.create(**validated_data)

        if imagen_ref_b64:
            imagen_ref = _decodificar_imagen(imagen_ref_b64)
            pregunta.imagen_referencia.save(imagen_ref.name, imagen_ref, save=True)

        if pregunta.tipo == 'pronunciacion' and pregunta.texto_pronunciar.strip():
            audio_bytes = generar_audio_referencia(pregunta.texto_pronunciar)
            pregunta.audio_referencia.save(f'{uuid.uuid4().hex}.mp3', ContentFile(audio_bytes), save=True)

        for caso in casos_data:
            CasoTest.objects.create(pregunta=pregunta, **caso)

        for v in variantes_data:
            variante = VarianteProblemaVisual(
                pregunta=pregunta,
                opciones=v['opciones'],
                respuesta_correcta=v['respuesta_correcta'],
            )
            # Las variantes se dibujan por código como SVG (ver agente_problema_visual.py),
            # no son PNG generado por un modelo de imágenes.
            imagen_variante = _decodificar_imagen(v['imagen_base64'], extension='svg')
            variante.imagen.save(imagen_variante.name, imagen_variante, save=True)

        return pregunta

    def update(self, instance, validated_data):
        casos_data = validated_data.pop('casos_test', None)
        # Las variantes solo se crean al aceptar un borrador de IA (creación); no se editan por PATCH.
        validated_data.pop('variantes_base64', None)
        imagen_ref_b64 = validated_data.pop('imagen_referencia_base64', None)
        texto_pronunciar_previo = instance.texto_pronunciar

        for atributo, valor in validated_data.items():
            setattr(instance, atributo, valor)
        if imagen_ref_b64:
            imagen_ref = _decodificar_imagen(imagen_ref_b64)
            instance.imagen_referencia.save(imagen_ref.name, imagen_ref, save=False)
        instance.save()

        if (instance.tipo == 'pronunciacion' and instance.texto_pronunciar.strip()
                and instance.texto_pronunciar != texto_pronunciar_previo):
            audio_bytes = generar_audio_referencia(instance.texto_pronunciar)
            instance.audio_referencia.save(f'{uuid.uuid4().hex}.mp3', ContentFile(audio_bytes), save=True)

        if casos_data is not None:
            instance.casos_test.all().delete()
            for caso in casos_data:
                CasoTest.objects.create(pregunta=instance, **caso)

        return instance


class SerializadorPreguntaEstudiante(serializers.ModelSerializer):
    casos_test = serializers.SerializerMethodField()
    mi_variante = serializers.SerializerMethodField()

    class Meta:
        model = Pregunta
        fields = [
            'id', 'tipo', 'enunciado', 'lenguaje', 'codigo_inicial', 'setup_sql',
            'imagen_referencia', 'mi_variante', 'texto_pronunciar', 'audio_referencia',
            'puntos', 'orden', 'casos_test',
        ]
        read_only_fields = fields

    def get_casos_test(self, pregunta):
        publicos = pregunta.casos_test.filter(es_publico=True)
        return SerializadorCasoTestPublico(publicos, many=True).data

    # Sortea (la primera vez) o recupera la variante ya asignada a este estudiante, sin respuesta_correcta.
    def get_mi_variante(self, pregunta):
        if pregunta.tipo != 'problema_visual':
            return None
        request = self.context.get('request')
        if request is None:
            return None

        asignacion = AsignacionVariante.obtener_o_asignar(pregunta, request.user)
        if asignacion is None:
            return None
        return SerializadorVarianteProblemaVisualEstudiante(asignacion.variante).data
