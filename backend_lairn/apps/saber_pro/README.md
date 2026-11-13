# Módulo Saber Pro

Módulo de preparación para el examen **Saber Pro** (ICFES, Colombia) dentro de
PseudoTutor Lairn. Los docentes crean cursos y simulacros, generan contenido con
IA y consultan la analítica de sus grupos; los estudiantes se inscriben,
presentan simulacros y revisan su desempeño; coordinación y vicerrectoría
consultan la analítica consolidada de la institución.

## Funcionalidades

### Docente
- Crear y administrar cursos Saber Pro con código de acceso e inscripciones.
- Crear simulacros por competencia, afirmación y distribución de preguntas.
- Generar, revisar y aprobar contenido (preguntas y consignas) con IA.
- Analítica del curso por área, competencia, afirmación y parte de Inglés.
- Exportación a Excel y análisis de acciones de mejora con IA.
- Revisión y calificación de respuestas abiertas de Comunicación Escrita.
- Gestión de solicitudes de desbloqueo y anulación de presentaciones.

### Estudiante
- Inscripción a un curso mediante código de acceso.
- Consulta de simulacros activos y presentación cronometrada.
- Protección durante el simulacro con solicitud de desbloqueo al docente.
- Consulta de su propio desempeño (percentil) sin ver datos de terceros.

### Coordinador y Vicerrector
- Analítica institucional consolidada por curso, carrera, área y periodo.
- Exportación a Excel.
- Análisis de acciones de mejora con IA sobre la analítica institucional.

## Arquitectura

| Parte | Ubicación | Stack |
|---|---|---|
| Backend | `backend_lairn/apps/saber_pro/` | Django + DRF |
| Frontend | `Lairn_Frontend/src/pages/saber-pro/` | React + Vite + TypeScript |

La API se monta en `/api/saber-pro/` y las rutas están separadas por rol:

- `urls/docente.py`: cursos, contenido, simulacros, analítica y desbloqueos.
- `urls/estudiante.py`: inscripción, simulacros, presentación y desempeño.
- `urls/institucional.py`: analítica consolidada y catálogo de filtros.

### Backend

```
apps/saber_pro/
├── models/          # áreas, competencias, afirmaciones, cursos, simulacros...
├── serializers/     # contrato de la API
├── services/        # reglas de negocio, IA, analítica y exportación
├── views/           # una vista por acción, registradas en urls/
├── urls/            # rutas por rol
└── management/commands/seed_saber_pro.py
```

### Frontend

```
src/pages/saber-pro/
├── pagina-*.tsx     # vistas por rol y feature
└── componentes/     # modales, tarjetas, filtros y tablas compartidas
```

## Endpoints principales

| Grupo | Endpoints |
|---|---|
| Panel | `GET /api/saber-pro/panel/`, `GET /api/saber-pro/areas/` |
| Docente | `/docente/cursos/`, `/docente/cursos/{id}/simulacros/`, `/docente/cursos/{id}/contenido/`, `/docente/cursos/{id}/analitica/`, `/docente/cursos/{id}/analitica/acciones/`, `/docente/cursos/{id}/analitica/exportar/` |
| Estudiante | `/estudiante/unirse/`, `/estudiante/cursos/`, `/estudiante/simulacros/`, `/estudiante/desempeno/`, `/estudiante/presentaciones/{id}/` |
| Institucional | `/institucional/analitica/`, `/institucional/analitica/acciones/`, `/institucional/analitica/exportar/`, `/institucional/catalogo/` |

La documentación interactiva está disponible en `/api/docs/` (Swagger).

## Modelos principales

`AreaSaberPro`, `CompetenciaSaberPro`, `AfirmacionSaberPro`,
`EvidenciaSaberPro`, `CursoSaberPro`, `InscripcionCursoSaberPro`,
`ContenidoBancoSaberPro`, `Simulacro`, `SimulacroPregunta`,
`PresentacionSimulacro`, `PresentacionPregunta`, `RespuestaPresentacion` y
`SolicitudDesbloqueoSimulacro`.

## Integración con IA

- `services/agente_saber_pro.py`: generación de contenido del banco.
- `services/agente_analitica.py`: análisis de acciones recomendadas (curso e
  institución).
- El proveedor se configura con `AI_PROVIDER` (`openai`, `grok` o `groq`).
- En la analítica la IA solo recibe datos agregados: nunca resultados
  individuales ni datos personales.
- Si la IA falla, la consulta y la exportación a Excel siguen funcionando.

## Puesta en marcha

Las migraciones se aplican automáticamente al arrancar el contenedor `web`. Para
cargar los datos iniciales del módulo:

```bash
docker compose exec web python manage.py seed_saber_pro
```

## Permisos

Cada vista declara sus permisos en `core/permissions/permisos_rol.py`
(`EsDocente`, `EsEstudiante`, `EsLectorAnalitica`,
`EsLectorAnaliticaConIA`). La analítica institucional es agregada y no expone
resultados individuales de estudiantes.
