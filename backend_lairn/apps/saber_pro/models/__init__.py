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

Con la HU-20 se añade el catálogo académico y el banco de contenido:

- `CompetenciaSaberPro` / `AfirmacionSaberPro` / `EvidenciaSaberPro`: jerarquía
  de criterios de evaluación de las áreas estructuradas, sembrada con
  `seed_saber_pro` y seleccionada por el docente al generar contenido (HU-20.1).
- `ContenidoBancoSaberPro`: pregunta de selección múltiple o consigna de
  escritura generada con IA, con ciclo `pendiente → aprobado` que controla el
  uso en simulacros (HU-20.3/20.4). Se ancla a docente + área.

Con la HU-19 se agregan los modelos del simulacro:

- `Simulacro`: configuración del simulacro dentro de un curso (cantidad de
  preguntas, tiempo límite y disponibilidad para inscritos).
- `DistribucionSimulacro`: criterios académicos que cubre y preguntas que
  aporta cada uno.
- `SimulacroPregunta`: preguntas aprobadas asignadas, con orden y sin
  duplicados.

Con la HU-21 se agregan los modelos de presentación:

- `PresentacionSimulacro`: intento cronometrado de un estudiante sobre un
  simulacro, con estado, vencimiento y agregados de calificación.
- `PresentacionPregunta`: copia congelada y ordenada del contenido del intento.
- `RespuestaPresentacion`: respuesta única por bloque y su calificación.

Modelos restantes por épica (fuera de alcance de HU-17, HU-19, HU-20 y HU-21):
- HU-23/24: modelos o vistas agregadas para ranking y analítica.

Se mantiene un módulo por recurso (mismo patrón que `examenes` y `laboratorios`).
"""

from apps.saber_pro.models.afirmacion_saber_pro import AfirmacionSaberPro
from apps.saber_pro.models.area_saber_pro import AreaSaberPro
from apps.saber_pro.models.competencia_saber_pro import CompetenciaSaberPro
from apps.saber_pro.models.contenido_banco_saber_pro import ContenidoBancoSaberPro
from apps.saber_pro.models.curso_saber_pro import CursoSaberPro
from apps.saber_pro.models.distribucion_simulacro import DistribucionSimulacro
from apps.saber_pro.models.evidencia_saber_pro import EvidenciaSaberPro
from apps.saber_pro.models.inscripcion_curso_saber_pro import InscripcionCursoSaberPro
from apps.saber_pro.models.presentacion_pregunta import PresentacionPregunta
from apps.saber_pro.models.presentacion_simulacro import PresentacionSimulacro
from apps.saber_pro.models.respuesta_presentacion import RespuestaPresentacion
from apps.saber_pro.models.simulacro import Simulacro
from apps.saber_pro.models.simulacro_pregunta import SimulacroPregunta

__all__ = [
    'AfirmacionSaberPro',
    'AreaSaberPro',
    'CompetenciaSaberPro',
    'ContenidoBancoSaberPro',
    'CursoSaberPro',
    'DistribucionSimulacro',
    'EvidenciaSaberPro',
    'InscripcionCursoSaberPro',
    'PresentacionPregunta',
    'PresentacionSimulacro',
    'RespuestaPresentacion',
    'Simulacro',
    'SimulacroPregunta',
]