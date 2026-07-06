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

Tres roles como strings exactos: `Administrador`, `Docente`, `Estudiante`.
Deben coincidir exactamente con los datos del backend (case-sensitive).
La sidebar en `src/app/layout.tsx` muestra navegación diferente por rol.
`RutaProtegida` acepta `rolesPermitidos?: string[]` para restringir acceso.

## Estructura de páginas (feature-based)

Las páginas en `src/paginas/` están agrupadas por feature. Cuando un feature tiene vistas distintas por rol, se usa el patrón `pagina-{feature}-{rol}.tsx`. Los componentes compartidos del feature van en `componentes/` dentro de la carpeta del feature.

```
paginas/
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
- `src/contextos/contexto-auth/` — proveedor de autenticación (exporta `ProveedorAuth` y `useAuth`)
- `src/paginas/` — vistas por feature
- `src/servicios/` — instancia Axios y servicios de API
- `src/tipos/` — interfaces TypeScript y constante `ROLES`
  - `src/types/usuario.ts` — roles y modelo de usuario
  - `src/types/auth.ts` — tipos de autenticación
  - `src/types/examen.ts` — tipos compartidos de exámenes (`Examen`, `SesionExamen`, `ResultadoExamen`)
- `src/utilidades/` — helpers (rutas protegidas)
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
