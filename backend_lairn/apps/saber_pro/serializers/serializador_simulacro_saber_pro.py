"""
Serializadores del recurso `Simulacro` (HU-19).

- `SerializadorSimulacro`: lectura completa para el docente, con el área
  heredada del curso y las distribuciones configuradas.
- `SerializadorSimulacroEstudiante`: lectura acotada para estudiantes inscritos;
  no expone preguntas, respuestas correctas ni la distribución (HU-19.5).
- `SerializadorCrearEditarSimulacro`: escritura con distribución académica.
  Valida la estructura del área, resuelve competencias/afirmaciones/partes y
  delega la selección aleatoria en `services.simulacros`.
- `SerializadorDisponibilidadSimulacro`: conteo de banco aprobado por criterio.
- `SerializadorPreguntaAsignadaSimulacro`: pregunta aprobada que quedó asignada
  al simulacro, con su orden y el contenido completo (incluida la respuesta
  correcta para la consulta de solo lectura del docente).
"""

from rest_framework import serializers

from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.distribucion_simulacro import DistribucionSimulacro
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.models.simulacro_pregunta import SimulacroPregunta
from apps.saber_pro.serializers.serializador_contenido_banco_saber_pro import (
    SerializadorAfirmacionReferencia,
    SerializadorCompetenciaReferencia,
    SerializadorContenidoBanco,
)
from apps.saber_pro.serializers.serializador_curso_saber_pro import (
    SerializadorAreaSaberPro,
    SerializadorCursoSaberPro,
)
from apps.saber_pro.services.catalogo_saber_pro import (
    AREA_CIUDADANAS,
    AREA_LECTURA_CRITICA,
    AREA_RAZONAMIENTO,
    ESTRUCTURA_COMPETENCIAS,
    ESTRUCTURA_CONSIGNA,
    ESTRUCTURA_PARTES,
    TOTAL_PREGUNTAS_INGLES,
    obtener_estructura_area,
    peso_de_criterio,
)
from apps.saber_pro.services.simulacros import (
    cantidades_automaticas,
    distribuciones_ingles_obligatorias,
    distribuciones_oficiales,
    guardar_distribuciones,
    seleccionar_preguntas,
)
from django.utils import timezone
from rest_framework import serializers


class SerializadorDistribucionSimulacro(serializers.ModelSerializer):
    competencia = SerializadorCompetenciaReferencia(read_only=True)
    afirmacion = SerializadorAfirmacionReferencia(read_only=True)

    class Meta:
        model = DistribucionSimulacro
        fields = ['id', 'competencia', 'afirmacion', 'parte', 'cantidad']
        read_only_fields = fields


class SerializadorSimulacro(serializers.ModelSerializer):
    curso = SerializadorCursoSaberPro(read_only=True)
    area = SerializadorAreaSaberPro(source='curso.area', read_only=True)
    distribuciones = SerializadorDistribucionSimulacro(many=True, read_only=True)
    total_preguntas = serializers.SerializerMethodField()
    tiene_codigo_desbloqueo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Simulacro
        fields = [
            'id',
            'curso',
            'area',
            'titulo',
            'descripcion',
            'num_preguntas',
            'tiempo_limite_minutos',
            'intentos_maximos',
            'fecha_limite',
            'limite_palabras',
            'activo',
            'tiene_codigo_desbloqueo',
            'total_preguntas',
            'distribuciones',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = fields

    def get_total_preguntas(self, simulacro) -> int:
        return simulacro.total_preguntas_asignadas()


class SerializadorPreguntaAsignadaSimulacro(serializers.ModelSerializer):
    contenido = SerializadorContenidoBanco(read_only=True)

    class Meta:
        model = SimulacroPregunta
        fields = ['id', 'orden', 'contenido']
        read_only_fields = fields


class SerializadorPreguntasSimulacro(serializers.Serializer):
    simulacro_id = serializers.IntegerField()
    titulo = serializers.CharField()
    total_preguntas = serializers.IntegerField()
    preguntas = SerializadorPreguntaAsignadaSimulacro(many=True)


class SerializadorCursoResumenSimulacro(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    area = SerializadorAreaSaberPro(read_only=True)


class SerializadorSimulacroEstudiante(serializers.ModelSerializer):
    curso = SerializadorCursoResumenSimulacro(read_only=True)
    area = SerializadorAreaSaberPro(source='curso.area', read_only=True)
    total_preguntas = serializers.SerializerMethodField()
    intentos_realizados = serializers.SerializerMethodField()
    intentos_restantes = serializers.SerializerMethodField()
    intento_en_progreso = serializers.SerializerMethodField()
    puede_presentar = serializers.SerializerMethodField()
    vencido = serializers.SerializerMethodField()

    class Meta:
        model = Simulacro
        fields = [
            'id',
            'curso',
            'area',
            'titulo',
            'descripcion',
            'num_preguntas',
            'tiempo_limite_minutos',
            'total_preguntas',
            'intentos_maximos',
            'intentos_realizados',
            'intentos_restantes',
            'intento_en_progreso',
            'puede_presentar',
            'fecha_limite',
            'limite_palabras',
            'vencido',
            'creado_en',
        ]
        read_only_fields = fields

    def get_total_preguntas(self, simulacro) -> int:
        return simulacro.total_preguntas_asignadas()

    def _presentaciones(self, simulacro):
        """Intentos del estudiante precargados por la vista del listado."""
        return getattr(simulacro, 'presentaciones_estudiante', [])

    def get_intentos_realizados(self, simulacro) -> int:
        return len(self._presentaciones(simulacro))

    def get_intentos_restantes(self, simulacro) -> int:
        return max(0, simulacro.intentos_maximos - self.get_intentos_realizados(simulacro))

    def get_intento_en_progreso(self, simulacro) -> bool:
        return any(
            presentacion.estado == 'en_progreso'
            for presentacion in self._presentaciones(simulacro)
        )

    def get_vencido(self, simulacro) -> bool:
        return simulacro.esta_vencido()

    def get_puede_presentar(self, simulacro) -> bool:
        if simulacro.esta_vencido():
            return False
        return (
            self.get_intento_en_progreso(simulacro)
            or self.get_intentos_realizados(simulacro) < simulacro.intentos_maximos
        )


class SerializadorDistribucionEntrada(serializers.Serializer):
    competencia_id = serializers.IntegerField(required=False, allow_null=True)
    afirmacion_id = serializers.IntegerField(required=False, allow_null=True)
    parte = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=7,
    )
    cantidad = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text=(
            'Si se omite, el sistema reparte las preguntas según los porcentajes '
            'oficiales del área.'
        ),
    )


class SerializadorCrearEditarSimulacro(serializers.Serializer):
    titulo = serializers.CharField(required=False, allow_blank=True, max_length=150)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    num_preguntas = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=200,
        help_text=(
            'En Inglés se fija automáticamente en 45 (las 7 partes completas). '
            'En Comunicación Escrita el valor por defecto es 1 consigna.'
        ),
    )
    tiempo_limite_minutos = serializers.IntegerField(required=False, min_value=1, max_value=600)
    intentos_maximos = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        help_text='Cantidad máxima de intentos por estudiante (1 por defecto).',
    )
    fecha_limite = serializers.DateTimeField(required=False, allow_null=True)
    limite_palabras = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=10000,
        help_text='Máximo de palabras por consigna escrita; vacío significa sin límite.',
    )
    activo = serializers.BooleanField(required=False)
    codigo_desbloqueo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=32,
        trim_whitespace=True,
        help_text=(
            'Codigo que el docente usara para desbloquear un intento cuando el '
            'estudiante salga de la pantalla completa o cambie de pestana.'
        ),
    )
    distribuciones = SerializadorDistribucionEntrada(
        many=True,
        required=False,
        help_text=(
            'Si se omite en un área estructurada, se aplica la estructura oficial '
            'completa con sus porcentajes. En Inglés se ignora: siempre se asignan '
            'las 7 partes.'
        ),
    )

    def validate(self, attrs):
        curso = self.context['curso']
        instancia = self.instance
        estructura = obtener_estructura_area(curso.area)

        codigo = attrs.get('codigo_desbloqueo')
        if codigo is not None:
            codigo = codigo.strip().upper()
            if codigo and (len(codigo) < 6 or not codigo.isalnum()):
                raise serializers.ValidationError({
                    'codigo_desbloqueo': (
                        'El codigo debe tener al menos 6 caracteres y solo puede '
                        'contener letras y numeros.'
                    ),
                })
            attrs['codigo_desbloqueo'] = codigo
        if instancia is None and not codigo:
            raise serializers.ValidationError({
                'codigo_desbloqueo': 'Define un codigo de desbloqueo para el simulacro.',
            })

        if attrs.get('limite_palabras') is not None and estructura != ESTRUCTURA_CONSIGNA:
            raise serializers.ValidationError({
                'limite_palabras': 'Solo aplica al simulacro de Comunicación Escrita.',
            })
        fecha = attrs.get('fecha_limite')
        if fecha is not None and fecha <= timezone.now() and (
            instancia is None or fecha != instancia.fecha_limite
        ):
            raise serializers.ValidationError({
                'fecha_limite': 'La fecha límite debe ser posterior al momento actual.',
            })

        # Comunicación Escrita se evalúa con una consigna abierta en el examen
        # real; si el cliente no envía `num_preguntas`, se usa 1 en lugar del
        # default general de 40. El docente puede cambiarlo explícitamente.
        preguntas_por_defecto = 1 if estructura == ESTRUCTURA_CONSIGNA else 40
        num_preguntas = attrs.get(
            'num_preguntas',
            instancia.num_preguntas if instancia else preguntas_por_defecto,
        )
        if (
            estructura == ESTRUCTURA_CONSIGNA
            and instancia is None
            and 'num_preguntas' not in attrs
        ):
            attrs['num_preguntas'] = preguntas_por_defecto

        if estructura == ESTRUCTURA_PARTES:
            attrs.pop('distribuciones', None)
            attrs['num_preguntas'] = TOTAL_PREGUNTAS_INGLES
            attrs['distribuciones_resueltas'] = distribuciones_ingles_obligatorias()
            return attrs

        if 'distribuciones' not in attrs:
            if instancia:
                if instancia.distribuciones.exists() and 'num_preguntas' in attrs:
                    if num_preguntas != instancia.num_preguntas:
                        raise serializers.ValidationError({
                            'num_preguntas': (
                                'Para cambiar la cantidad de preguntas de un simulacro con '
                                'distribución, envía también la nueva distribución.'
                            ),
                        })
                attrs['distribuciones_resueltas'] = None
                return attrs
            # Al crear sin distribución explícita se aplica la estructura
            # oficial completa del área (competencias o afirmaciones).
            distribuciones_entrada = []
        else:
            distribuciones_entrada = attrs.pop('distribuciones')
        resueltas = self._resolver_distribuciones(
            curso,
            estructura,
            distribuciones_entrada,
            num_preguntas,
        )
        attrs['distribuciones_resueltas'] = resueltas
        return attrs

    def _resolver_distribuciones(self, curso, estructura, distribuciones, num_preguntas):
        if estructura == ESTRUCTURA_CONSIGNA:
            if distribuciones:
                raise serializers.ValidationError({
                    'distribuciones': (
                        'Comunicación Escrita no usa competencias, afirmaciones ni partes: '
                        'el simulacro toma consignas aprobadas del banco del área.'
                    ),
                })
            return []

        if distribuciones:
            if num_preguntas < len(distribuciones):
                raise serializers.ValidationError({
                    'num_preguntas': (
                        f'El simulacro debe tener al menos {len(distribuciones)} preguntas '
                        'para cubrir todos los criterios seleccionados.'
                    ),
                })
            resueltas = []
            claves = set()
            for item in distribuciones:
                resuelta = self._resolver_criterio_competencia(curso, item)
                clave = self._clave_criterio(resuelta)
                if clave in claves:
                    raise serializers.ValidationError({
                        'distribuciones': 'No se puede repetir el mismo criterio en la distribución.',
                    })
                claves.add(clave)
                resueltas.append(resuelta)
            cantidades = [item.get('cantidad') for item in distribuciones]
        else:
            # Sin selección explícita, el simulacro sigue la estructura oficial
            # completa del área (competencias o afirmaciones según corresponda).
            resueltas = distribuciones_oficiales(curso.area)
            if not resueltas:
                raise serializers.ValidationError({
                    'distribuciones': 'El área no tiene criterios oficiales configurados.',
                })
            if num_preguntas < len(resueltas):
                raise serializers.ValidationError({
                    'num_preguntas': (
                        f'El simulacro debe tener al menos {len(resueltas)} preguntas '
                        'para cubrir la estructura oficial del área.'
                    ),
                })
            cantidades = [None] * len(resueltas)

        pesos = [
            distribucion.get('peso') or peso_de_criterio(
                competencia=distribucion.get('competencia'),
                afirmacion=distribucion.get('afirmacion'),
            )
            for distribucion in resueltas
        ]
        automaticas = cantidades_automaticas(num_preguntas, len(resueltas), pesos)

        if any(cantidad is None for cantidad in cantidades):
            for resuelta, cantidad in zip(resueltas, automaticas):
                resuelta['cantidad'] = cantidad
        else:
            total = sum(cantidades)
            if total != num_preguntas:
                raise serializers.ValidationError({
                    'distribuciones': (
                        f'La suma de cantidades ({total}) debe ser igual al número de '
                        f'preguntas del simulacro ({num_preguntas}).'
                    ),
                })
            if list(cantidades) != automaticas:
                esperadas = ', '.join(
                    f'{self._etiqueta_distribucion(resuelta)}: {cantidad}'
                    for resuelta, cantidad in zip(resueltas, automaticas)
                )
                raise serializers.ValidationError({
                    'distribuciones': (
                        'La distribución debe respetar los porcentajes oficiales del área. '
                        f'Con {num_preguntas} preguntas corresponde: {esperadas}.'
                    ),
                })
            for resuelta, cantidad in zip(resueltas, cantidades):
                resuelta['cantidad'] = cantidad

        for resuelta in resueltas:
            if resuelta['cantidad'] < 1:
                raise serializers.ValidationError({
                    'distribuciones': 'Cada criterio debe aportar al menos una pregunta.',
                })
        return resueltas

    def _etiqueta_distribucion(self, distribucion):
        """Nombre legible del criterio para los mensajes de porcentaje oficial."""
        if distribucion.get('afirmacion'):
            return distribucion['afirmacion'].nombre
        if distribucion.get('competencia'):
            return distribucion['competencia'].nombre
        return f'Parte {distribucion.get("parte")}'

    def _resolver_criterio_competencia(self, curso, item):
        if item.get('parte'):
            raise serializers.ValidationError({
                'distribuciones': 'Las áreas estructuradas no usan partes de Inglés.',
            })

        competencia = None
        afirmacion = None

        if item.get('competencia_id'):
            try:
                competencia = CompetenciaSaberPro.objects.get(
                    id=item['competencia_id'],
                    area=curso.area,
                )
            except CompetenciaSaberPro.DoesNotExist:
                raise serializers.ValidationError({
                    'distribuciones': 'La competencia no pertenece al área del curso.',
                })

        if item.get('afirmacion_id'):
            try:
                afirmacion = AfirmacionSaberPro.objects.select_related('competencia').get(
                    id=item['afirmacion_id'],
                    competencia__area=curso.area,
                )
            except AfirmacionSaberPro.DoesNotExist:
                raise serializers.ValidationError({
                    'distribuciones': 'La afirmación no pertenece al área del curso.',
                })
            if competencia and afirmacion.competencia_id != competencia.id:
                raise serializers.ValidationError({
                    'distribuciones': 'La afirmación no pertenece a la competencia indicada.',
                })
            competencia = afirmacion.competencia

        if not competencia:
            raise serializers.ValidationError({
                'distribuciones': 'Selecciona una competencia o una afirmación.',
            })

        area_nombre = curso.area.nombre
        if area_nombre == AREA_LECTURA_CRITICA and afirmacion is None:
            raise serializers.ValidationError({
                'distribuciones': (
                    'Lectura Crítica se distribuye por afirmaciones, no por la '
                    'competencia general.'
                ),
            })
        if area_nombre in (AREA_RAZONAMIENTO, AREA_CIUDADANAS) and afirmacion is not None:
            raise serializers.ValidationError({
                'distribuciones': (
                    'Esta área se distribuye por competencias; selecciona la competencia '
                    'en lugar de una afirmación.'
                ),
            })

        return {
            'competencia': competencia,
            'afirmacion': afirmacion,
            'parte': None,
            'cantidad': item.get('cantidad'),
        }

    def _resolver_criterio_parte(self, item):
        if item.get('competencia_id') or item.get('afirmacion_id'):
            raise serializers.ValidationError({
                'distribuciones': 'Inglés se distribuye por partes, no por competencias.',
            })
        if not item.get('parte'):
            raise serializers.ValidationError({
                'distribuciones': 'Selecciona la parte de Inglés que cubrirá el simulacro.',
            })
        return {
            'competencia': None,
            'afirmacion': None,
            'parte': item['parte'],
            'cantidad': item.get('cantidad'),
        }

    def _clave_criterio(self, distribucion):
        if distribucion.get('afirmacion'):
            return ('afirmacion', distribucion['afirmacion'].id)
        if distribucion.get('competencia'):
            return ('competencia', distribucion['competencia'].id)
        return ('parte', distribucion['parte'])

    def create(self, validated_data):
        distribuciones = validated_data.pop('distribuciones_resueltas', []) or []
        codigo_desbloqueo = validated_data.pop('codigo_desbloqueo', '')
        curso = self.context['curso']
        titulo = (validated_data.pop('titulo', '') or '').strip()
        simulacro = Simulacro.objects.create(
            curso=curso,
            titulo=titulo or f'Simulacro de {curso.area.nombre}',
            descripcion=validated_data.pop('descripcion', ''),
            num_preguntas=validated_data.pop('num_preguntas', 40),
            tiempo_limite_minutos=validated_data.pop('tiempo_limite_minutos', 60),
            intentos_maximos=validated_data.pop('intentos_maximos', 1),
            fecha_limite=validated_data.pop('fecha_limite', None),
            limite_palabras=validated_data.pop('limite_palabras', None),
            activo=validated_data.pop('activo', True),
        )
        if codigo_desbloqueo:
            simulacro.establecer_codigo_desbloqueo(codigo_desbloqueo)
            simulacro.save(update_fields=['codigo_desbloqueo_hash'])
        guardar_distribuciones(simulacro, distribuciones)
        seleccionar_preguntas(simulacro)
        return simulacro

    def update(self, instance, validated_data):
        distribuciones = validated_data.pop('distribuciones_resueltas', None)
        codigo_desbloqueo = validated_data.pop('codigo_desbloqueo', None)
        num_anterior = instance.num_preguntas

        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if codigo_desbloqueo:
            instance.establecer_codigo_desbloqueo(codigo_desbloqueo)
        instance.save()

        cambio_distribucion = False
        if distribuciones is not None:
            cambio_distribucion = not self._misma_distribucion(instance, distribuciones)
            if cambio_distribucion:
                guardar_distribuciones(instance, distribuciones)

        if cambio_distribucion or instance.num_preguntas != num_anterior:
            seleccionar_preguntas(instance)
        return instance

    def _misma_distribucion(self, simulacro, resueltas):
        actuales = {
            (
                distribucion.competencia_id,
                distribucion.afirmacion_id,
                distribucion.parte,
                distribucion.cantidad,
            )
            for distribucion in simulacro.distribuciones.all()
        }
        nuevas = {
            (
                distribucion['competencia'].id if distribucion.get('competencia') else None,
                distribucion['afirmacion'].id if distribucion.get('afirmacion') else None,
                distribucion.get('parte'),
                distribucion['cantidad'],
            )
            for distribucion in resueltas
        }
        return actuales == nuevas


class SerializadorAfirmacionDisponibilidad(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    peso = serializers.IntegerField(
        help_text='Peso porcentual oficial de la afirmación o de su competencia.',
    )
    disponibles = serializers.IntegerField()


class SerializadorCompetenciaDisponibilidad(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    peso = serializers.IntegerField(
        help_text='Peso porcentual oficial de la competencia en el examen.',
    )
    disponibles = serializers.IntegerField()
    afirmaciones = SerializadorAfirmacionDisponibilidad(many=True)


class SerializadorParteDisponibilidad(serializers.Serializer):
    numero = serializers.IntegerField()
    nombre = serializers.CharField()
    peso = serializers.IntegerField()
    preguntas = serializers.IntegerField()
    disponibles = serializers.IntegerField()


class SerializadorDisponibilidadSimulacro(serializers.Serializer):
    area = SerializadorAreaSaberPro(read_only=True)
    tipo_estructura = serializers.ChoiceField(
        choices=[ESTRUCTURA_COMPETENCIAS, ESTRUCTURA_PARTES, ESTRUCTURA_CONSIGNA],
    )
    total_aprobados = serializers.IntegerField()
    competencias = SerializadorCompetenciaDisponibilidad(many=True)
    partes = SerializadorParteDisponibilidad(many=True)
