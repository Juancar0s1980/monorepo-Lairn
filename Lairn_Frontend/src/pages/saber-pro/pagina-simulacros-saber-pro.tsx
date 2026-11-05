// Pagina de simulacros del docente (HU-19).
//
// Ruta /saber-pro/simulacros. Permite elegir uno de los cursos del docente y
// gestionar sus simulacros: crear (HU-19.1/19.2), ver la distribucion y el
// estado, editar, activar/desactivar y eliminar (HU-19.4). El area siempre se
// hereda del curso y el sistema selecciona el contenido aprobado (HU-19.3).
//
// Identidad institucional del modulo: banda beige/navy, franja navy-dorado-
// naranja, Montserrat solo en el hero y tarjetas Shadcn sobre superficie.

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  ClipboardList,
  Loader2,
  Plus,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

import { toast } from 'sonner'
import api from '@/services/api'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { useSimulacrosSaberPro } from '@/hooks/use-simulacros-saber-pro'
import type { SimulacroSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerAncho } from './utilidades'
import { ModalRevisionSimulacroSaberPro } from './componentes/modal-revision-simulacro-saber-pro'
import { ModalPreguntasSimulacroSaberPro } from './componentes/modal-preguntas-simulacro-saber-pro'
import { ModalResultadosSimulacroSaberPro } from './componentes/modal-resultados-simulacro-saber-pro'
import { ModalSimulacroSaberPro } from './componentes/modal-simulacro-saber-pro'
import { TarjetaSimulacro } from './componentes/tarjeta-simulacro-saber-pro'


function SkeletonSimulacros() {
  return (
    <div aria-busy="true" aria-label="Cargando simulacros" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 3 }).map((_, indice) => (
        <div
          key={indice}
          className={`h-64 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-10 w-10 rounded-xl ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-4 w-2/3 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-14 w-full rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

function ErrorEstado({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
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

function mensajeDeError(error: unknown): string {
  const axiosError = error as { response?: { data?: { detalle?: string; errores?: string[] } } }
  const datos = axiosError.response?.data
  if (!datos) return 'No se pudo completar la operacion.'
  return [datos.detalle, ...(datos.errores ?? [])].filter(Boolean).join(' ') || 'No se pudo completar la operacion.'
}

export default function PaginaSimulacrosSaberPro() {
  const navigate = useNavigate()
  const { cursos, cargando: cargandoCursos, error: errorCursos, recargar: recargarCursos } = useCursosSaberPro()
  const [cursoId, setCursoId] = useState<number | null>(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [simulacroEnEdicion, setSimulacroEnEdicion] = useState<SimulacroSaberPro | null>(null)
  const [simulacroEnConsulta, setSimulacroEnConsulta] = useState<SimulacroSaberPro | null>(null)
  const [simulacroEnRevision, setSimulacroEnRevision] = useState<SimulacroSaberPro | null>(null)
  const [simulacroEnResultados, setSimulacroEnResultados] = useState<SimulacroSaberPro | null>(null)
  const [simulacroAEliminar, setSimulacroAEliminar] = useState<SimulacroSaberPro | null>(null)
  const [eliminando, setEliminando] = useState(false)
  const [procesandoId, setProcesandoId] = useState<number | null>(null)

  const cursoSeleccionado = cursos.find((curso) => curso.id === cursoId) ?? cursos[0] ?? null
  const { simulacros, cargando, error, recargar } = useSimulacrosSaberPro(cursoSeleccionado?.id ?? null)

  const totalActivos = simulacros.filter((simulacro) => simulacro.activo).length
  const totalAsignadas = simulacros.reduce((total, simulacro) => total + simulacro.total_preguntas, 0)

  const abrirCreacion = () => {
    if (!cursoSeleccionado) {
      toast.error('Primero crea un curso Saber Pro.')
      return
    }
    setSimulacroEnEdicion(null)
    setModalAbierto(true)
  }

  const abrirEdicion = (simulacro: SimulacroSaberPro) => {
    setSimulacroEnEdicion(simulacro)
    setModalAbierto(true)
  }

  const cambiarActivo = async (simulacro: SimulacroSaberPro) => {
    if (!cursoSeleccionado) return
    setProcesandoId(simulacro.id)
    try {
      await api.patch(
        `/saber-pro/docente/cursos/${cursoSeleccionado.id}/simulacros/${simulacro.id}/`,
        { activo: !simulacro.activo }
      )
      toast.success(simulacro.activo ? 'Simulacro desactivado' : 'Simulacro activado')
      await recargar()
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setProcesandoId(null)
    }
  }

  const eliminarSimulacro = async () => {
    if (!cursoSeleccionado || !simulacroAEliminar) return
    setEliminando(true)
    try {
      await api.delete(
        `/saber-pro/docente/cursos/${cursoSeleccionado.id}/simulacros/${simulacroAEliminar.id}/`
      )
      toast.success('Simulacro eliminado')
      setSimulacroAEliminar(null)
      await recargar()
    } catch (error) {
      toast.error(mensajeDeError(error))
    } finally {
      setEliminando(false)
    }
  }

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />

      <div className="relative p-6 md:p-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button
              type="button"
              onClick={() => navigate('/saber-pro')}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.accion}`}
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Volver al panel
            </button>
            <h1
              className={`mt-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight ${paletaSaberPro.fuenteHero} ${paletaSaberPro.titulo}`}
            >
              Simulacros <span className="text-[#e8740e] dark:text-[#F29A52]">Saber Pro</span>
            </h1>
            <p className={`mt-2 max-w-2xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Configura la evaluacion de cada curso y deja que el sistema seleccione preguntas aprobadas
              de tu banco segun la distribucion que definas.
            </p>
          </div>
          <Button
            type="button"
            className={`h-11 gap-2 px-5 font-bold shadow-md ${paletaSaberPro.botonAccion}`}
            onClick={abrirCreacion}
            disabled={!cursoSeleccionado}
          >
            <Plus className="h-4 w-4" /> Nuevo simulacro
          </Button>
        </header>

        {cargandoCursos && (
          <div className={`mt-8 flex items-center gap-2 text-sm ${paletaSaberPro.apoyo}`}>
            <Loader2 className="h-4 w-4 animate-spin" /> Cargando tus cursos...
          </div>
        )}

        {!cargandoCursos && errorCursos && (
          <div className="mt-8">
            <ErrorEstado mensaje={errorCursos} reintentar={() => void recargarCursos()} />
          </div>
        )}

        {!cargandoCursos && !errorCursos && cursos.length === 0 && (
          <section
            className={`mt-8 flex flex-col items-center rounded-3xl border border-dashed p-12 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
          >
            <span className={`flex h-16 w-16 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
              <BookOpen className="h-8 w-8" />
            </span>
            <h2 className={`mt-4 text-lg font-bold ${paletaSaberPro.titulo}`}>Necesitas un curso primero</h2>
            <p className={`mt-2 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Los simulacros heredan el area de un curso Saber Pro. Crea tu primer curso y vuelve a esta
              seccion para configurar la evaluacion.
            </p>
            <Button
              type="button"
              className={`mt-5 gap-2 ${paletaSaberPro.botonAccion}`}
              onClick={() => navigate('/saber-pro/cursos')}
            >
              <Plus className="h-4 w-4" /> Crear curso
            </Button>
          </section>
        )}

        {!cargandoCursos && !errorCursos && cursos.length > 0 && cursoSeleccionado && (
          <main className="mt-8">
            <section
              className={`rounded-2xl border p-4 md:p-5 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="w-full max-w-xl space-y-1.5">
                  <label htmlFor="curso-simulacros" className={`text-xs font-semibold ${paletaSaberPro.titulo}`}>
                    Curso Saber Pro
                  </label>
                  <Select
                    items={cursos.map((curso) => ({ value: String(curso.id), label: curso.nombre }))}
                    value={String(cursoSeleccionado.id)}
                    onValueChange={(valor) => setCursoId(Number(valor))}
                  >
                    <SelectTrigger id="curso-simulacros" className={selectTriggerAncho}>
                      <SelectValue placeholder="Selecciona un curso" />
                    </SelectTrigger>
                    <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                      {cursos.map((curso) => (
                        <SelectItem key={curso.id} value={String(curso.id)} className={selectItemLargo}>
                          {curso.nombre} - {curso.area.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                    {cursoSeleccionado.area.nombre}
                  </Badge>
                  <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                    {simulacros.length} simulacros
                  </Badge>
                  <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                    {totalActivos} activos
                  </Badge>
                  <Badge variant="outline" className={cn('text-[11px]', paletaSaberPro.badge)}>
                    {totalAsignadas} preguntas asignadas
                  </Badge>
                </div>
              </div>
            </section>

            <section aria-labelledby="lista-simulacros" className="mt-6">
              <div className="flex items-center gap-3">
                <span className={`h-6 w-1.5 rounded-full ${paletaSaberPro.separador}`} aria-hidden="true" />
                <div>
                  <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${paletaSaberPro.apoyoTitulo}`}>
                    Evaluaciones del curso
                  </p>
                  <h2 id="lista-simulacros" className={`mt-0.5 text-[22px] font-bold tracking-tight ${paletaSaberPro.titulo}`}>
                    Simulacros configurados
                  </h2>
                </div>
              </div>

              <div className="mt-5">
                {cargando && <SkeletonSimulacros />}

                {!cargando && error && <ErrorEstado mensaje={error} reintentar={() => void recargar()} />}

                {!cargando && !error && simulacros.length === 0 && (
                  <div
                    className={`flex flex-col items-center rounded-3xl border border-dashed p-10 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
                  >
                    <span className={`flex h-14 w-14 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                      <ClipboardList className="h-7 w-7" />
                    </span>
                    <h3 className={`mt-3 text-base font-bold ${paletaSaberPro.titulo}`}>
                      Este curso aun no tiene simulacros
                    </h3>
                    <p className={`mt-1.5 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>
                      Crea el primero indicando cuantas preguntas y cuanto tiempo tendra. Asegurate de
                      tener contenido aprobado en el banco del area.
                    </p>
                    <div className="mt-4 flex flex-wrap justify-center gap-2">
                      <Button type="button" className={`gap-2 ${paletaSaberPro.botonAccion}`} onClick={abrirCreacion}>
                        <Plus className="h-4 w-4" /> Crear simulacro
                      </Button>
                      <Button
                        type="button"
                        className={paletaSaberPro.botonNeutro}
                        onClick={() => navigate('/saber-pro/banco')}
                      >
                        Ir al banco de contenido
                      </Button>
                    </div>
                  </div>
                )}

                {!cargando && !error && simulacros.length > 0 && (
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {simulacros.map((simulacro) => (
                      <div key={simulacro.id} className={procesandoId === simulacro.id ? 'pointer-events-none opacity-60' : ''}>
                        <TarjetaSimulacro
                          simulacro={simulacro}
                          onVerPreguntas={setSimulacroEnConsulta}
                          onVerResultados={setSimulacroEnResultados}
                          onRevisar={setSimulacroEnRevision}
                          onEditar={abrirEdicion}
                          onEliminar={setSimulacroAEliminar}
                          onCambiarActivo={(item) => void cambiarActivo(item)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </main>
        )}
      </div>

      {cursoSeleccionado && (
        <>
          <ModalSimulacroSaberPro
            abierta={modalAbierto}
            curso={cursoSeleccionado}
            simulacro={simulacroEnEdicion}
            onCerrar={() => setModalAbierto(false)}
            onGuardado={() => void recargar()}
          />
          <ModalPreguntasSimulacroSaberPro
            abierta={Boolean(simulacroEnConsulta)}
            cursoId={cursoSeleccionado.id}
            simulacro={simulacroEnConsulta}
            onCerrar={() => setSimulacroEnConsulta(null)}
          />
          <ModalResultadosSimulacroSaberPro
            abierta={Boolean(simulacroEnResultados)}
            cursoId={cursoSeleccionado.id}
            simulacro={simulacroEnResultados}
            onCerrar={() => setSimulacroEnResultados(null)}
          />
          <ModalRevisionSimulacroSaberPro
            abierta={Boolean(simulacroEnRevision)}
            cursoId={cursoSeleccionado.id}
            simulacro={simulacroEnRevision}
            onCerrar={() => setSimulacroEnRevision(null)}
            onCambio={() => void recargar()}
          />
        </>
      )}

      <Dialog open={Boolean(simulacroAEliminar)} onOpenChange={(abre) => !abre && setSimulacroAEliminar(null)}>
        <DialogContent className={`max-w-[calc(100%-1.5rem)] sm:max-w-md ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}>
              <Trash2 className="h-5 w-5" />
            </span>
            <DialogTitle className={paletaSaberPro.titulo}>Eliminar simulacro</DialogTitle>
            <DialogDescription className={paletaSaberPro.texto}>
              Se eliminara &quot;{simulacroAEliminar?.titulo || 'este simulacro'}&quot; y sus preguntas
              asignadas. Esta accion no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <Button
              type="button"
              className={paletaSaberPro.botonNeutro}
              onClick={() => setSimulacroAEliminar(null)}
              disabled={eliminando}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              className="gap-2 bg-[#b8432a] text-white hover:bg-[#9d3722] dark:bg-[#F29A52] dark:text-[#172A45] dark:hover:bg-[#F7AC6B]"
              onClick={() => void eliminarSimulacro()}
              disabled={eliminando}
            >
              {eliminando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              {eliminando ? 'Eliminando...' : 'Eliminar'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
