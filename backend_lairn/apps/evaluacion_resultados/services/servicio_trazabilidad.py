"""
Servicio de trazabilidad: bitácora + versionado histórico (HU-01.8).

- `registrar_sincronizacion`: deja `RegistroSincronizacion` por cada
  import/sync para auditoría TI.
- `versionar_resultado`: si un RA ya se usó en evaluación, no se edita
  in-place: se clona con `version + 1` y el anterior se desactiva.
  Hoy detecta uso vía `vinculos_momento`; cuando existan evaluaciones
  finalizadas ligadas, se amplía la condición sin cambiar la firma.
"""

from apps.evaluacion_resultados.models import RegistroSincronizacion


def registrar_sincronizacion(
    *,
    origen: str,
    entidad: str,
    modo: str = 'real',
    total_recibidos: int = 0,
    creados: int = 0,
    actualizados: int = 0,
    omitidos: int = 0,
    errores: list | None = None,
    ejecutado_por=None,
) -> RegistroSincronizacion:
    return RegistroSincronizacion.objects.create(
        origen=origen,
        entidad=entidad,
        modo=modo,
        total_recibidos=total_recibidos,
        creados=creados,
        actualizados=actualizados,
        omitidos=omitidos,
        errores=errores or [],
        ejecutado_por=ejecutado_por,
    )


def requiere_versionado(resultado) -> bool:
    """True si el RA ya está comprometido y no debe editarse in-place."""
    return resultado.vinculos_momento.exists()


def versionar_resultado(resultado, *, nuevos_datos: dict, creado_por=None):
    """Crea la versión N+1 y desactiva la anterior (retorna la nueva)."""
    from apps.evaluacion_resultados.models import ResultadoAprendizaje
    from apps.evaluacion_resultados.models import OpcionesEstadoRevision

    nueva = ResultadoAprendizaje.objects.create(
        competencia_id=nuevos_datos.get('competencia_id', resultado.competencia_id),
        asignatura_id=nuevos_datos.get('asignatura_id', resultado.asignatura_id),
        descripcion=nuevos_datos.get('descripcion', resultado.descripcion),
        evidencia_observable=nuevos_datos.get('evidencia_observable', resultado.evidencia_observable),
        tarea_sugerida=nuevos_datos.get('tarea_sugerida', resultado.tarea_sugerida),
        criterios_rubrica=nuevos_datos.get('criterios_rubrica', resultado.criterios_rubrica),
        origen=resultado.origen,
        datos_origen=resultado.datos_origen,
        estado_revision=OpcionesEstadoRevision.APROBADO,
        version=resultado.version + 1,
        activo=True,
        creado_por=creado_por,
    )
    resultado.activo = False
    resultado.estado_revision = OpcionesEstadoRevision.INACTIVO
    resultado.reemplazado_por = nueva
    resultado.save(update_fields=['activo', 'estado_revision', 'reemplazado_por', 'actualizado_en'])
    return nueva
