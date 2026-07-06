// Enrutador principal de la aplicación.
// Define todas las rutas y componentes selectores por rol (*PorRol).
//
// Estructura de rutas:
//   /iniciar-sesion  → PaginaLogin (pública)
//   /*               → RutasPrivadas (requiere autenticación)
//     /                  → Dashboard (vista diferente por rol)
//     /usuarios          → Solo Administrador
//     /mis-cursos/:id/examenes → Docente y Estudiante (vistas distintas)
//     /analitica         → Administrador y Docente (vistas distintas)
//
// Los componentes *PorRol resuelven qué página renderizar según el rol del usuario,
// ya que React Router no permite múltiples rutas en el mismo path.
//
// Code splitting: todas las páginas se cargan con React.lazy() para que
// el navegador descargue solo el JS necesario para la ruta actual.

import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProveedorAuth } from '@/context/contexto-auth'
import { Layout } from '@/app/layout'
import { RutaProtegida } from '@/utilities/rutas-protegidas'
import { ROLES } from '@/types/usuario'
import { useAuth } from '@/context/contexto-auth/use-auth'
import { Toaster } from '@/components/ui/sonner'
import { BrainCircuit } from 'lucide-react'

// Lazy loading de todas las páginas.
// Cada import() genera un chunk separado que se descarga solo cuando se visita la ruta.
const PaginaLogin = lazy(() => import('@/pages/auth/pagina-login'))
const PaginaDashboardAdmin = lazy(() => import('@/pages/dashboard/pagina-dashboard-admin'))
const PaginaDashboardDocente = lazy(() => import('@/pages/dashboard/pagina-dashboard-docente'))
const PaginaDashboardEstudiante = lazy(() => import('@/pages/dashboard/pagina-dashboard-estudiante'))
const PaginaUsuarios = lazy(() => import('@/pages/usuarios/pagina-usuarios'))
const PaginaExamenesCursoEstudiante = lazy(() => import('@/pages/examenes/pagina-examenes-curso-estudiante'))
const PaginaCursosDocente = lazy(() => import('@/pages/cursos/pagina-cursos-docente'))
const PaginaExamenesCursoDocente = lazy(() => import('@/pages/examenes/pagina-examenes-curso-docente'))
const PaginaRendirExamen = lazy(() => import('@/pages/examenes/pagina-rendir-examen'))
const PaginaCursosEstudiante = lazy(() => import('@/pages/cursos/pagina-cursos-estudiante'))

// Fallback de carga mostrado mientras se descarga el chunk de una página.
function CargandoPagina() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 animate-pulse">
          <BrainCircuit className="h-6 w-6 text-primary" />
        </div>
        <div className="flex gap-1">
          <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
          <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
          <span className="h-2 w-2 rounded-full bg-primary animate-bounce" />
        </div>
      </div>
    </div>
  )
}

// Selector por rol para el Dashboard: cada rol ve su propia vista.
function PaginaDashboardPorRol() {
  const { rol } = useAuth()

  if (rol === ROLES.ADMIN) return <PaginaDashboardAdmin />
  if (rol === ROLES.DOCENTE) return <PaginaDashboardDocente />
  if (rol === ROLES.ESTUDIANTE) return <PaginaDashboardEstudiante />
  return <Navigate to="/iniciar-sesion" replace />
}

// Selector por rol para Exámenes del Curso: Docente gestiona, Estudiante rinde.
function PaginaExamenesCursoPorRol() {
  const { rol } = useAuth()

  if (rol === ROLES.DOCENTE) return <PaginaExamenesCursoDocente />
  if (rol === ROLES.ESTUDIANTE) return <PaginaExamenesCursoEstudiante />
  return <Navigate to="/" replace />
}

// Selector por rol para Mis Cursos: Docente gestiona, Estudiante ve los suyos.
function PaginaCursosPorRol() {
  const { rol } = useAuth()

  if (rol === ROLES.DOCENTE) return <PaginaCursosDocente />
  if (rol === ROLES.ESTUDIANTE) return <PaginaCursosEstudiante />
  return <Navigate to="/" replace />
}

// Agrupa todas las rutas privadas dentro del Layout compartido.
// Cada ruta está envuelta en RutaProtegida con los roles que pueden acceder.
function RutasPrivadas() {
  return (
    <Layout>
      <Suspense fallback={<CargandoPagina />}>
        <Routes>
          <Route
            path="/"
            element={
              <RutaProtegida>
                <PaginaDashboardPorRol />
              </RutaProtegida>
            }
          />
          <Route
            path="/usuarios"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN]}>
                <PaginaUsuarios />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-cursos"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE, ROLES.ESTUDIANTE]}>
                <PaginaCursosPorRol />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-cursos/:cursoId/examenes/:examenId/rendir"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaRendirExamen />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-cursos/:id/examenes"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE, ROLES.ESTUDIANTE]}>
                <PaginaExamenesCursoPorRol />
              </RutaProtegida>
            }
          />
        </Routes>
      </Suspense>
    </Layout>
  )
}

// Componente exportado: punto de entrada del sistema de rutas.
// Envuelve todo en BrowserRouter (enrutado del lado del cliente),
// ProveedorAuth (contexto de autenticación) y Toaster (notificaciones).
export function Enrutador() {
  return (
    <BrowserRouter>
      <ProveedorAuth>
        <Suspense fallback={<CargandoPagina />}>
          <Routes>
            <Route path="/iniciar-sesion" element={<PaginaLogin />} />
            <Route path="/*" element={<RutasPrivadas />} />
          </Routes>
        </Suspense>
        <Toaster richColors position="top-right" />
      </ProveedorAuth>
    </BrowserRouter>
  )
}
