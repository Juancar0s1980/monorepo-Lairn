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
import { LogoMarca } from '@/components/logo-marca'

// Lazy loading de todas las páginas.
// Cada import() genera un chunk separado que se descarga solo cuando se visita la ruta.
const PaginaLogin = lazy(() => import('@/pages/auth/pagina-login'))
const PaginaRecuperarContrasena = lazy(() => import('@/pages/auth/pagina-recuperar-contrasena'))
const PaginaRestablecerContrasena = lazy(() => import('@/pages/auth/pagina-restablecer-contrasena'))
const PaginaDashboardAdmin = lazy(() => import('@/pages/dashboard/pagina-dashboard-admin'))
const PaginaDashboardCoordinador = lazy(() => import('@/pages/dashboard/pagina-dashboard-coordinador'))
const PaginaDashboardDocente = lazy(() => import('@/pages/dashboard/pagina-dashboard-docente'))
const PaginaDashboardEstudiante = lazy(() => import('@/pages/dashboard/pagina-dashboard-estudiante'))
const PaginaUsuarios = lazy(() => import('@/pages/usuarios/pagina-usuarios'))
const PaginaExamenesCursoEstudiante = lazy(() => import('@/pages/examenes/pagina-examenes-curso-estudiante'))
const PaginaCursosDocente = lazy(() => import('@/pages/cursos/pagina-cursos-docente'))
const PaginaExamenesCursoDocente = lazy(() => import('@/pages/examenes/pagina-examenes-curso-docente'))
const PaginaRendirExamen = lazy(() => import('@/pages/examenes/pagina-rendir-examen'))
const PaginaCursosEstudiante = lazy(() => import('@/pages/cursos/pagina-cursos-estudiante'))
const PaginaExamenesAdmin = lazy(() => import('@/pages/examenes/pagina-examenes-admin'))
const PaginaAnaliticaAdmin = lazy(() => import('@/pages/analitica/pagina-analitica-admin'))
const PaginaModeracionAdmin = lazy(() => import('@/pages/moderacion/pagina-moderacion-admin'))
const PaginaRedesAdmin = lazy(() => import('@/pages/redes/pagina-redes-admin'))
const PaginaAcademicoAdmin = lazy(() => import('@/pages/academico/pagina-academico'))
const PaginaEditorLaboratorioDocente = lazy(() => import('@/pages/laboratorios/pagina-editor-laboratorio-docente'))
const PaginaResolverLaboratorioEstudiante = lazy(() => import('@/pages/laboratorios/pagina-resolver-laboratorio-estudiante'))
const PaginaTemaEstudioEstudiante = lazy(() => import('@/pages/examenes/pagina-tema-estudio-estudiante'))
const PaginaPanelSaberPro = lazy(() => import('@/pages/saber-pro/pagina-panel-saber-pro'))
const PaginaGestionCursosSaberPro = lazy(() => import('@/pages/saber-pro/pagina-gestion-cursos-saber-pro'))
const PaginaBancoContenidoSaberPro = lazy(() => import('@/pages/saber-pro/pagina-banco-contenido-saber-pro'))
const PaginaReporteInstitucional = lazy(() => import('@/pages/reporte/pagina-reporte-institucional'))
const PaginaEvaluacionesEstudiante = lazy(() => import('@/pages/evaluaciones/pagina-evaluaciones-estudiante'))
const PaginaPresentarEvaluacion = lazy(() => import('@/pages/evaluaciones/pagina-presentar-evaluacion'))
const PaginaTareasDocente = lazy(() => import('@/pages/tareas/pagina-tareas-docente'))
const PaginaTareasEstudiante = lazy(() => import('@/pages/tareas/pagina-tareas-estudiante'))
const PaginaTareaEstudiante = lazy(() => import('@/pages/tareas/pagina-tarea-estudiante'))
const PaginaEvaluacionFormal = lazy(() => import('@/pages/academico/pagina-evaluacion-formal'))
const PaginaEstudiantes = lazy(() => import('@/pages/estudiantes/pagina-estudiantes'))
const PaginaAyuda = lazy(() => import('@/pages/ayuda/pagina-ayuda'))
const PaginaNotasMomento = lazy(() => import('@/pages/notas-momento/pagina-notas-momento'))
const PaginaGuiaAyuda = lazy(() => import('@/pages/ayuda/pagina-guia-ayuda'))
const PaginaSupervision = lazy(() => import('@/pages/supervision/pagina-supervision'))
const PaginaLlamadoLista = lazy(() => import('@/pages/supervision/pagina-llamado-lista'))
const PaginaBancoPreguntasDocente = lazy(() => import('@/pages/banco-preguntas/pagina-banco-preguntas-docente'))
const PaginaSimulacrosSaberPro = lazy(() => import('@/pages/saber-pro/pagina-simulacros-saber-pro'))
const PaginaSimulacrosEstudianteSaberPro = lazy(
  () => import('@/pages/saber-pro/pagina-simulacros-estudiante-saber-pro')
)
const PaginaPresentarSimulacroSaberPro = lazy(
  () => import('@/pages/saber-pro/pagina-presentar-simulacro-saber-pro')
)
const PaginaRankingSaberPro = lazy(
  () => import('@/pages/saber-pro/pagina-ranking-saber-pro')
)
const PaginaDesempenoEstudianteSaberPro = lazy(
  () => import('@/pages/saber-pro/pagina-desempeno-estudiante-saber-pro')
)

// Fallback de carga mostrado mientras se descarga el chunk de una página.
function CargandoPagina() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 animate-pulse">
          <LogoMarca className="h-6 w-6 text-primary" />
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
  // ADR-013: el Coordinador tiene su propio inicio con datos reales de sus programas.
  if (rol === ROLES.COORDINADOR) return <PaginaDashboardCoordinador />
  // El Vicerrector solo consulta el reporte institucional (HU-11).
  if (rol === ROLES.VICERRECTOR) return <Navigate to="/reporte-institucional" replace />
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

// Selector por rol para un Laboratorio: Docente edita preguntas, Estudiante las resuelve.
function PaginaLaboratorioPorRol() {
  const { rol } = useAuth()

  if (rol === ROLES.DOCENTE) return <PaginaEditorLaboratorioDocente />
  if (rol === ROLES.ESTUDIANTE) return <PaginaResolverLaboratorioEstudiante />
  return <Navigate to="/" replace />
}

// Selector por rol para Simulacros: Docente gestiona, Estudiante consulta los publicados.
function PaginaSimulacrosSaberProPorRol() {
  const { rol } = useAuth()

  if (rol === ROLES.DOCENTE) return <PaginaSimulacrosSaberPro />
  if (rol === ROLES.ESTUDIANTE) return <PaginaSimulacrosEstudianteSaberPro />
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
            path="/examenes"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN]}>
                <PaginaExamenesAdmin />
              </RutaProtegida>
            }
          />
          <Route
            path="/analitica"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN]}>
                <PaginaAnaliticaAdmin />
              </RutaProtegida>
            }
          />
          <Route
            path="/moderacion"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN]}>
                <PaginaModeracionAdmin />
              </RutaProtegida>
            }
          />
          <Route
            path="/redes"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN]}>
                <PaginaRedesAdmin />
              </RutaProtegida>
            }
          />
          <Route
            path="/saber-pro"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE, ROLES.ESTUDIANTE]}>
                <PaginaPanelSaberPro />
              </RutaProtegida>
            }
          />
          {/* HU-17: gestión de cursos Saber Pro, exclusiva del docente.
              El estudiante no crea cursos: solo se inscribe por código (HU-18). */}
          <Route
            path="/saber-pro/cursos"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaGestionCursosSaberPro />
              </RutaProtegida>
            }
          />
          {/* HU-20: banco de contenido generado con IA, exclusivo del docente. */}
          <Route
            path="/saber-pro/banco"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaBancoContenidoSaberPro />
              </RutaProtegida>
            }
          />
          {/* HU-11: reporte ejecutivo institucional (solo lectura). */}
          <Route
            path="/reporte-institucional"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN, ROLES.VICERRECTOR, ROLES.COORDINADOR]}>
                <PaginaReporteInstitucional />
              </RutaProtegida>
            }
          />
          {/* HU-07: el estudiante presenta la evaluación formal publicada. */}
          <Route
            path="/mis-evaluaciones"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaEvaluacionesEstudiante />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-evaluaciones/:evaluacionId"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaPresentarEvaluacion />
              </RutaProtegida>
            }
          />
          {/* ADR-012: convocados e inscritos (Admin/Coordinador: todos; Docente: sus cursos y supervisiones). */}
          <Route
            path="/notas-momento"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN, ROLES.COORDINADOR, ROLES.VICERRECTOR]}>
                <PaginaNotasMomento />
              </RutaProtegida>
            }
          />
          <Route
            path="/ayuda"
            element={
              <RutaProtegida>
                <PaginaAyuda />
              </RutaProtegida>
            }
          />
          <Route
            path="/ayuda/:slug"
            element={
              <RutaProtegida>
                <PaginaGuiaAyuda />
              </RutaProtegida>
            }
          />
          <Route
            path="/estudiantes"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN, ROLES.COORDINADOR, ROLES.DOCENTE]}>
                <PaginaEstudiantes />
              </RutaProtegida>
            }
          />
          {/* ADR-009: el docente supervisor hace el llamado a lista en sala. */}
          <Route
            path="/supervision"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaSupervision />
              </RutaProtegida>
            }
          />
          <Route
            path="/supervision/:evaluacionId"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaLlamadoLista />
              </RutaProtegida>
            }
          />
          {/* HU-08B / HU-08A: tareas prácticas con rúbrica (docente crea y califica, estudiante entrega). */}
          <Route
            path="/tareas"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaTareasDocente />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-tareas"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaTareasEstudiante />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-tareas/:tareaId"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaTareaEstudiante />
              </RutaProtegida>
            }
          />
          {/* HU-06: ensamblado de la evaluación formal de un momento. */}
          <Route
            path="/academico/momentos/:momentoId/evaluaciones"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN, ROLES.COORDINADOR]}>
                <PaginaEvaluacionFormal />
              </RutaProtegida>
            }
          />
          {/* Módulo 2 (HU-04/05): banco de preguntas por RA, exclusivo del docente. */}
          <Route
            path="/banco-preguntas"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaBancoPreguntasDocente />
              </RutaProtegida>
            }
          />
          {/* HU-19: simulacros del curso, con vista distinta por rol. */}
          <Route
            path="/saber-pro/simulacros"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE, ROLES.ESTUDIANTE]}>
                <PaginaSimulacrosSaberProPorRol />
              </RutaProtegida>
            }
          />
          {/* HU-21: presentación cronometrada de un simulacro, solo estudiante. */}
          <Route
            path="/saber-pro/simulacros/:simulacroId/presentar"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaPresentarSimulacroSaberPro />
              </RutaProtegida>
            }
          />
          {/* HU-23: ranking nominal del curso, exclusivo del docente propietario. */}
          <Route
            path="/saber-pro/ranking"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE]}>
                <PaginaRankingSaberPro />
              </RutaProtegida>
            }
          />
          {/* HU-23: percentil y agregados propios del estudiante, sin datos de terceros. */}
          <Route
            path="/saber-pro/desempeno"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaDesempenoEstudianteSaberPro />
              </RutaProtegida>
            }
          />
          <Route
            path="/academico"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ADMIN, ROLES.COORDINADOR]}>
                <PaginaAcademicoAdmin />
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
          <Route
            path="/mis-cursos/:cursoId/laboratorios/:laboratorioId"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.DOCENTE, ROLES.ESTUDIANTE]}>
                <PaginaLaboratorioPorRol />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-cursos/:cursoId/campo-estudio/:temaId"
            element={
              <RutaProtegida rolesPermitidos={[ROLES.ESTUDIANTE]}>
                <PaginaTemaEstudioEstudiante />
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
            <Route path="/recuperar-contrasena" element={<PaginaRecuperarContrasena />} />
            <Route path="/restablecer-contrasena/:uid/:token" element={<PaginaRestablecerContrasena />} />
            <Route path="/*" element={<RutasPrivadas />} />
          </Routes>
        </Suspense>
        <Toaster richColors position="top-right" />
      </ProveedorAuth>
    </BrowserRouter>
  )
}
