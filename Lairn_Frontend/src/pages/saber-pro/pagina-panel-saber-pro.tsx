// Panel principal del módulo Saber Pro (HU-16).
//
// Punto de entrada propio del módulo: NO depende de estar inscrito o tener
// un curso académico regular (HU-16.2). Muestra:
//
//   1. Hero institucional de marca (montserrat + sello) con las áreas de
//      Saber Pro como contexto.
//   2. Estado vacío (HU-16.3) cuando el usuario aún no tiene cursos Saber Pro:
//      el docente es invitado a "Crear curso" (navega a /saber-pro/cursos,
//      HU-17) y el estudiante a "Unirme con código" (abre el modal de
//      inscripción por código, HU-18).
//   3. "Mis cursos de preparación" cuando el usuario sí tiene cursos: el
//      docente ve sus cursos con el código vigente (HU-17) y el estudiante los
//      cursos a los que se unió con su fecha de ingreso (HU-18.3).
//   4. "Cómo funciona" (pasos según el rol) que le enseña al usuario a empezar.
//   5. "Lo que puedes explorar": avances de las herramientas del módulo
//      (HU-19 a HU-24), todas marcadas como "Próximamente".
//
// El diseño es una PORTADA institucional propia, deliberadamente distinta al
// resto de la app: banda beige con franja navy→dorado→naranja, título de marca
// en Montserrat 900, sello circular navy/dorado y capas de bandas alternas.
// Ambos temas (claro y oscuro) comparten la misma estructura y roles de color
// simétricos (ver ./utilidades.ts); la tipografía sigue las reglas
// institucionales: Inter para texto y títulos de sección, Montserrat 800-900
// para la marca.

import '@fontsource/montserrat/800.css'
import '@fontsource/montserrat/900.css'

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, GraduationCap, CheckCircle2, ArrowRight, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { usePanelSaberPro } from '@/hooks/use-panel-saber-pro'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import type { CursoSaberPro, FuncionalidadSaberPro } from '@/types/saber-pro'
import { paletaSaberPro, AREAS_SABER_PRO, obtenerPasosInicio } from './utilidades'
import { TarjetaFuncionalidad } from './componentes/tarjeta-funcionalidad'
import { EstadoVacioSaberPro } from './componentes/estado-vacio-saber-pro'
import { ModalUnirseCursoSaberPro } from './componentes/modal-unirse-curso-saber-pro'
import { SeccionCursosEstudianteSaberPro } from './componentes/seccion-cursos-estudiante-saber-pro'

function SkeletonPanel() {
  return (
    <div aria-busy="true" aria-label="Cargando panel de Saber Pro">
      <div className="animate-pulse space-y-2">
        <div className={`h-4 w-48 rounded ${paletaSaberPro.esqueleto}`} />
        <div className={`h-14 w-72 max-w-full rounded ${paletaSaberPro.esqueleto}`} />
        <div className={`h-4 w-96 max-w-full rounded ${paletaSaberPro.esqueleto}`} />
      </div>
      <div className={`mt-8 h-64 rounded-3xl ${paletaSaberPro.bandaProfunda}`} />
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className={`h-40 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
          >
            <div className={`mx-5 mt-5 h-10 w-10 rounded-xl ${paletaSaberPro.esqueleto}`} />
            <div className={`mx-5 mt-3 h-4 w-32 rounded ${paletaSaberPro.esqueleto}`} />
            <div className={`mx-5 mt-2 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          </div>
        ))}
      </div>
    </div>
  )
}

function ErrorPanel({ error }: { error: string | null }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border p-12 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
        <AlertCircle className="h-6 w-6" />
      </span>
      <p className={`mt-4 text-sm font-medium ${paletaSaberPro.apoyo}`}>
        {error ?? 'No se pudo cargar el panel de Saber Pro.'}
      </p>
    </div>
  )
}

// Sello circular institucional: navy con dorado (claro) ↔ crema con navy (oscuro),
// con doble anillo (punteado + fino) que evoca una estampilla oficial de examen.
function SelloSaberPro() {
  return (
    <div className="relative hidden h-40 w-40 shrink-0 items-center justify-center lg:flex" aria-hidden="true">
      <div className="absolute inset-0 rounded-full border-2 border-dashed border-[#c89b14]/50 dark:border-[#E3C063]/50" />
      <div className="absolute inset-2.5 rounded-full border border-[#1e3a5f]/15 dark:border-[#F3EDE1]/15" />
      <div className={`absolute inset-5 rounded-full bg-radial from-[#c89b14]/20 to-transparent dark:from-[#E3C063]/15`} />
      <div
        className={`relative flex h-24 w-24 flex-col items-center justify-center gap-1 rounded-full shadow-lg ${paletaSaberPro.sello}`}
      >
        <GraduationCap className="h-9 w-9" />
        <span className="text-[9px] font-bold uppercase tracking-[0.18em]">Saber Pro</span>
      </div>
    </div>
  )
}

// Hero institucional del módulo: marca en Montserrat + sellos y chips de áreas.
function HeroPanel() {
  return (
    <header className="relative flex flex-col gap-10 lg:flex-row lg:items-center lg:justify-between">
      <div className="max-w-2xl">
        <p
          className={`flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}
        >
          <span className={`h-px w-8 ${paletaSaberPro.separador}`} aria-hidden="true" />
          Módulo de preparación
        </p>
        <h1
          className={`mt-4 text-[clamp(2.75rem,6vw,4.5rem)] leading-[0.98] tracking-tight text-balance ${paletaSaberPro.titulo} ${paletaSaberPro.fuenteHero}`}
        >
          Saber{' '}
          <span className="text-[#e8740e] dark:text-[#F29A52]">Pro</span>
        </h1>
        <p className={`mt-5 max-w-prose text-base leading-relaxed ${paletaSaberPro.texto}`}>
          Bienvenido al modulo de preparacion para las pruebas Saber Pro: simulacros con temporizador, banco de contenido
          generado con IA y analítica de desempeño.
        </p>

        {/* Áreas Saber Pro como contexto del módulo (HUs 17-20) */}
        <div className="mt-7 flex flex-wrap items-center gap-2">
          {AREAS_SABER_PRO.map((area) => (
            <span
              key={area}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-medium ${paletaSaberPro.superficie} ${paletaSaberPro.borde} ${paletaSaberPro.titulo}`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
              {area}
            </span>
          ))}
        </div>
      </div>
      <SelloSaberPro />
    </header>
  )
}

// "Cómo funciona": pasos de inicio según el rol, bajo el estado vacío (HU-16.3).
function SeccionPasos({ rol }: { rol: string }) {
  const pasos = obtenerPasosInicio(rol)
  return (
    <section aria-labelledby="pasos-saber-pro" className="mt-12">
      <div className="flex items-center gap-3">
        <span className={`h-6 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
        <div>
          <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}>
            Cómo funciona
          </p>
          <h2
            id="pasos-saber-pro"
            className={`mt-0.5 text-[22px] font-bold tracking-tight ${paletaSaberPro.titulo}`}
          >
            Da tus primeros pasos
          </h2>
        </div>
      </div>

      <div className="relative mt-6 grid gap-5 sm:grid-cols-3">
        {/* Línea conectora entre pasos (decorativa, se oculta en móvil) */}
        <div
          aria-hidden="true"
          className="absolute left-[16.66%] right-[16.66%] top-7 hidden h-px bg-gradient-to-r from-[#c89b14]/50 via-[#e8740e]/50 to-[#c89b14]/50 sm:block dark:from-[#E3C063]/50 dark:via-[#F29A52]/50 dark:to-[#E3C063]/50"
        />
        {pasos.map((paso, indice) => (
          <div
            key={paso.titulo}
            className={`relative flex flex-col gap-3 rounded-2xl border p-5 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
          >
            <span
              className={`flex h-11 w-11 items-center justify-center rounded-full text-sm font-bold shadow-sm ${paletaSaberPro.numeracionPaso}`}
            >
              {indice + 1}
            </span>
            <h3 className={`text-sm font-bold ${paletaSaberPro.titulo}`}>{paso.titulo}</h3>
            <p className={`text-xs leading-relaxed ${paletaSaberPro.apoyo}`}>{paso.descripcion}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

// Avances de las herramientas del módulo (HU-19 a HU-24), como tarjetas "Próximamente".
function SeccionFuncionalidades({
  rol,
  funcionalidades,
  onAccionPorClave,
}: {
  rol: string
  funcionalidades: FuncionalidadSaberPro[]
  onAccionPorClave?: (clave: string) => void
}) {
  if (funcionalidades.length === 0) return null
  return (
    <section aria-labelledby="herramientas-saber-pro" className="mt-12">
      <div className="flex items-center gap-3">
        <span className={`h-6 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
        <div>
          <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}>
            Lo que puedes explorar
          </p>
          <h2
            id="herramientas-saber-pro"
            className={`mt-0.5 text-[22px] font-bold tracking-tight ${paletaSaberPro.titulo}`}
          >
            Herramientas para {rol.toLowerCase()}
          </h2>
        </div>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {funcionalidades.map((funcionalidad) => (
          <TarjetaFuncionalidad
            key={funcionalidad.clave}
            funcionalidad={funcionalidad}
            onAccion={onAccionPorClave ? () => onAccionPorClave(funcionalidad.clave) : undefined}
          />
        ))}
      </div>
    </section>
  )
}

// Nota de independencia del módulo (HU-16.2): no requiere curso académico previo.
function NotaAccesoLibre({ rol }: { rol: string }) {
  return (
    <div
      className={`mt-10 flex flex-col gap-4 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between sm:gap-5 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${paletaSaberPro.chipAccion}`}
        >
          <GraduationCap className="h-6 w-6" />
        </span>
        <div>
          <h3 className={`font-bold ${paletaSaberPro.titulo}`}>Acceso sin curso académico</h3>
          <p className={`mt-1 text-sm leading-relaxed ${paletaSaberPro.texto}`}>
            Este módulo se habilita para tu rol ({rol.toLowerCase()}) sin necesidad de estar
            inscrito en una asignatura o programa académico específico.
          </p>
        </div>
      </div>
      <Badge
        variant="outline"
        className={`h-7 shrink-0 gap-1.5 self-start px-3 sm:self-center ${paletaSaberPro.badge}`}
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
        Módulo independiente
      </Badge>
    </div>
  )
}

// Contenido visible cuando el usuario YA tiene cursos Saber Pro (HU-17/18).
// Para el docente muestra sus cursos reales con el código vigente y un acceso
// completo a la gestión (HU-17); para el estudiante, los cursos a los que se
// unió con el código (HU-18.3) más la acción de unirse a otro curso (HU-18),
// que debe seguir disponible aunque ya pertenezca a uno.
function SeccionMisCursosSaberPro({
  rol,
  onUnirse,
  claveLista,
}: {
  rol: string
  onUnirse: () => void
  claveLista: number
}) {
  const navigate = useNavigate()
  const esDocente = rol === 'Docente'

  return (
    <section
      aria-labelledby="mis-cursos-saber-pro"
      className={`mt-10 rounded-3xl border p-6 md:p-8 ${paletaSaberPro.bandaProfunda} ${paletaSaberPro.borde}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.iconoChip}`}>
            <GraduationCap className="h-6 w-6" />
          </span>
          <div>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}>
              Mis cursos de preparación
            </p>
            <h2
              id="mis-cursos-saber-pro"
              className={`mt-0.5 text-xl font-bold ${paletaSaberPro.titulo}`}
            >
              {esDocente ? 'Tus cursos Saber Pro' : 'Tus cursos de preparación'}
            </h2>
          </div>
        </div>
        {esDocente ? (
          <Button
            type="button"
            className={`h-10 gap-2 px-4 font-bold ${paletaSaberPro.botonAccion}`}
            onClick={() => navigate('/saber-pro/cursos')}
          >
            Gestionar cursos
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            type="button"
            className={`h-10 gap-2 px-4 font-bold ${paletaSaberPro.botonAccion}`}
            onClick={onUnirse}
          >
            Unirme con un código
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {esDocente ? (
        <ListaCursosDocente />
      ) : (
        <SeccionCursosEstudianteSaberPro key={claveLista} />
      )}
    </section>
  )
}

// Listado compacto de los cursos del docente dentro del panel (HU-17): fila con
// nombre, área y código vigente, accesible desde "Gestionar cursos".
function ListaCursosDocente() {
  const { cursos, cargando } = useCursosSaberPro()

  if (cargando) {
    return (
      <div aria-busy="true" className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className={`h-24 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`} />
        ))}
      </div>
    )
  }

  return (
    <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {cursos.slice(0, 3).map((curso: CursoSaberPro) => (
        <li
          key={curso.id}
          className={`flex items-center gap-3 rounded-2xl border p-4 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${paletaSaberPro.chipGold}`}>
            <GraduationCap className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <p className={`truncate text-sm font-bold ${paletaSaberPro.titulo}`}>{curso.nombre}</p>
            <p className={`truncate text-xs ${paletaSaberPro.apoyo}`}>{curso.area.nombre}</p>
          </div>
          <Badge
            variant="outline"
            className={`ml-auto shrink-0 font-mono tracking-[0.18em] ${paletaSaberPro.badge}`}
          >
            {curso.codigo}
          </Badge>
        </li>
      ))}
    </ul>
  )
}

export default function PaginaPanelSaberPro() {
  const { panel, cargando, error, recargar } = usePanelSaberPro()
  const navigate = useNavigate()
  const [modalAbierto, setModalAbierto] = useState(false)
  const esDocente = panel?.rol === 'Docente'
  // Incrementa al inscribirse para remontar la lista del estudiante y que
  // recargue los cursos (escasez de refresco cuando ya estaba en la vista).
  const [claveLista, setClaveLista] = useState(0)

  // Tras unirse exitosamente, refresca el panel: `tiene_cursos` pasa a true y
  // se monta la sección de cursos del estudiante (HU-18.3); si ya estaba montada
  // (se une a un segundo curso), la `claveLista` fuerza su recarga.
  const onInscripcionExitosa = () => {
    setModalAbierto(false)
    setClaveLista((c) => c + 1)
    void recargar()
  }

  // Navegación de las herramientas del panel que ya están disponibles. Por ahora
  // solo el banco de contenido (HU-20); las demás siguen "Próximamente".
  const manejarAccionFuncionalidad = (clave: string) => {
    if (clave === 'banco_contenido') {
      navigate('/saber-pro/banco')
    }
  }

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      {/* Halos decorativos de la portada institucional */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-radial from-[#1e3a5f]/10 to-transparent dark:from-[#F3EDE1]/8"
      />

      {/* Franja institucional superior: navy → dorado → naranja */}
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />
      <div className="relative p-6 md:p-10">
        {cargando && <SkeletonPanel />}
        {error && <ErrorPanel error={error} />}
        {!error && panel && (
          <>
            <HeroPanel />
            {panel.tiene_cursos ? (
              <SeccionMisCursosSaberPro
                rol={panel.rol}
                onUnirse={() => setModalAbierto(true)}
                claveLista={claveLista}
              />
            ) : (
              <>
                <EstadoVacioSaberPro
                  accion={panel.accion_vacia}
                  onAccion={
                    // HU-17: el docente salta directo a la gestión de cursos;
                    // HU-18: el estudiante abre el modal de inscripción por código.
                    esDocente
                      ? () => navigate('/saber-pro/cursos')
                      : () => setModalAbierto(true)
                  }
                />
                <SeccionPasos rol={panel.rol} />
              </>
            )}
            <SeccionFuncionalidades
              rol={panel.rol}
              funcionalidades={panel.funcionalidades}
              onAccionPorClave={manejarAccionFuncionalidad}
            />
            <NotaAccesoLibre rol={panel.rol} />
          </>
        )}
      </div>

      {/* HU-18: inscripción del estudiante por código de acceso */}
      <ModalUnirseCursoSaberPro
        abierta={modalAbierto}
        onCerrar={() => setModalAbierto(false)}
        onInscripcionExitosa={onInscripcionExitosa}
      />
    </div>
  )
}