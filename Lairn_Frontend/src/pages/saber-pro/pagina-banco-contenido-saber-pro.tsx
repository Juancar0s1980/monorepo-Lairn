// Página del banco de contenido Saber Pro, para el rol Docente (HU-20).
//
// Punto de trabajo para generar y curar el contenido con IA por área:
//
//   1. El docente elige uno de sus cursos Saber Pro; el banco que se muestra es
//      el de su área (el banco es del docente + área, compartido entre sus
//      cursos de la misma área).
//   2. "Generar contenido" abre el modal que arma los criterios según la
//      estructura del área (HU-20.1/20.2).
//   3. Pestañas separan "Pendientes" y "Aprobados". Se agregan filtros por
//      competencia, afirmación, evidencia o parte (Inglés) para revisar más
//      ordenado y ágilmente. Diseño responsive y modular.

import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, BookMarked, GraduationCap, Plus, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { useContenidoBancoSaberPro } from '@/hooks/use-contenido-banco-saber-pro'
import { useCriteriosAreaSaberPro } from '@/hooks/use-criterios-area-saber-pro'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerLargo } from './utilidades'
import { TarjetaContenidoSaberPro } from './componentes/tarjeta-contenido-saber-pro'
import { ModalGenerarContenidoSaberPro } from './componentes/modal-generar-contenido-saber-pro'
import { FiltrosBancoContenido } from './componentes/filtros-banco-contenido'
import { PaginacionBancoContenido } from './componentes/paginacion-banco-contenido'

const ELEMENTOS_POR_PAGINA = 9

function SkeletonBanco() {
  return (
    <div aria-busy="true" aria-label="Cargando banco de contenido" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className={`h-56 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-4 w-24 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-3 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-4/5 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-6 h-8 w-32 rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

function EstadoVacioBanco({ titulo, detalle, icono }: { titulo: string; detalle: string; icono: ReactNode }) {
  return (
    <div className={`flex flex-col items-center rounded-3xl border border-dashed p-10 text-center sm:p-12 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}>
      <span className={`flex h-16 w-16 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
        {icono}
      </span>
      <h2 className={`mt-4 text-lg font-bold ${paletaSaberPro.titulo}`}>{titulo}</h2>
      <p className={`mt-2 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>{detalle}</p>
    </div>
  )
}

export default function PaginaBancoContenidoSaberPro() {
  const navigate = useNavigate()
  const { cursos, cargando: cargandoCursos, error: errorCursos } = useCursosSaberPro()

  const [cursoIdSeleccionado, setCursoIdSeleccionado] = useState<number | null>(null)
  const [modalGenerarAbierto, setModalGenerarAbierto] = useState(false)
  const [pestanaActiva, setPestanaActiva] = useState('pendientes')
  const [competenciaId, setCompetenciaId] = useState<number | null>(null)
  const [afirmacionId, setAfirmacionId] = useState<number | null>(null)
  const [evidenciaId, setEvidenciaId] = useState<number | null>(null)
  const [parte, setParte] = useState<number | null>(null)
  const [pagina, setPagina] = useState(1)

  const cursoId = cursoIdSeleccionado ?? cursos[0]?.id ?? null
  const curso = useMemo(() => cursos.find((c) => c.id === cursoId) ?? null, [cursos, cursoId])
  const { criterios } = useCriteriosAreaSaberPro(curso?.area.id ?? null)

  const filtros = useMemo(
    () => ({
      competenciaId,
      afirmacionId,
      evidenciaId,
      parte,
    }),
    [afirmacionId, competenciaId, evidenciaId, parte]
  )

  const { contenidos, cargando, error, recargar } = useContenidoBancoSaberPro(cursoId, filtros)
  const tipoEstructura = criterios?.tipo_estructura ?? (curso?.area.nombre === 'Inglés' ? 'partes' : curso?.area.nombre === 'Comunicación Escrita' ? 'consigna' : 'competencias')

  useEffect(() => {
    setCompetenciaId(null)
    setAfirmacionId(null)
    setEvidenciaId(null)
    setParte(null)
    setPestanaActiva('pendientes')
    setPagina(1)
  }, [cursoId])

  useEffect(() => {
    setPagina(1)
  }, [pestanaActiva, competenciaId, afirmacionId, evidenciaId, parte])

  const pendientes = useMemo(() => contenidos.filter((c) => c.estado === 'pendiente'), [contenidos])
  const aprobados = useMemo(() => contenidos.filter((c) => c.estado === 'aprobado'), [contenidos])
  const listaActual = pestanaActiva === 'pendientes' ? pendientes : aprobados
  const totalElementos = listaActual.length
  const totalPaginas = Math.max(1, Math.ceil(totalElementos / ELEMENTOS_POR_PAGINA))
  const paginaSegura = Math.min(pagina, totalPaginas)
  const listaPaginada = useMemo(
    () => listaActual.slice((paginaSegura - 1) * ELEMENTOS_POR_PAGINA, paginaSegura * ELEMENTOS_POR_PAGINA),
    [listaActual, paginaSegura]
  )

  const limpiarFiltros = () => {
    setCompetenciaId(null)
    setAfirmacionId(null)
    setEvidenciaId(null)
    setParte(null)
    setPagina(1)
  }

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />
      <div className="relative p-4 sm:p-6 md:p-10">
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
            <h1 className={`mt-3 flex items-center gap-3 text-[clamp(1.9rem,4vw,2.8rem)] font-black leading-tight tracking-tight ${paletaSaberPro.fuenteHero} ${paletaSaberPro.titulo}`}>
              Banco de <span className="text-[#e8740e] dark:text-[#F29A52]">contenido</span>
            </h1>
            <p className={`mt-2 max-w-2xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Genera preguntas y consignas con IA, revísalas por pestañas y filtra por competencia, afirmación, evidencia o parte para aprobarlas más rápido y ordenado.
            </p>
          </div>
          {curso && (
            <Button
              type="button"
              className={`h-11 gap-2 px-5 font-bold shadow-md ${paletaSaberPro.botonAccion}`}
              onClick={() => setModalGenerarAbierto(true)}
            >
              <Plus className="h-4 w-4" />
              Generar contenido
            </Button>
          )}
        </header>

        <main className="mt-8 space-y-6">
          {!cargandoCursos && !errorCursos && cursos.length === 0 && (
            <EstadoVacioBanco
              titulo="Aún no tienes cursos Saber Pro"
              detalle="El banco de contenido se genera desde un curso del docente. Crea tu primer curso para empezar a preparar material."
              icono={<BookMarked className="h-8 w-8" />}
            />
          )}

          {(cargandoCursos || errorCursos) && (
            <>
              {cargandoCursos && <SkeletonBanco />}
              {errorCursos && (
                <div className={`flex flex-col items-center rounded-2xl border p-12 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}>
                  <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                    <AlertCircle className="h-6 w-6" />
                  </span>
                  <p className={`mt-4 text-sm font-medium ${paletaSaberPro.titulo}`}>{errorCursos}</p>
                </div>
              )}
            </>
          )}

          {cursos.length > 0 && (
            <>
              <div className="max-w-md space-y-1.5">
                <Label className={`${paletaSaberPro.titulo}`}>Curso</Label>
                <Select
                  items={cursos.map((c) => ({ value: String(c.id), label: `${c.nombre} · ${c.area.nombre}` }))}
                  value={cursoId ? String(cursoId) : ''}
                  onValueChange={(valor) => setCursoIdSeleccionado(Number(valor))}
                >
                  <SelectTrigger className={selectTriggerLargo}>
                    <SelectValue placeholder="Selecciona un curso" />
                  </SelectTrigger>
                  <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                    {cursos.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)} className={selectItemLargo}>
                        {c.nombre} — {c.area.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {curso && (
                  <p className={`flex items-center gap-1.5 text-xs ${paletaSaberPro.apoyo}`}>
                    <GraduationCap className="h-3.5 w-3.5" />
                    El banco es del área <strong>{curso.area.nombre}</strong>: se comparte entre tus cursos de esa área.
                  </p>
                )}
              </div>

              {curso && (
                <FiltrosBancoContenido
                  criterios={criterios}
                  tipoEstructura={tipoEstructura}
                  competenciaId={competenciaId}
                  afirmacionId={afirmacionId}
                  evidenciaId={evidenciaId}
                  parte={parte}
                  onCompetenciaChange={setCompetenciaId}
                  onAfirmacionChange={setAfirmacionId}
                  onEvidenciaChange={setEvidenciaId}
                  onParteChange={setParte}
                  onLimpiar={limpiarFiltros}
                />
              )}

              <div className="space-y-4">
                {cargando && <SkeletonBanco />}

                {!cargando && error && (
                  <div className={`flex flex-col items-center rounded-2xl border p-12 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}>
                    <span className={`flex h-12 w-12 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                      <AlertCircle className="h-6 w-6" />
                    </span>
                    <p className={`mt-4 text-sm font-medium ${paletaSaberPro.titulo}`}>{error}</p>
                    <Button type="button" className={`mt-4 ${paletaSaberPro.botonNeutro}`} onClick={() => void recargar()}>
                      Reintentar
                    </Button>
                  </div>
                )}

                {!cargando && !error && (
                  <Tabs value={pestanaActiva} onValueChange={setPestanaActiva}>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <TabsList>
                        <TabsTrigger value="pendientes">Pendientes ({pendientes.length})</TabsTrigger>
                        <TabsTrigger value="aprobados">Aprobados ({aprobados.length})</TabsTrigger>
                      </TabsList>
                      <p className={`text-xs ${paletaSaberPro.apoyo}`}>
                        Mostrando {totalElementos} {pestanaActiva === 'pendientes' ? 'pregunta(s)/consigna(s) pendiente(s)' : 'aprobada(s)'}
                      </p>
                    </div>

                    <TabsContent value="pendientes" className="mt-4">
                      {listaPaginada.length === 0 ? (
                        <EstadoVacioBanco
                          titulo="No hay contenido pendiente con estos filtros"
                          detalle="Ajusta los filtros o genera contenido con IA para revisarlo aquí antes de aprobarlo."
                          icono={<Sparkles className="h-8 w-8" />}
                        />
                      ) : (
                        <>
                          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                            {listaPaginada.map((c) => (
                              <TarjetaContenidoSaberPro key={c.id} contenido={c} onCambio={() => void recargar()} />
                            ))}
                          </div>
                          <PaginacionBancoContenido
                            pagina={paginaSegura}
                            totalPaginas={totalPaginas}
                            totalElementos={totalElementos}
                            elementosPorPagina={ELEMENTOS_POR_PAGINA}
                            onPaginaChange={setPagina}
                          />
                        </>
                      )}
                    </TabsContent>

                    <TabsContent value="aprobados" className="mt-4">
                      {listaPaginada.length === 0 ? (
                        <EstadoVacioBanco
                          titulo="No hay contenido aprobado con estos filtros"
                          detalle="Cuando apruebes piezas del banco, aparecerán aquí y quedarán listas para los simulacros."
                          icono={<BookMarked className="h-8 w-8" />}
                        />
                      ) : (
                        <>
                          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                            {listaPaginada.map((c) => (
                              <TarjetaContenidoSaberPro key={c.id} contenido={c} onCambio={() => void recargar()} />
                            ))}
                          </div>
                          <PaginacionBancoContenido
                            pagina={paginaSegura}
                            totalPaginas={totalPaginas}
                            totalElementos={totalElementos}
                            elementosPorPagina={ELEMENTOS_POR_PAGINA}
                            onPaginaChange={setPagina}
                          />
                        </>
                      )}
                    </TabsContent>
                  </Tabs>
                )}
              </div>
            </>
          )}
        </main>
      </div>

      {curso && (
        <ModalGenerarContenidoSaberPro
          abierta={modalGenerarAbierto}
          curso={curso}
          onCerrar={() => setModalGenerarAbierto(false)}
          onGenerado={() => void recargar()}
        />
      )}
    </div>
  )
}