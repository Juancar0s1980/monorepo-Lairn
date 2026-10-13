"""
Admin de Django para `evaluacion_resultados` (solo lectura operativa).

El CRUD real vive en la API con RBAC; el admin es apoyo de soporte.
Nunca muestra `numero_documento` en listados (PII).
"""

from django.contrib import admin

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


@admin.register(ProgramaAcademico)
class AdminPrograma(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'modalidad', 'duracion_semestres', 'estado', 'origen', 'activo')
    search_fields = ('codigo', 'nombre')
    list_filter = ('modalidad', 'estado', 'origen', 'activo')


@admin.register(SemestrePrograma)
class AdminSemestre(admin.ModelAdmin):
    list_display = ('programa', 'numero', 'nombre', 'origen', 'activo')
    list_filter = ('programa',)


@admin.register(AsignaturaMalla)
class AdminAsignatura(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'programa', 'semestre', 'creditos', 'tipo', 'origen', 'activo')
    search_fields = ('codigo', 'nombre')
    list_filter = ('programa', 'tipo', 'origen')


@admin.register(Competencia)
class AdminCompetencia(admin.ModelAdmin):
    list_display = ('nombre', 'programa', 'tipo', 'origen', 'activo')
    list_filter = ('programa', 'tipo')


@admin.register(ResultadoAprendizaje)
class AdminResultado(admin.ModelAdmin):
    list_display = ('id', 'descripcion_corta', 'competencia', 'asignatura', 'version', 'activo')
    list_filter = ('activo',)

    def descripcion_corta(self, obj):
        return obj.descripcion[:60]


@admin.register(MomentoEvaluacion)
class AdminMomento(admin.ModelAdmin):
    list_display = ('nombre', 'programa', 'semestre_referencia', 'periodo', 'activo')
    list_filter = ('programa',)


admin.site.register(MomentoResultado)
admin.site.register(CargueDocumental)
admin.site.register(RegistroSincronizacion)


@admin.register(PerfilAcademico)
class AdminPerfil(admin.ModelAdmin):
    list_display = ('usuario', 'codigo_matricula', 'programa', 'semestre_actual', 'estado')
    exclude = ('numero_documento',)
