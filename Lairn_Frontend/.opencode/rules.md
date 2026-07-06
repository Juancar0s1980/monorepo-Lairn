# Reglas del Proyecto — PseudoTutor Frontend

## 1. Idioma

- TODO el código, comentarios, nombres de variables, funciones, componentes y archivos debe estar en **español**.
- Excepción: nombres de librerías externas y sus APIs (React, Axios, Tailwind, etc.) se mantienen en inglés.

## 2. Nomenclatura

| Elemento             | Convención       | Ejemplo                          |
| -------------------- | ---------------- | -------------------------------- |
| Componentes          | PascalCase       | `PaginaLogin`, `CardExamen`      |
| Funciones/hooks      | camelCase        | `iniciarSesion`, `useExamenes`   |
| Variables/constantes | camelCase        | `estaAutenticado`, `rolUsuario`  |
| Constantes globales  | UPPER_SNAKE_CASE | `ROLES`, `API_BASE_URL`          |
| Archivos de página   | kebab-case       | `pagina-login.tsx`               |
| Componentes UI       | kebab-case       | `card-curso.tsx`                 |
| Tipos/Interfaces     | PascalCase       | `Usuario`, `LoginRequest`        |

## 3. Estructura de Archivos

- Páginas van en `src/paginas/` (no `src/pages/`), subcarpetas por feature.
- Componentes reutilizables van en `src/components/`.
- Componentes de UI (shadcn) van en `src/components/ui/` — **no editar manualmente**.
- Servicios API van en `src/services/`.
- Tipos van en `src/types/`.
- Utilidades van en `src/utilidades/`.
- Contextos van en `src/context/`.
- Hooks personalizados van en `src/hooks/`.
- Layout y enrutador van en `src/app/`.

## 4. Imports

- Usar siempre el alias `@/` en lugar de rutas relativas largas.
- Ejemplo: `import { useAuth } from '@/context/contexto-auth/use-auth'` ✅
- Evitar: `import { useAuth } from '../../context/contexto-auth/use-auth'` ❌

## 5. UI y Componentes

- **Solo** usar componentes de `src/components/ui/` (shadcn/ui).
- **No** crear componentes de UI desde cero si ya existe uno en shadcn.
- **No** agregar nuevas dependencias de UI sin consultar.
- Los componentes shadcn usan `@base-ui/react`, **no Radix**. No usar props de Radix como `onPointerDownOutside` o `onEscapeKeyDown`.
- Usar `cn()` de `@/lib/utils` para combinar clases de Tailwind.
- Usar `lucide-react` para iconos.

## 6. Formularios

- Usar `react-hook-form` + `zod` para validación.
- El schema de Zod se define separado del formulario.
- Usar `@hookform/resolvers/zod` para integración.

## 7. Autenticación

- Tokens se guardan en `localStorage` con keys `access_token` y `refresh_token`.
- El contexto de auth está en `src/context/contexto-auth/`.
- Usar el hook `useAuth()` para acceder al estado y funciones de auth.
- Los roles se definen con la constante `ROLES` de `@/types/usuario` — **no usar strings hardcodeados**.
- Roles válidos: `Administrador`, `Docente`, `Estudiante`.

## 8. Enrutamiento

- Usar React Router v7 (`BrowserRouter`).
- Rutas protegidas con componente `RutaProtegida` de `@/utilities/rutas-protegidas`.
- Para rutas con vistas por rol, usar componentes selectores `*PorRol` en el enrutador.
- **No** crear múltiples rutas en el mismo path — usar el selector por rol.

## 9. Peticiones HTTP

- Usar la instancia de Axios de `@/services/api.ts` — **no** crear nuevas instancias.
- El interceptor de Axios refresca automáticamente el access token en errores 401.
- Si el refresh falla, redirige a `/iniciar-sesion`.

## 10. Comentarios

- Cada archivo debe tener un comentario al inicio describiendo su propósito.
- Comentarios inline en lógica compleja explicando el **por qué**, no el qué obvio.
- Todos los comentarios en **español**.

## 11. Estilo de Código

- No usar `enum` de TypeScript (no compatible con `erasableSyntaxOnly`).
- Usar `import type` para imports de solo tipos (`verbatimModuleSyntax`).
- No usar `namespace` de TypeScript.
- Preferir `const` sobre `let`.
- Evitar `any` — usar tipos explícitos o `unknown`.
- No usar `console.log` en código de producción.

## 12. Rutas por Rol — Patrón

Cuando un feature tiene vistas distintas por rol:
1. Crear `pagina-{feature}-{rol}.tsx` en la carpeta del feature.
2. Crear componente selector `Pagina{Feature}PorRol` en el enrutador.
3. Agregar `<Route>` con `rolesPermitidos` y el selector.

## 13. Code Splitting (CRITICAL)

- **Todas las páginas** deben usar `export default function PaginaX()`.
- En `enrutador.tsx`, importar páginas con `lazy(() => import('@/pages/...'))`.
- Nunca importar páginas estáticamente en el enrutador — rompe code splitting.
- Siempre envolver rutas en `<Suspense fallback={<CargandoPagina />}>`.
- Componentes pesados (charts, editores, modals complejos) también deben lazy-loadearse.

## 14. Build Optimization (CRITICAL)

- `vite.config.ts` debe mantener `manualChunks` actualizado al agregar dependencias pesadas.
- Chunks configurados: `vendor` (react), `charts` (recharts), `forms` (hook-form, zod), `router` (react-router).
- Al agregar una librería nueva pesada, agregarla al `manualChunks` correspondiente en `vite.config.ts`.
- `build.target: 'baseline-widely-available'` — no cambiar.
- `build.sourcemap: false` en producción — no activar.

## 15. Variables de entorno

- Todas las variables deben empezar con `VITE_` para ser accesibles en el cliente.
- Declarar tipos en `src/vite-env.d.ts` para autocompletado y type safety.
- `.env` para desarrollo, `.env.production` para producción.
- **Nunca** exponer secrets (API keys, passwords) en variables `VITE_`.

## 16. Checklist al agregar una nueva página

1. Crear `pagina-{nombre}.tsx` con `export default function PaginaNombre()`.
2. Agregar `const PaginaNombre = lazy(() => import('@/pages/...'))` en `enrutador.tsx`.
3. Agregar `<Route>` dentro del `<Suspense>` existente en `RutasPrivadas`.
4. Si la página tiene componentes pesados, lazy-loadearlos también.
5. Verificar que `npm run build` genera un chunk separado para la nueva página.
6. Si la página usa una nueva librería pesada, agregarla a `manualChunks`.

## 17. Prohibido

- No instalar dependencias nuevas sin consultar.
- No modificar archivos en `src/components/ui/` directamente.
- No usar `console.log` para debug en código final.
- No hardcodear roles como strings — usar `ROLES`.
- No crear rutas duplicadas en el mismo path.
- No usar estilos inline — usar Tailwind.
- No ignorar errores silenciosamente sin log o manejo.
- No usar `useEffect` innecesario — evaluar si se puede derivar el estado.
- No importar páginas estáticamente en `enrutador.tsx` — usar siempre `lazy()`.
- No crear variables de entorno sin prefijo `VITE_`.
- No declarar variables de entorno sin tipar en `src/vite-env.d.ts`.
