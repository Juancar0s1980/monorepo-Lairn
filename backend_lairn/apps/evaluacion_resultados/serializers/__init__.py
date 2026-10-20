"""
Serializadores de `evaluacion_resultados`.

Regla de seguridad: los FK de propiedad (`programa`, `momento`, etc.)
se asignan en la vista desde la URL tras validar, nunca desde el payload,
para que nadie cuelgue datos en programas ajenos.
"""

from rest_framework import serializers

from apps.evaluacion_resultados.models import (
    AsignaturaMalla,
    CargueDocumental,
    Competencia,
    MomentoEvaluacion,
    MomentoResultado,
    PerfilAcademico,
    ProgramaAcademico,
    RegistroSincronizacion,
    ResultadoAprendizaje,
    SemestrePrograma,
)


class SerializadorPrograma(serializers.ModelSerializer):
    # Conteo de semestres activos. Se calcula en Python (no con
    # `source='semestres.count'`, que devuelve el método sin llamar y
    # rompe el GET con 500). Así el CRUD de programas nunca falla al listar.
    total_semestres = serializers.SerializerMethodField()

    class Meta:
        model = ProgramaAcademico
        fields = [
            'id', 'codigo', 'nombre', 'modalidad', 'sede',
            'duracion_semestres', 'fecha_vigencia', 'estado',
            'origen', 'external_id', 'estado_revision', 'version',
            'activo', 'total_semestres', 'creado_en',
        ]
        read_only_fields = ['origen', 'external_id', 'version', 'creado_en']

    def get_total_semestres(self, obj) -> int:
        # Usa el prefetch si ya viene cargado; si no, cuenta en BD.
        try:
            semestres = obj.semestres.all()
            # Si está prefetchado, filtrar en memoria evita una query extra.
            return sum(1 for s in semestres if getattr(s, 'activo', True))
        except Exception:
            return obj.semestres.filter(activo=True).count()

    def validate_codigo(self, valor: str) -> str:
        codigo = (valor or '').strip()
        if not codigo:
            raise serializers.ValidationError('El código es obligatorio.')
        qs = ProgramaAcademico.objects.filter(codigo__iexact=codigo)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un programa con ese código.')
        return codigo

    def validate_duracion_semestres(self, valor: int) -> int:
        if valor is None or valor < 1 or valor > 14:
            raise serializers.ValidationError('La duración debe estar entre 1 y 14 semestres.')
        return valor


class SerializadorSemestre(serializers.ModelSerializer):
    class Meta:
        model = SemestrePrograma
        fields = ['id', 'numero', 'nombre', 'origen', 'estado_revision', 'activo', 'creado_en']
        read_only_fields = ['origen', 'creado_en']

    def validate_numero(self, valor: int) -> int:
        if valor is None or valor < 1 or valor > 14:
            raise serializers.ValidationError('El número de semestre debe estar entre 1 y 14.')
        return valor

    def validate(self, datos):
        # Número único por programa (amable antes del error 500 del constraint).
        numero = datos.get('numero', getattr(self.instance, 'numero', None))
        programa = getattr(self.instance, 'programa', None)
        vista = self.context.get('view')
        if vista is not None and programa is None:
            programa_id = vista.kwargs.get('programa_id')
            if programa_id is not None:
                from apps.evaluacion_resultados.models import ProgramaAcademico
                try:
                    programa = ProgramaAcademico.objects.get(pk=programa_id)
                except ProgramaAcademico.DoesNotExist:
                    programa = None
        if programa is not None and numero is not None:
            qs = SemestrePrograma.objects.filter(programa=programa, numero=numero)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'numero': f'Ya existe el semestre {numero} en este programa.'}
                )
        return datos


class SerializadorAsignatura(serializers.ModelSerializer):
    # Nombre legible del semestre para la tabla (evita otro GET en frontend).
    semestre_numero = serializers.IntegerField(source='semestre.numero', read_only=True, allow_null=True)

    class Meta:
        model = AsignaturaMalla
        fields = [
            'id', 'codigo', 'nombre', 'creditos', 'intensidad_horaria',
            'tipo', 'semestre', 'semestre_numero', 'curso_vinculado', 'origen', 'external_id',
            'estado_revision', 'activo', 'creado_en',
        ]
        read_only_fields = ['origen', 'external_id', 'creado_en']

    def validate_codigo(self, valor: str) -> str:
        codigo = (valor or '').strip()
        if not codigo:
            raise serializers.ValidationError('El código es obligatorio.')
        qs = AsignaturaMalla.objects.filter(codigo__iexact=codigo)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe una asignatura con ese código.')
        return codigo

    def validate_creditos(self, valor: int) -> int:
        if valor is None or valor < 0 or valor > 20:
            raise serializers.ValidationError('Los créditos deben estar entre 0 y 20.')
        return valor


class SerializadorCompetencia(serializers.ModelSerializer):
    class Meta:
        model = Competencia
        fields = ['id', 'nombre', 'tipo', 'descripcion', 'origen', 'estado_revision', 'activo', 'creado_en']
        read_only_fields = ['origen', 'creado_en']

    def validate_nombre(self, valor: str) -> str:
        nombre = (valor or '').strip()
        if not nombre:
            raise serializers.ValidationError('El nombre es obligatorio.')
        return nombre


class SerializadorResultado(serializers.ModelSerializer):
    class Meta:
        model = ResultadoAprendizaje
        fields = [
            'id', 'competencia', 'asignatura', 'descripcion',
            'evidencia_observable', 'tarea_sugerida', 'criterios_rubrica',
            'version', 'activo', 'estado_revision', 'origen', 'creado_en',
        ]
        read_only_fields = ['version', 'origen', 'creado_en']

    def validate(self, datos):
        # Coherencia DCE: competencia y asignatura deben ser del mismo programa.
        competencia = datos.get('competencia') or getattr(self.instance, 'competencia', None)
        asignatura = datos.get('asignatura') or getattr(self.instance, 'asignatura', None)
        if competencia is not None and asignatura is not None:
            prog_comp = getattr(competencia, 'programa_id', None)
            prog_asig = getattr(asignatura, 'programa_id', None)
            if prog_comp is not None and prog_asig is not None and prog_comp != prog_asig:
                raise serializers.ValidationError(
                    'La competencia y la asignatura deben pertenecer al mismo programa.'
                )
        return datos

    def validate_criterios_rubrica(self, valor):
        if not valor:
            return valor
        total = sum(int(c.get('peso', 0)) for c in valor)
        if total != 100:
            raise serializers.ValidationError(f'Los pesos deben sumar 100, hoy suman {total}.')
        return valor


class SerializadorMomento(serializers.ModelSerializer):
    # Igual que en programas: SerializerMethodField para no devolver el
    # método `vinculos.count` sin llamar (causaba 500 en el CRUD de momentos).
    total_ras = serializers.SerializerMethodField()

    class Meta:
        model = MomentoEvaluacion
        fields = [
            'id', 'semestre_referencia', 'nombre', 'periodo', 'descripcion',
            'origen', 'estado_revision', 'activo', 'total_ras', 'creado_en',
        ]
        read_only_fields = ['origen', 'creado_en']

    def get_total_ras(self, obj) -> int:
        try:
            vinculos = obj.vinculos.all()
            return vinculos.count() if hasattr(vinculos, 'count') else len(list(vinculos))
        except Exception:
            return 0

    def validate_nombre(self, valor: str) -> str:
        nombre = (valor or '').strip()
        if not nombre:
            raise serializers.ValidationError('El nombre del momento es obligatorio.')
        return nombre

    def validate_semestre_referencia(self, valor: int) -> int:
        if valor is None or valor < 1 or valor > 14:
            raise serializers.ValidationError('El semestre de referencia debe estar entre 1 y 14.')
        return valor


class SerializadorMomentoResultado(serializers.ModelSerializer):
    # Info legible del RA para no hacer join en frontend.
    resultado_descripcion = serializers.CharField(source='resultado.descripcion', read_only=True)

    class Meta:
        model = MomentoResultado
        fields = ['id', 'resultado', 'resultado_descripcion', 'obligatorio', 'creado_en']
        read_only_fields = ['creado_en']

    def validate(self, datos):
        # El vínculo no puede repetirse (mensaje amable antes del 500 del constraint).
        momento = datos.get('momento', getattr(self.instance, 'momento', None))
        resultado = datos.get('resultado', getattr(self.instance, 'resultado', None))
        vista = self.context.get('view')
        if momento is None and vista is not None and hasattr(vista, 'kwargs'):
            momento_id = vista.kwargs.get('momento_id')
            if momento_id is not None:
                from apps.evaluacion_resultados.models import MomentoEvaluacion
                try:
                    momento = MomentoEvaluacion.objects.get(pk=momento_id)
                except MomentoEvaluacion.DoesNotExist:
                    momento = None
        if momento is not None and resultado is not None:
            # Coherencia: el RA debe ser del mismo programa que el momento.
            prog_momento = getattr(momento, 'programa_id', None)
            prog_ra = getattr(getattr(resultado, 'asignatura', None), 'programa_id', None)
            if prog_momento is not None and prog_ra is not None and prog_momento != prog_ra:
                raise serializers.ValidationError(
                    'El resultado debe pertenecer al mismo programa que el momento.'
                )
            qs = MomentoResultado.objects.filter(momento=momento, resultado=resultado)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('Ese resultado ya está vinculado a este momento.')
        return datos


class SerializadorCargue(serializers.ModelSerializer):
    # Nombre del programa destino para mostrar en la revisión sin otro GET.
    programa_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CargueDocumental
        fields = ['id', 'tipo', 'nombre_archivo', 'programa', 'programa_nombre',
                  'estado', 'propuesta_json', 'detalle_error', 'creado_en']
        read_only_fields = ['estado', 'propuesta_json', 'detalle_error', 'creado_en']

    def get_programa_nombre(self, obj) -> str | None:
        return obj.programa.nombre if obj.programa_id and obj.programa else None


class SerializadorRegistroSync(serializers.ModelSerializer):
    class Meta:
        model = RegistroSincronizacion
        fields = '__all__'
        read_only_fields = ['id', 'creado_en']


class SerializadorPerfil(serializers.ModelSerializer):
    class Meta:
        model = PerfilAcademico
        fields = [
            'id', 'usuario', 'numero_documento', 'codigo_matricula',
            'programa', 'semestre_actual', 'cohorte_ingreso', 'estado',
            'external_id', 'creado_en',
        ]
        read_only_fields = ['creado_en']
        extra_kwargs = {'numero_documento': {'write_only': True}}
