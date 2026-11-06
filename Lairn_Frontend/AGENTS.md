# PseudoTutor Frontend

## Comandos

- `npm run dev` — servidor de desarrollo (Vite, puerto 5173)
- `npm run build` — compila con `tsc -b` y luego `vite build`
- `npm run lint` — ESLint sobre `**/*.{ts,tsx}`
- `npm run preview` — previsualiza el build de producción
- `npx shadcn@latest add <component>` — agrega componente Shadcn/UI

No hay tests configurados. No hay CI ni pre-commit hooks.

## Stack

React 19 + TypeScript 6 + Vite 8 + Tailwind CSS v4 + Shadcn/UI (estilo `base-nova`, iconos `lucide`).
HTTP con Axios. Rutas con React Router v7 (`BrowserRouter`).
Forms con React Hook Form + Zod.

## Path alias

`@/*` → `./src/*`. Está en `vite.config.ts` (resolve.alias) y en `tsconfig.json` (paths).
**No usar `baseUrl`** — TypeScript 6 lo deprecó y rompe el build.

## Convención de nombres

Todo el código está en **español**:
- Archivos: `pagina-login.tsx`, `rutas-protegidas.tsx` (kebab-case)
- Componentes/funciones: `PaginaLogin`, `RutaProtegida` (PascalCase)
- Variables/hooks: `estaAutenticado`, `iniciarSesion` (camelCase)
- Imports: usar alias `@/` en lugar de rutas relativas largas

## Comentarios en el código

Todo archivo fuente (.ts, .tsx) debe tener comentarios explicativos **en español** al inicio del archivo describiendo su propósito, y comentarios inline en lógica compleja. Los comentarios deben explicar el "por qué" y el "qué hace", no repetir lo obvio. No pedir permiso para comentar — hacerlo automáticamente.

## Autenticación (JWT)

Tokens en `localStorage` con claves `access_token` y `refresh_token`.
El interceptor de Axios en `src/servicios/api.ts` refresca automáticamente el access token en errores 401.
Si el refresh falla, redirige a `/iniciar-sesion`.

Endpoints backend usados:
- `POST /usuarios/iniciar-sesion/` → `{ email, password }` → `{ access, refresh }`
- `GET /usuarios/mis-datos/` → datos del usuario autenticado
- `POST /usuarios/cerrar-sesion/` → blacklist del refresh token
- `POST /usuarios/token/actualizar/` → `{ refresh }` → `{ access, refresh? }`

### Exámenes y Cursos
- `GET /examenes/cursos/` → cursos del docente
- `POST /examenes/cursos/` → crear curso
- `GET /examenes/mis-cursos/` → cursos del estudiante inscrito
- `POST /examenes/inscribirse/` → inscribir estudiante a curso con código
- `GET /examenes/examenes/` → todos los exámenes (docente filtra client-side por `curso`)
- `POST /examenes/examenes/` → crear examen
- `GET /examenes/mis-cursos/{curso_id}/examenes/` → exámenes de un curso para el estudiante
- `GET /examenes/cursos/{id}/estudiantes/` → estudiantes de un curso
- `DELETE /examenes/cursos/{id}/estudiantes/{estId}/` → eliminar estudiante de curso

### Evaluación Académica (`/academico`, Administrador y Coordinador)
- `GET /evaluacion/programas/` → programas activos
- `POST /evaluacion/programas/` → crear programa
- `PATCH /evaluacion/programas/{id}/` → actualizar; `{"activo": false, "estado_revision": "inactivo"}` desactiva (borrado lógico, HU-01.8)
- `GET /evaluacion/programas/{id}/semestres/` → semestres de la malla
- `GET /evaluacion/programas/{id}/asignaturas/` → asignaturas de la malla
- `GET /evaluacion/programas/{id}/competencias/` → competencias del programa
- `POST /evaluacion/programas/{id}/competencias/` → crear competencia `{nombre, tipo: 'transversal'|'especifica', descripcion}`
- `GET /evaluacion/programas/{id}/resultados/` → resultados de aprendizaje DCE
- `GET /evaluacion/programas/{id}/momentos/` → momentos de evaluación
- `GET /evaluacion/programas/{id}/tablero/` → resumen del programa
- `GET /evaluacion/cargues/` → cargues documentales
- `POST /evaluacion/integracion/importar-json/` → `{datos, modo: 'simulacro'|'real', fuente?: 'archivo'|'pegado', huella?}` (archivo o JSON pegado)
- `POST /evaluacion/integracion/importar-url/` → `{url, modo, huella?}`: el backend descarga el JSON (solo https, bloquea redes internas, 5 MB, 20/min). `modo: 'real'` exige la `huella` devuelta por la validación (`simulacro`); si la fuente cambió responde 409. Flujo en `use-importacion.ts` + `componentes/asistente-importacion.tsx`.

### Evaluación formal por momento (`/academico/momentos/:momentoId/evaluaciones`, Admin y Coordinador — HU-06)
- `GET/POST /evaluacion/momentos/{id}/evaluaciones/` → `{nombre, instrucciones, tipo: 'cuestionario', fecha_inicio, fecha_fin, duracion_minutos}` (tipo `tarea` responde 400 hasta HU-08B)
- `GET /evaluacion/momentos/{id}/banco-elegible/` → RA del momento + preguntas aprobadas (sin las ya usadas en laboratorio)
- `GET/PATCH/DELETE /evaluacion/evaluaciones/{id}/` · `GET/PUT .../preguntas/ {preguntas: [ids]}` · `POST .../publicar/` (publicada = 409 al editar)
- Código: `pages/academico/pagina-evaluacion-formal.tsx` + `use-evaluacion-formal.ts`; tipos en `src/types/evaluacion-formal.ts`.

### Reporte ejecutivo (`/reporte-institucional`, Vicerrector y Admin — HU-11)
- `GET /evaluacion/reporte-ejecutivo/[?programa=id]` → institución con desglose por programa, o programa con desglose por materia (drill-down; el programa va en la URL `?programa=`).
- `GET /evaluacion/reporte-ejecutivo/exportar/?formato=pdf|xlsx[&programa=id]` (reportlab / openpyxl en el backend).

### Alerta temprana (`/academico` → pestaña "Alertas", Admin y Coordinador — HU-10)
- `GET/PUT /evaluacion/alertas/regla/` `{porcentaje_minimo, actividades_minimas, activa}` (PUT solo Admin; reevalúa todo)
- `GET /evaluacion/programas/{id}/alertas/?estado=abierta|atendida|resuelta&tipo=` (reevalúa el programa) · `POST /evaluacion/alertas/{id}/atender/ {nota}` · `GET .../alertas/exportar/` (CSV `;` + BOM, solo Admin)
- Comando programable: `python manage.py evaluar_alertas`. Actividad = evaluación formal (% aciertos) o tarea calificada (nota/5).

### Desempeño por RA (`/academico` → pestaña "Desempeño por RA", solo Administrador — HU-09.1)
- `GET /evaluacion/programas/{id}/desempeno-ra/?momento=&evaluacion=` → `{resumen, grupal[], individual[], filtros, metrica}`
- Métrica PROVISIONAL (pendiente con Vicerrectoría): aciertos ÷ preguntas presentadas del RA en intentos enviados de evaluaciones tipo cuestionario; sin responder = no acertada. Definida en un solo lugar: `backend_lairn/apps/evaluacion_resultados/services/servicio_desempeno_ra.py`.

### Presentación de la evaluación formal (`/mis-evaluaciones`, solo Estudiante — HU-07)
- `GET /evaluacion/estudiante/evaluaciones/` (activas convocadas + ya presentadas) · `GET .../evaluaciones/{id}/` (incluye `ahora_servidor`; preguntas solo con intento en curso, SIN respuesta correcta)
- `POST .../evaluaciones/{id}/iniciar/` (intento único) · `PUT .../evaluaciones/{id}/respuestas/ {pregunta, opcion}` (se guarda al marcar) · `POST .../evaluaciones/{id}/enviar/`
- Temporizador con el reloj del servidor; al llegar a 0 la página envía sola y el servidor cierra perezosamente cualquier intento vencido. Barra del temporizador `fixed` abajo (el `<main>` del layout tiene `overflow-auto`, así que `sticky` no es fiable).

### Tareas prácticas con rúbrica (HU-08B docente `/tareas`, HU-08A estudiante `/mis-tareas`)
- Docente: `GET/POST /evaluacion/docente/tareas/?asignatura=` · `POST .../tareas/generar/ {asignatura, resultado, fecha_limite, formatos_permitidos}` (IA) · `GET/PATCH/DELETE .../tareas/{id}/` (solo borrador) · `POST/DELETE .../tareas/{id}/archivos/[{aid}/]` · `POST .../tareas/{id}/publicar/` · `GET .../tareas/{id}/entregas/` · `GET .../entregas/{id}/archivo/` · `POST .../entregas/{id}/calificar/ {niveles_elegidos, observaciones}`
- Estudiante: `GET /evaluacion/estudiante/tareas/[{id}/]` · `GET .../tareas/{id}/archivos/{aid}/` · `POST .../tareas/{id}/entregar/` (multipart `archivo`, envío único y definitivo) · `GET .../entregas/{id}/archivo/`
- Rúbrica: criterios `{criterio, peso (suman 100), niveles: [{nombre, valor 0-5}]}`; nota = Σ peso/100 × valor. Archivos privados: se descargan con Axios `responseType: 'blob'` (`descargarArchivo` en `pages/tareas/utilidades-tareas.ts`), nunca por `/media/`.
- Evaluación formal tipo `tarea`: `{tipo: 'tarea', tarea: id}` (tarea publicada de un RA del momento).

### Banco de preguntas por RA (`/banco-preguntas`, solo Docente — HU-04/05)
- `GET /evaluacion/docente/asignaturas/` → asignaturas cuyo `curso_vinculado` es un curso del docente, con sus RA y competencias transversales
- `POST /evaluacion/docente/banco/generar/` → `{asignatura, resultado, competencia_transversal?, cantidad 1-5}` → preguntas en estado `pendiente` (IA, 20-90 s, timeout 120 s, 10/min)
- `GET /evaluacion/docente/banco/?estado=&asignatura=&resultado=&competencia_transversal=`
- `PATCH /evaluacion/docente/banco/{id}/` (solo pendientes) · `POST .../aprobar/` · `POST .../descartar/ {motivo?}`
- La coordinación vincula curso↔asignatura en Malla (`curso_vinculado`, lista en `GET /evaluacion/cursos/`).
- Código: `src/pages/banco-preguntas/` (hook `use-banco-preguntas.ts`), tipos en `src/types/banco.ts`.

### Motor Adaptativo (rendir examen)
- `POST /motor-adaptativo/iniciar/` → `{ examen_id }` → inicia sesión de examen, devuelve primera pregunta
- `POST /motor-adaptativo/{sesion_id}/responder/` → `{ respuesta, tiempo_segundos }` → envía respuesta, devuelve siguiente pregunta o resultado final

**Importante:** el `sesion_id` no siempre viene en la respuesta de `/responder/`. Guardarlo en un `useRef` al iniciar para no perderlo.

La respuesta del backend trae los campos de pregunta al nivel raíz (`pregunta`, `opciones`, `explicacion`, `pregunta_numero`, `total_preguntas`), no dentro de un objeto `pregunta_actual`.

Estos endpoints se usan en `src/pages/examenes/pagina-rendir-examen.tsx`.

## Manejo de errores en peticiones API

El backend devuelve errores de validación como objetos con arrays de mensajes:
```json
{ "codigo": ["El código no existe"], "email": ["Este campo es requerido."] }
```

Patrón estándar para capturar y mostrar estos errores:
```tsx
} catch (err: unknown) {
  const axiosErr = err as {
    response?: { data?: Record<string, string[]> }
  }
  const data = axiosErr.response?.data
  if (data) {
    const mensajes = Object.values(data).flat().join('. ')
    toast.error(mensajes)
  } else {
    toast.error('Mensaje genérico de error')
  }
}
```

- `Object.values(data).flat()` extrae todos los mensajes de error
- `.join('. ')` los une en un solo string
- Si no hay `data` del backend, mostrar mensaje genérico
- Usar `toast.error()` de `sonner` para notificaciones

## Roles

Cinco roles como strings exactos: `Administrador`, `Coordinador`, `Vicerrector`, `Docente`, `Estudiante`.
`Vicerrector` (HU-11): solo lectura; entra directo a `/reporte-institucional`. Backend: `EsLectorInstitucional` (Vicerrector o Admin, solo GET).
`Coordinador` (HU-01.3 a HU-02.3): entra directo a `/academico`; consulta programas y gestiona malla, competencias, RA y momentos. No crea/edita programas ni ve Importar (`ac.esAdmin`). Backend: `EsGestorAcademico` / `EsAdministradorOLecturaCoordinador`.
Deben coincidir exactamente con los datos del backend (case-sensitive).
La sidebar en `src/app/layout.tsx` muestra navegación diferente por rol.
`RutaProtegida` acepta `rolesPermitidos?: string[]` para restringir acceso.

## Estructura de páginas (feature-based)

Las páginas en `src/pages/` están agrupadas por feature. Cuando un feature tiene vistas distintas por rol, se usa el patrón `pagina-{feature}-{rol}.tsx`. Los componentes compartidos del feature van en `componentes/` dentro de la carpeta del feature.

```
pages/
├── auth/                          ← login (compartido)
├── dashboard/                     ← pagina-dashboard-{admin,docente,estudiante}.tsx
├── usuarios/                      ← solo admin
├── examenes/                      ← docente + estudiante (vistas distintas)
│   ├── componentes/
│   │   ├── modal-crear-examen.tsx
│   │   ├── tab-examenes-docente.tsx
│   │   ├── tab-estudiantes-docente.tsx
│   │   ├── tab-analitica-docente.tsx
│   │   ├── tab-examenes-estudiante.tsx
│   │   ├── tab-resumen-estudiante.tsx
│   │   └── tab-intento-estudiante.tsx
│   ├── utilidades.ts              ← helpers compartidos (dificultadConfig, colorNota, colorAprobados)
│   ├── pagina-examenes-curso-docente.tsx
│   └── pagina-examenes-curso-estudiante.tsx
├── analitica/                     ← admin + docente + estudiante
│   └── componentes/
└── cursos/                        ← docente + estudiante
```

### Convención de nombres para tabs

Los componentes de tabs usan el sufijo `-docente` o `-estudiante` para distinguirlos por rol:
- `tab-examenes-docente.tsx` — tab de exámenes para docente
- `tab-estudiantes-docente.tsx` — tab de estudiantes para docente
- `tab-analitica-docente.tsx` — tab de analítica para docente
- `tab-examenes-estudiante.tsx` — tab de exámenes para estudiante
- `tab-resumen-estudiante.tsx` — tab de resumen de conocimiento para estudiante
- `tab-intento-estudiante.tsx` — tab de detalle de intentos para estudiante

Los helpers compartidos van en `utilidades.ts` en la raíz del feature.

## Routing por rol

React Router no permite múltiples rutas en el mismo path. La solución: componentes selectores `*PorRol` en `src/app/enrutador.tsx` que leen el rol del contexto auth y renderizan la página correcta. Cada feature compartido tiene un selector.

Al agregar un nuevo feature con vistas por rol:
1. Crear `pagina-{feature}-{rol}.tsx` en la carpeta del feature
2. Crear componente selector `Pagina{Feature}PorRol` en `enrutador.tsx`
3. Agregar `<Route>` con `rolesPermitidos` y el selector

Usar la constante `ROLES` de `src/tipos/usuario.ts` en vez de strings hardcoded.

## Estructura general

- `src/app/` — enrutador y layout principal
- `src/context/contexto-auth/` — proveedor de autenticación (exporta `ProveedorAuth` y `useAuth`)
- `src/pages/` — vistas por feature
- `src/services/` — instancia Axios y servicios de API
- `src/types/` — interfaces TypeScript y constante `ROLES`
  - `src/types/usuario.ts` — roles y modelo de usuario
  - `src/types/auth.ts` — tipos de autenticación
  - `src/types/examen.ts` — tipos compartidos de exámenes (`Examen`, `SesionExamen`, `ResultadoExamen`)
- `src/utilities/` — helpers (rutas protegidas)
- `src/components/ui/` — componentes Shadcn generados (no editar directamente)
- `src/lib/utils.ts` — función `cn()` de Shadcn

## Efectos visuales reutilizables

Componentes de animación/efectos en `src/components/efectos/`:

- **`CanvasParticulas`** — Fondo de partículas con efecto de constelación/red neuronal.
  Puntos flotantes conectados por líneas tenues. Ideal para fondos de branding con temática IA/tech.
  Uso: `<CanvasParticulas />` dentro de un contenedor con `position: relative; overflow: hidden`.
  Props opcionales: `cantidad`, `distanciaMaxima`, `color`, `opacidadMin/Max`, etc.
  Ver implementación en `src/pages/auth/pagina-login.tsx`.

## Componentes reutilizables

Componentes de UI compartidos en `src/components/`:

- **`EncabezadoGradiente`** — Header con gradiente índigo, patrón de puntos, link de volver y badge opcional.
  Uso: `<EncabezadoGradiente titulo="Álgebra" subtitulo="Exámenes" volverA="/mis-cursos" badgeTexto="3/5 rendidos" />`.
  Props: `titulo`, `subtitulo?`, `volverA?`, `volverTexto?`, `badgeTexto?`, `children?`.

- **`CardCurso`** — Card de curso con header gradiente, avatar con inicial, badge, stats y barra de progreso.
  Uso: `<CardCurso id={1} nombre="Álgebra" descripcion="..." examenesRendidos={3} totalExamenes={5} notaPromedio={4.2} badgeTexto="Prof. García" />`.
  Props: `id`, `nombre`, `descripcion`, `examenesRendidos`, `totalExamenes`, `notaPromedio?`, `badgeTexto?`, `rutaBase?`.

- **`CardExamen`** — Card de examen con dificultad, stats compactas, estado de intentos y botón contextual.
  Uso: `<CardExamen id={1} cursoId={10} titulo="Parcial 1" tema="Álgebra" dificultad={2} numPreguntas={20} tiempo={60} maxIntentos={3} ultimaNota={4.2} intentosUsados={1} />`.
  Props: `id`, `cursoId`, `titulo`, `tema`, `dificultad`, `numPreguntas`, `tiempo`, `maxIntentos`, `ultimaNota?`, `intentosUsados?`.

## Componentes de UI

**Regla obligatoria:** usar exclusivamente los componentes Shadcn/UI instalados en `src/components/ui/`. No crear componentes de UI desde cero ni agregar nuevas dependencias externas para UI. Si falta un componente, instalarlo con `npx shadcn@latest add <component>`.

Componentes disponibles:
`badge`, `button`, `card`, `carousel`, `chart`, `dialog`, `input`, `label`, `radio-group`, `select`, `sheet`, `sonner`, `switch`, `table`, `tabs`, `textarea`, `tooltip`.

Para tablas: usar `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` de `@/components/ui/table`.
Para paneles laterales: usar `Sheet`, `SheetContent`, `SheetHeader`, `SheetTitle`, `SheetDescription` de `@/components/ui/sheet`.

## Paleta de colores

Todos los componentes deben usar exclusivamente los colores de la paleta definida en `src/index.css`. No usar colores arbitrarios como `bg-white`, `bg-gray-50`, `text-gray-700`, etc.

Colores disponibles (usar como clases de Tailwind):
- `bg-background` / `text-foreground` — fondo y texto principal
- `bg-card` / `text-card-foreground` — fondo de cards y tablas (blanco en light, oscuro en dark)
- `bg-primary` / `text-primary-foreground` — púrpura principal
- `bg-secondary` / `text-secondary-foreground` — gris claro
- `bg-muted` / `text-muted-foreground` — gris sutil para headers, tooltips
- `bg-accent` / `text-accent-foreground` — ámbar/naranja para destacados
- `bg-destructive` / `text-destructive-foreground` — rojo para errores/eliminar
- `border` — bordes estándar
- `ring` — focus rings

Regla: siempre usar las variantes de la paleta para garantizar consistencia en light/dark mode.

## Quirks

- `npm run build` ejecuta `tsc -b` primero; si TS falla, no se genera build.
- `erasableSyntaxOnly: true` en tsconfig — no usar `enum` ni `namespace` de TS.
- `verbatimModuleSyntax: true` — usar `import type` para imports de solo tipos.
- Shadcn genera componentes en `src/components/ui/`; se pueden modificar para personalizar diseño, pero siempre usando la paleta de colores.
- Los componentes Shadcn usan `@base-ui/react` (no Radix). Props como `onPointerDownOutside` o `onEscapeKeyDown` no existen; usar `onOpenChange` en el componente `Dialog` raíz para controlar cierre.
- El `.env` tiene `VITE_API_URL=http://localhost:8000/api`; el backend debe estar corriendo.

## Mejores prácticas React + Vite (reglas obligatorias)

Referencia completa: `.agents/skills/react-vite-best-practices/AGENTS.md`.

### 1. Build Optimization (CRITICAL)

**`vite.config.ts` debe incluir siempre:**
- `build.target: 'baseline-widely-available'` — código moderno sin polyfills innecesarios.
- `build.sourcemap: false` en producción (no exponer código fuente).
- `build.chunkSizeWarningLimit: 500` — advertir si un chunk supera 500 KB.
- `build.rollupOptions.output.manualChunks` — separar vendor libs en chunks independientes.
- `optimizeDeps.include` — pre-bundlea dependencias pesadas para desarrollo más rápido.

**Manual chunks configurados:**
```ts
manualChunks(id) {
  if (id.includes('node_modules')) {
    if (id.includes('react') && !id.includes('react-router')) return 'vendor'
    if (id.includes('recharts')) return 'charts'
    if (id.includes('react-hook-form') || id.includes('@hookform') || id.includes('zod')) return 'forms'
    if (id.includes('react-router')) return 'router'
  }
}
```

Al agregar una nueva dependencia pesada, actualizar `manualChunks` en `vite.config.ts`.

### 2. Code Splitting (CRITICAL)

**Todas las páginas deben usar `React.lazy()` + `export default`.**

Patrón obligatorio para nuevas páginas:
```tsx
// src/pages/feature/pagina-nueva.tsx
export default function PaginaNueva() { ... }
```

En `enrutador.tsx`:
```tsx
const PaginaNueva = lazy(() => import('@/pages/feature/pagina-nueva'))
```

**Reglas:**
- Nunca importar páginas estáticamente en `enrutador.tsx` (rompe code splitting).
- Siempre envolver rutas en `<Suspense fallback={<CargandoPagina />}>`.
- Componentes pesados (charts, editores, modals complejos) también deben lazy-loadearse con `lazy()`.
- No crear un solo chunk gigante — cada ruta debe ser su propio chunk.

### 3. Variables de entorno

- Todas las variables deben empezar con `VITE_` para ser accesibles en el cliente.
- Declarar tipos en `src/vite-env.d.ts` para autocompletado y type safety.
- Usar `.env` para desarrollo, `.env.production` para producción.
- **Nunca** exponer secrets (API keys, passwords) en variables `VITE_` — son visibles en el bundle.

### 4. Assets

- Fuentes: importar desde paquetes `@fontsource-*` (ya configurado con `@fontsource-variable/geist`).
- SVGs: usar como componentes React con SVGR si se necesitan props dinámicas.
- Imágenes: colocar en `public/` si son estáticas, importar en JS si necesitan hash.
- No abusar de `public/` — todo lo que se importa en JS tiene hash automático para cache busting.

### 5. Checklist al agregar una nueva página

1. Crear `pagina-{nombre}.tsx` con `export default function PaginaNombre()`.
2. Agregar `const PaginaNombre = lazy(() => import('@/pages/...'))` en `enrutador.tsx`.
3. Agregar `<Route>` dentro del `<Suspense>` existente en `RutasPrivadas`.
4. Si la página tiene componentes pesados, lazy-loadearlos también.
5. Verificar que `npm run build` genera un chunk separado para la nueva página.
6. Si la página usa una nueva librería pesada, agregarla a `manualChunks`.
