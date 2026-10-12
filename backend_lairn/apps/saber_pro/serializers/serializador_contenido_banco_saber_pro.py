"""
Serializers del contenido del banco de Saber Pro (HU-20).

Tres contratos:

- `SerializadorContenidoBanco`: lectura de una pregunta o consigna del banco
  (con área y criterios anidados), la respuesta común de generar, listar,
  editar y aprobar.
- `SerializadorGenerarContenido`: entrada de la generación con IA. Valida que
  los criterios enviados correspondan a la estructura del área del curso
  (competencia/afirmación/evidencia en áreas estructuradas, `parte` en Inglés,
  nada en Comunicación Escrita).
- `SerializadorEditarContenido`: entrada de la edición manual del docente.
  Revalida la forma del contenido (nº de opciones según área/parte, correcta ∈
  opciones, texto base de Lectura Crítica, 8 palabras + 5 descripciones en la
  parte 1 de Inglés y preguntas del bloque con sus opciones en las partes 2 a 7)
  para no dejar ítems imposibles en el banco.
"""

from rest_framework import serializers

from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.evidencia_saber_pro import EvidenciaSaberPro
from apps.saber_pro.serializers.serializador_curso_saber_pro import SerializadorAreaSaberPro
from apps.saber_pro.services.catalogo_saber_pro import (
    ESTRUCTURA_COMPETENCIAS,
    ESTRUCTURA_CONSIGNA,
    ESTRUCTURA_PARTES,
    es_parte_relacion,
    opciones_de_parte,
    parte_exige_espacios,
    parte_usa_texto_comun,
    preguntas_de_parte,
    validar_relacion,
)

AREA_LECTURA_CRITICA = 'Lectura Crítica'


# Referencia mínima (id + nombre) de un criterio anidado en la respuesta.
class SerializadorCompetenciaReferencia(serializers.ModelSerializer):
    class Meta:
        model = CompetenciaSaberPro
        fields = ['id', 'nombre']


class SerializadorAfirmacionReferencia(serializers.ModelSerializer):
    class Meta:
        model = AfirmacionSaberPro
        fields = ['id', 'nombre']


class SerializadorEvidenciaReferencia(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaSaberPro
        fields = ['id', 'nombre']


# Lectura de una pieza del banco: pregunta de selección múltiple o consigna.
class SerializadorContenidoBanco(serializers.ModelSerializer):
    area = SerializadorAreaSaberPro(read_only=True)
    competencia = SerializadorCompetenciaReferencia(read_only=True)
    afirmacion = SerializadorAfirmacionReferencia(read_only=True)
    evidencia = SerializadorEvidenciaReferencia(read_only=True)

    class Meta:
        model = ContenidoBancoSaberPro
        fields = [
            'id',
            'tipo',
            'estado',
            'area',
            'competencia',
            'afirmacion',
            'evidencia',
            'parte',
            'tema',
            'contexto',
            'enunciado',
            'opciones',
            'respuesta_correcta',
            'relaciones',
            'preguntas',
            'creado_en',
            'actualizado_en',
            'aprobado_en',
        ]


# Entrada de la generación de contenido con IA (HU-20.1/20.2).
class SerializadorGenerarContenido(serializers.Serializer):
    competencia_id = serializers.IntegerField(required=False, allow_null=True)
    afirmacion_id = serializers.IntegerField(required=False, allow_null=True)
    evidencia_id = serializers.IntegerField(required=False, allow_null=True)
    parte = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=7)
    cantidad = serializers.IntegerField(required=False, min_value=1, max_value=5, default=3)

    def validate(self, attrs):
        """Valida los criterios contra la estructura del área (contexto de la vista).

        Deja en `validated_data` las instancias resueltas (`competencia`,
        `afirmacion`, `evidencia`) para que la vista las use al persistir, y
        `parte` cuando aplique. La evidencia es opcional: el docente puede
        generar el contenido solo con competencia y afirmación.
        """
        area = self.context['area']
        estructura = self.context['estructura']

        competencia_id = attrs.get('competencia_id')
        afirmacion_id = attrs.get('afirmacion_id')
        evidencia_id = attrs.get('evidencia_id')
        parte = attrs.get('parte')

        if estructura == ESTRUCTURA_COMPETENCIAS:
            if parte is not None:
                raise serializers.ValidationError({'parte': 'Esta área no usa partes; la parte solo aplica a Inglés.'})
            self._validar_competencia_y_afirmacion(attrs, area)
            self._validar_evidencia(attrs)
            return attrs

        if estructura == ESTRUCTURA_PARTES:
            if any(v is not None for v in (competencia_id, afirmacion_id, evidencia_id)):
                raise serializers.ValidationError({
                    'competencia_id': 'El área de Inglés no usa competencia, afirmación ni evidencia.',
                })
            if parte is None:
                raise serializers.ValidationError({'parte': 'Debes indicar la parte del examen de Inglés (1 a 7).'})
            attrs['competencia'] = None
            attrs['afirmacion'] = None
            attrs['evidencia'] = None
            return attrs

        # Comunicación Escrita: consigna sin criterios ni parte.
        if parte is not None or any(
            attrs.get(clave) not in (None,) for clave in ('competencia_id', 'afirmacion_id', 'evidencia_id')
        ):
            raise serializers.ValidationError({
                'detalle': 'Comunicación Escrita se genera como consigna: no admite criterios ni parte.',
            })
        attrs['competencia'] = None
        attrs['afirmacion'] = None
        attrs['evidencia'] = None
        return attrs

    def _validar_competencia_y_afirmacion(self, attrs, area):
        """Resuelve y valida competencia y afirmación del área del curso."""
        competencia_id = attrs.get('competencia_id')
        afirmacion_id = attrs.get('afirmacion_id')
        if not competencia_id:
            raise serializers.ValidationError({'competencia_id': 'La competencia es obligatoria para esta área.'})
        if not afirmacion_id:
            raise serializers.ValidationError({'afirmacion_id': 'La afirmación es obligatoria para esta área.'})

        competencia = CompetenciaSaberPro.objects.filter(id=competencia_id, area=area).first()
        if competencia is None:
            raise serializers.ValidationError({'competencia_id': 'La competencia no pertenece al área del curso.'})

        afirmacion = AfirmacionSaberPro.objects.filter(id=afirmacion_id, competencia=competencia).first()
        if afirmacion is None:
            raise serializers.ValidationError({'afirmacion_id': 'La afirmación no pertenece a la competencia indicada.'})

        attrs['competencia'] = competencia
        attrs['afirmacion'] = afirmacion

    def _validar_evidencia(self, attrs):
        """Resuelve y valida la evidencia (opcional) de la afirmación."""
        evidencia_id = attrs.get('evidencia_id')
        if evidencia_id:
            evidencia = EvidenciaSaberPro.objects.filter(id=evidencia_id, afirmacion=attrs['afirmacion']).first()
            if evidencia is None:
                raise serializers.ValidationError({'evidencia_id': 'La evidencia no pertenece a la afirmación indicada.'})
            attrs['evidencia'] = evidencia
        else:
            attrs['evidencia'] = None


# Entrada de la edición manual de una pieza del banco (HU-20.3).
class SerializadorEditarContenido(serializers.Serializer):
    enunciado = serializers.CharField()
    opciones = serializers.ListField(child=serializers.CharField(), required=False)
    respuesta_correcta = serializers.CharField(required=False, allow_blank=True)
    relaciones = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text='Parte 1 de Inglés: 5 objetos {"descripcion", "respuesta"}.',
    )
    contexto = serializers.CharField(required=False, allow_blank=True)
    tema = serializers.CharField(required=False, allow_blank=True)
    preguntas = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text='Partes 2 a 7 de Inglés: objetos {"enunciado", "opciones", "respuesta_correcta"}.',
    )

    def validate(self, attrs):
        """Revalida la forma del contenido antes de guardar la edición."""
        contenido = self.context['contenido']

        if contenido.tipo == 'seleccion_multiple':
            if contenido.parte is not None and not es_parte_relacion(contenido.parte):
                return self._validar_parte_ingles(attrs, contenido)
            if es_parte_relacion(contenido.parte):
                return self._validar_relacion(attrs)
            return self._validar_pregunta(attrs, contenido)
        return self._validar_consigna(attrs)

    def _validar_parte_ingles(self, attrs, contenido):
        """Partes 2 a 7 de Inglés: bloque del examen con su lista de `preguntas`.

        Valida `enunciado` (instrucciones del bloque), el `contexto` (texto base
        obligatorio en las partes 4 a 7, con los espacios `__N__` completos en 4
        y 7) y cada pregunta con su cantidad exacta de opciones y respuesta
        dentro de ellas. Este ítem no es MCQ a nivel de bloque: se descartan
        `opciones`, `respuesta_correcta`, `relaciones` y `tema`.
        """
        enunciado = str(attrs.get('enunciado') or '').strip()
        if not enunciado:
            raise serializers.ValidationError({'enunciado': 'Las instrucciones del bloque son obligatorias.'})

        parte = contenido.parte
        esperadas = preguntas_de_parte(parte)
        preguntas = attrs.get('preguntas')
        if not preguntas:
            raise serializers.ValidationError({'preguntas': f'El bloque debe tener exactamente {esperadas} preguntas.'})
        if len(preguntas) != esperadas:
            raise serializers.ValidationError({'preguntas': f'El bloque debe tener exactamente {esperadas} preguntas.'})

        opciones_esperadas = opciones_de_parte(parte)
        validadas = []
        for indice, pregunta in enumerate(preguntas, start=1):
            try:
                if not isinstance(pregunta, dict):
                    raise ValueError(f'la pregunta {indice} debe ser un objeto JSON')
                enunciado_pregunta = (str(pregunta.get('enunciado') or '').strip()
                                      if pregunta.get('enunciado') is not None else '')
                if not enunciado_pregunta:
                    raise ValueError(f'la pregunta {indice} no tiene enunciado')
                opciones = [str(opcion).strip() for opcion in (pregunta.get('opciones') or [])]
                if len(opciones) != opciones_esperadas or any(not opcion for opcion in opciones):
                    raise ValueError(f'la pregunta {indice} debe tener exactamente {opciones_esperadas} opciones, sin vacíos')
                if len(set(opciones)) != opciones_esperadas:
                    raise ValueError(f'las opciones de la pregunta {indice} deben ser distintas entre sí')
                correcta = (str(pregunta.get('respuesta_correcta') or '').strip()
                            if pregunta.get('respuesta_correcta') is not None else '')
                if not correcta or correcta not in opciones:
                    raise ValueError(f'la respuesta de la pregunta {indice} debe coincidir con una de sus opciones')
            except ValueError as e:
                raise serializers.ValidationError({'preguntas': str(e)})
            validadas.append({
                'enunciado': enunciado_pregunta,
                'opciones': opciones,
                'respuesta_correcta': correcta,
            })

        contexto = str(attrs.get('contexto') or '').strip()
        if parte_usa_texto_comun(parte) and not contexto:
            raise serializers.ValidationError({'contexto': 'El texto base es obligatorio en esta parte de Inglés.'})

        attrs['enunciado'] = enunciado
        attrs['preguntas'] = validadas
        attrs['contexto'] = contexto
        # El bloque de la parte no usa ningún campo de pregunta única.
        attrs.pop('opciones', None)
        attrs.pop('respuesta_correcta', None)
        attrs.pop('relaciones', None)
        attrs.pop('tema', None)
        return attrs

    def _validar_relacion(self, attrs):
        """Parte 1 de Inglés: 8 palabras para 5 descripciones, sin respuesta única."""
        opciones = attrs.get('opciones')
        relaciones = attrs.get('relaciones')
        if not opciones:
            raise serializers.ValidationError({'opciones': 'Debes enviar exactamente 8 palabras.'})
        if not relaciones:
            raise serializers.ValidationError({'relaciones': 'Debes enviar exactamente 5 descripciones con su palabra.'})
        try:
            opciones, relaciones = validar_relacion(opciones, relaciones)
        except ValueError as e:
            raise serializers.ValidationError({'detalle': str(e)})

        attrs['opciones'] = opciones
        attrs['relaciones'] = relaciones
        # Este ítem no es de opción múltiple: nunca guarda respuesta única.
        attrs['respuesta_correcta'] = ''
        attrs['contexto'] = str(attrs.get('contexto') or '').strip()
        attrs.pop('tema', None)
        return attrs

    def _validar_pregunta(self, attrs, contenido):
        opciones = attrs.get('opciones')
        esperadas = opciones_de_parte(contenido.parte) if contenido.parte else 4
        if not opciones:
            raise serializers.ValidationError({'opciones': f'Debes enviar exactamente {esperadas} opciones.'})
        opciones = [str(o).strip() for o in opciones]
        if len(opciones) != esperadas:
            raise serializers.ValidationError({'opciones': f'Debes enviar exactamente {esperadas} opciones.'})
        if any(not o for o in opciones):
            raise serializers.ValidationError({'opciones': 'Ninguna opción puede quedar vacía.'})
        if len(set(opciones)) != esperadas:
            raise serializers.ValidationError({'opciones': 'Las opciones deben ser distintas entre sí.'})

        correcta = (attrs.get('respuesta_correcta') or '').strip()
        if not correcta:
            raise serializers.ValidationError({'respuesta_correcta': 'La respuesta correcta es obligatoria.'})
        if correcta not in opciones:
            raise serializers.ValidationError({'respuesta_correcta': 'Debe coincidir con una de las opciones.'})

        contexto = str(attrs.get('contexto') or '').strip()
        if contenido.area.nombre == AREA_LECTURA_CRITICA and not contexto:
            raise serializers.ValidationError({'contexto': 'El texto base es obligatorio en Lectura Crítica.'})

        attrs['opciones'] = opciones
        attrs['respuesta_correcta'] = correcta
        attrs['contexto'] = contexto
        # La pregunta de selección múltiple no usa tema ni relaciones: se descartan si vienen.
        attrs.pop('tema', None)
        attrs.pop('relaciones', None)
        return attrs

    def _validar_consigna(self, attrs):
        if 'opciones' in attrs or 'respuesta_correcta' in attrs or 'relaciones' in attrs:
            raise serializers.ValidationError({
                'detalle': 'Una consigna de escritura no lleva opciones, respuesta correcta ni relaciones.',
            })
        if not str(attrs.get('enunciado') or '').strip():
            raise serializers.ValidationError({'enunciado': 'La consigna no puede quedar vacía.'})
        if not str(attrs.get('tema') or '').strip():
            raise serializers.ValidationError({'tema': 'El tema es obligatorio en una consigna.'})
        if not str(attrs.get('contexto') or '').strip():
            raise serializers.ValidationError({'contexto': 'El contexto es obligatorio en una consigna.'})
        return attrs