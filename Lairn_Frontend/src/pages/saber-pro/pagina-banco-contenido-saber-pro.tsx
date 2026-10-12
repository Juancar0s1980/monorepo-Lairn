// Página del banco de contenido Saber Pro, para el rol Docente (HU-20).
//
// Punto de trabajo para generar y curar el contenido con IA por área:
//
//   1. El docente elige uno de sus cursos Saber Pro; el banco que se muestra es
//      el de su área (el banco es del docente + área, compartido entre sus
//      cursos de la misma área).
//   2. "Generar contenido" abre el modal que arma los criterios según la
//      estructura del área (HU-20.1/20.2).
//   3. Dos pestañas separan la cola de revisión ("Pendientes") del contenido ya
//      aprobado ("Aprobados"); cada tarjeta pendiente permite aprobar, editar o
//      descartar (HU-20.3/20.4).

import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, BookMarked, GraduationCap, Plus, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useCursosSaberPro } from '@/hooks/use-cursos-saber-pro'
import { useContenidoBancoSaberPro } from '@/hooks/use-contenido-banco-saber-pro'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerLargo } from './utilidades'
import { TarjetaContenidoSaberPro } from './componentes/tarjeta-contenido-saber-pro'
import { ModalGenerarContenidoSaberPro } from './componentes/modal-generar-contenido-saber-pro'

function SkeletonBanco() {
  return (
    <div aria-busy="true" aria-label="Cargando banco de contenido" className="grid gap-4 sm:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className={`h-48 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-4 w-24 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-3 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-4/5 rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

function EstadoVacioBanco({ titulo, detalle, icono }: { titulo: string; detalle: string; icono: ReactNode }) {
  return (
    <div className={`flex flex-col items-center rounded-3xl border border-dashed p-12 text-center ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}>
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

  // Curso efectivo: el elegido por el docente o, por defecto, el primero de la
  // lista (sin efecto de inicialización: se deriva en cada render).
  const cursoId = cursoIdSeleccionado ?? cursos[0]?.id ?? null
  const curso = useMemo(() => cursos.find((c) => c.id === cursoId) ?? null, [cursos, cursoId])
  const { contenidos, cargando, error, recargar } = useContenidoBancoSaberPro(cursoId)

  // La pestaña de revisión y la de aprobados se derivan del mismo listado.
  const pendientes = contenidos.filter((c) => c.estado === 'pendiente')
  const aprobados = contenidos.filter((c) => c.estado === 'aprobado')

  return (
    <div className={`relative overflow-hidden rounded-2xl ${paletaSaberPro.banda}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-radial from-[#c89b14]/15 to-transparent dark:from-[#E3C063]/15"
      />
      <div aria-hidden="true" className={`h-2 w-full ${paletaSaberPro.franja}`} />
      <div className="relative p-6 md:p-10">
        {/* Encabezado: volver al panel + título */}
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
            <p className={`mt-2 max-w-xl text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              Genera preguntas y consignas con IA, revísalas y apruébalas para que
              alimenten los simulacros del área.
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

        <main className="mt-8">
          {/* Sin cursos: el banco se genera desde un curso del docente (HU-17). */}
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
              {/* Selector de curso: el banco se consulta por el área del curso. */}
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

              <div className="mt-6">
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
                  <Tabs defaultValue="pendientes">
                    <TabsList>
                      <TabsTrigger value="pendientes">Pendientes ({pendientes.length})</TabsTrigger>
                      <TabsTrigger value="aprobados">Aprobados ({aprobados.length})</TabsTrigger>
                    </TabsList>

                    <TabsContent value="pendientes" className="mt-4">
                      {pendientes.length === 0 ? (
                        <EstadoVacioBanco
                          titulo="No hay contenido pendiente"
                          detalle="Genera contenido con IA para revisarlo aquí antes de aprobarlo."
                          icono={<Sparkles className="h-8 w-8" />}
                        />
                      ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                          {pendientes.map((c) => (
                            <TarjetaContenidoSaberPro key={c.id} contenido={c} onCambio={() => void recargar()} />
                          ))}
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="aprobados" className="mt-4">
                      {aprobados.length === 0 ? (
                        <EstadoVacioBanco
                          titulo="Todavía no hay contenido aprobado"
                          detalle="Cuando apruebes piezas del banco, aparecerán aquí y quedarán listas para los simulacros."
                          icono={<BookMarked className="h-8 w-8" />}
                        />
                      ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                          {aprobados.map((c) => (
                            <TarjetaContenidoSaberPro key={c.id} contenido={c} onCambio={() => void recargar()} />
                          ))}
                        </div>
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