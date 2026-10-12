"""
Modelos de dominio de la app `saber_pro`.

La HU-16 habilita el punto de entrada del módulo (ítem del menú, panel de
entrada y estado vacío con invitación a crear/unirse) y todavía no persiste
nada: el panel se construye con catálogos por rol en `services/`.

Con la HU-17 se materializan los primeros modelos de dominio:

- `AreaSaberPro`: catálogo de las cinco áreas oficiales del examen, sembrado
  con `seed_saber_pro` (HU-17.1). Las épicas siguientes lo referencian como FK.
- `CursoSaberPro`: curso de preparación del docente con área, nombre,
  descripción y código de acceso autogenerado (HU-17.1/17.2).
- `InscripcionCursoSaberPro`: relación estudiante-curso con fecha de ingreso;
  alimenta el listado de inscritos del docente (HU-17.5) y será el recurso de
  la inscripción por código (HU-18).

Modelos restantes por épica (fuera de alcance de HU-17):
- HU-19: Simulacro, DistribucionSimulacro (competencias/afirmaciones que cubre).
- HU-20: Competencia, Afirmacion, Evidencia, PreguntaBanco.
- HU-21: presentación de simulacro y sesiones de práctica del estudiante.
- HU-23/24: modelos o vistas agregadas para ranking y analítica.

Se mantiene un módulo por recurso (mismo patrón que `examenes` y `laboratorios`).
"""

from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro

__all__ = [
    'AreaSaberPro',
    'CursoSaberPro',
    'InscripcionCursoSaberPro',
]