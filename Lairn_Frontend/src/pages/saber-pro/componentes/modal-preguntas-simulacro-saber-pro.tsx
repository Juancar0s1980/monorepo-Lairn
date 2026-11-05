// Modal de solo lectura con las preguntas asignadas a un simulacro (HU-19.4).
//
// El docente ve el cuestionario congelado tal como quedó al crear o editar el
// simulacro: cada pregunta en su orden, con sus criterios, contexto, opciones y
// respuesta correcta resaltada. En Inglés se muestran la tarea de relacionar y
// los bloques completos de cada parte. No permite modificar el contenido.

import { AlertCircle, BookOpen, CheckCircle2, ClipboardList, Eye, Languages } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { usePreguntasSimulacroSaberPro } from '@/hooks/use-preguntas-simulacro-saber-pro'
import type { ContenidoBancoSaberPro, SimulacroSaberPro } from '@/types/saber-pro'
import { cn } from '@/lib/utils'
import { paletaSaberPro } from '../utilidades'
import { TarjetaContenidoSaberPro } from './tarjeta-contenido-saber-pro'

interface ModalPreguntasSimulacroSaberProProps {
  abierta: boolean
  cursoId: number
  simulacro: SimulacroSaberPro | null
  onCerrar: () => void
}

// Etiqueta breve del tipo de contenido asignado.
function etiquetaTipo(contenido: ContenidoBancoSaberPro): string {
  if (contenido.tipo === 'consigna_escrita') return 'Consigna abierta'
  if (contenido.parte === 1) return 'Relacionar'
  if (contenido.parte !== null && contenido.preguntas.length > 0) return `Parte ${contenido.parte}`
  return 'Pregunta'
}

function SkeletonPreguntas() {
  return (
    <div aria-busy="true" aria-label="Cargando preguntas asignadas" className="space-y-4">
      {Array.from({ length: 3 }).map((_, indice) => (
        <div
          key={indice}
          className={`h-48 animate-pulse rounded-2xl border ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
        >
          <div className={`mx-5 mt-5 h-5 w-1/3 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-3 h-3 w-full rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-2 h-3 w-4/5 rounded ${paletaSaberPro.esqueleto}`} />
          <div className={`mx-5 mt-4 h-16 w-full rounded ${paletaSaberPro.esqueleto}`} />
        </div>
      ))}
    </div>
  )
}

export function ModalPreguntasSimulacroSaberPro({
  abierta,
  cursoId,
  simulacro,
  onCerrar,
}: ModalPreguntasSimulacroSaberProProps) {
  const { datos, cargando, error, recargar } = usePreguntasSimulacroSaberPro(
    cursoId,
    simulacro?.id ?? null,
    abierta && Boolean(simulacro)
  )

  const asignaciones = datos?.preguntas ?? []
  const totalPreguntas = datos?.total_preguntas ?? simulacro?.total_preguntas ?? 0

  return (
    <Dialog open={abierta} onOpenChange={(abre) => !abre && onCerrar()}>
      <DialogContent className="max-h-[92vh] max-w-[calc(100%-1.5rem)] gap-0! overflow-x-hidden overflow-y-auto p-0! sm:max-w-4xl">
        <div className={`p-6 pb-4 ${paletaSaberPro.superficie}`}>
          <DialogHeader className="gap-3">
            <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${paletaSaberPro.chipAccion}`}>
              <Eye className="h-5 w-5" />
            </span>
            <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${paletaSaberPro.apoyoTitulo}`}>
              {simulacro?.area.nombre ?? 'Saber Pro'} · Solo lectura
            </p>
            <DialogTitle className={`text-xl ${paletaSaberPro.titulo}`}>
              Preguntas del simulacro
            </DialogTitle>
            <DialogDescription className={`text-sm leading-relaxed ${paletaSaberPro.texto}`}>
              {simulacro?.titulo || 'Simulacro sin título'}. Estas son las preguntas que quedaron
              asignadas; las respuestas correctas se resaltan en dorado.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 flex flex-wrap gap-1.5">
            <Badge variant="outline" className={cn('gap-1 text-[10px]', paletaSaberPro.badge)}>
              <ClipboardList className="h-3 w-3" /> {asignaciones.length} asignaciones
            </Badge>
            <Badge variant="outline" className={cn('gap-1 text-[10px]', paletaSaberPro.badge)}>
              <CheckCircle2 className="h-3 w-3" /> {totalPreguntas} preguntas totales
            </Badge>
            {simulacro?.area.nombre === 'Inglés' && (
              <Badge variant="outline" className={cn('gap-1 text-[10px]', paletaSaberPro.badge)}>
                <Languages className="h-3 w-3" /> 7 partes
              </Badge>
            )}
          </div>
        </div>

        <div className={`space-y-4 border-t p-6 ${paletaSaberPro.banda} ${paletaSaberPro.borde}`}>
          {cargando && <SkeletonPreguntas />}

          {!cargando && error && (
            <div
              className={`flex flex-col items-center rounded-2xl border p-8 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
            >
              <span className={`flex h-11 w-11 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                <AlertCircle className="h-5 w-5" />
              </span>
              <p className={`mt-3 text-sm font-medium ${paletaSaberPro.titulo}`}>{error}</p>
              <Button type="button" className={`mt-4 ${paletaSaberPro.botonNeutro}`} onClick={() => void recargar()}>
                Reintentar
              </Button>
            </div>
          )}

          {!cargando && !error && asignaciones.length === 0 && (
            <div
              className={`flex flex-col items-center rounded-2xl border border-dashed p-10 text-center ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
            >
              <span className={`flex h-14 w-14 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
                <BookOpen className="h-7 w-7" />
              </span>
              <h3 className={`mt-3 text-base font-bold ${paletaSaberPro.titulo}`}>Sin preguntas asignadas</h3>
              <p className={`mt-1.5 max-w-md text-sm leading-relaxed ${paletaSaberPro.texto}`}>
                El simulacro no tiene contenido asociado. Edítalo para que el sistema seleccione
                preguntas aprobadas del banco.
              </p>
            </div>
          )}

          {!cargando && !error && asignaciones.length > 0 && (
            <div className="space-y-5">
              {asignaciones.map((asignacion) => (
                <article key={asignacion.id} className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={cn(
                        'flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold',
                        paletaSaberPro.numeracionPaso
                      )}
                    >
                      {asignacion.orden}
                    </span>
                    <p className={cn('text-xs font-semibold uppercase tracking-[0.12em]', paletaSaberPro.apoyoTitulo)}>
                      Asignación {asignacion.orden}
                    </p>
                    <Badge variant="outline" className={cn('text-[10px]', paletaSaberPro.badge)}>
                      {etiquetaTipo(asignacion.contenido)}
                    </Badge>
                  </div>
                  <TarjetaContenidoSaberPro
                    contenido={asignacion.contenido}
                    onCambio={() => undefined}
                    soloLectura
                  />
                </article>
              ))}
            </div>
          )}

          <div className={`flex justify-end border-t pt-4 ${paletaSaberPro.borde}`}>
            <Button type="button" className={paletaSaberPro.botonNeutro} onClick={onCerrar}>
              Cerrar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
