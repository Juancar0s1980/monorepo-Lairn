// Página de gestión de cursos Saber Pro del docente (HU-17).
//
// Ruta exclusiva del rol Docente (/saber-pro/cursos). Lista los cursos del
// docente, permite crear uno nuevo (HU-17.1/17.2) y, desde las tarjetas,
// seguir el ciclo completo de gestión: consultar/regenerar el código (HU-17.3),
// editar (HU-17.4), ver estudiantes (HU-17.5) y desactivar/eliminar (HU-17.6).
//
// Diseño institucional de portada (tokens de `paletaSaberPro`): banda beige ↔
// navy, franja superior navy→dorado→naranja, tipografías Inter/Montserrat.

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Plus, BookMarked, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { paletaSaberPro } from './utilidades'
import { ModalCrearCursoSaberPro } from './componentes/modal-crear-curso-saber-pro'
import { TarjetaCursoSaberPro } from './componentes/tarjeta-curso-saber-pro'

function SkeletonCursos() {
  return (
    <div aria-busy="true" aria-label="Cargando cursos Saber Pro" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className={`h-56 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-11 w-11 rounded-xl ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-4 w-2/3 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-3 h-3 w-4/5 rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

function ErrorCursos({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-2xl border p-12 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
        <AlertCircle className="h-6 w-6" />
      </span>
      <p className={`mt-4 text-sm font-medium ${paletaSaberPro.titulo}`}>{mensaje}</p>
      <Button type="button" className={`mt-4 ${paletaSaberPro.botonNeutro}`} onClick={reintentar}>
        Reintentar
      </Button>
    </div>
  )
}

export default function PaginaGestionCursosSaberPro() {
  const navigate = useNavigate()
  const { cursos, cargando, error, recargar } = useCursosSaberPro()
  const [modalCrearAbierto, setModalCrearAbierto] = useState(false)

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />
      <div className="relative p-6 md:p-10">
        {/* Encabezado: volver al panel + título + crear curso (HU-17.1) */}
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button
              type="button"
              onClick={() => navigate('/saber-pro')}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.accion}`}
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Volver al panel
            </button>
            <h1 className={`mt-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight ${paletaSaberPro.fuenteHero} ${paletaSaberPro.titulo}`}>
              Tus cursos <span className="text-[#e8740e] dark:text-[#F29A52]">Saber Pro</span>
            </h1>
            <p className={`mt-2 max-w-xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Crea cursos de preparación por área, comparte su código y gestiona a
              tus estudiantes desde un solo lugar.
            </p>
          </div>
          <Button
            type="button"
            className={`h-11 gap-2 px-5 font-bold shadow-md ${paletaSaberPro.botonAccion}`}
            onClick={() => setModalCrearAbierto(true)}
          >
            <Plus className="h-4 w-4" />
            Crear curso
          </Button>
        </header>

        <main className="mt-8">
          {cargando && <SkeletonCursos />}

          {!cargando && error && <ErrorCursos mensaje={error} reintentar={() => void recargar()} />}

          {!cargando && !error && (
            <>
              {/* Estado vacío de gestión: el docente aún no ha creado cursos (HU-17.1). */}
              {cursos.length === 0 && (
                <section
                  className={`flex flex-col items-center rounded-3xl border border-dashed p-12 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
                >
                  <span
                    className={`flex h-16 w-16 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}
                  >
                    <BookMarked className="h-8 w-8" />
                  </span>
                  <h2 className={`mt-4 text-lg font-bold ${paletaSaberPro.titulo}`}>
                    Aún no tienes cursos Saber Pro
                  </h2>
                  <p className={`mt-2 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>
                    Crea tu primer curso eligiendo el área de preparación y el
                    sistema generará el código de acceso automáticamente.
                  </p>
                  <Button
                    type="button"
                    className={`mt-5 gap-2 ${paletaSaberPro.botonAccion}`}
                    onClick={() => setModalCrearAbierto(true)}
                  >
                    <Plus className="h-4 w-4" />
                    Crear mi primer curso
                  </Button>
                </section>
              )}

              {/* Lista de cursos del docente (HU-17.1 crea, el resto gestiona). */}
              {cursos.length > 0 && (
                <section aria-labelledby="lista-cursos-saber-pro" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <h2 id="lista-cursos-saber-pro" className="sr-only">
                    Lista de cursos Saber Pro
                  </h2>
                  {cursos.map((curso) => (
                    <TarjetaCursoSaberPro
                      key={curso.id}
                      curso={curso}
                      onCursoActualizado={() => void recargar()}
                    />
                  ))}
                </section>
              )}
            </>
          )}
        </main>
      </div>

      <ModalCrearCursoSaberPro
        abierta={modalCrearAbierto}
        onCerrar={() => setModalCrearAbierto(false)}
        onCursoCreado={() => void recargar()}
      />
    </div>
  )
}