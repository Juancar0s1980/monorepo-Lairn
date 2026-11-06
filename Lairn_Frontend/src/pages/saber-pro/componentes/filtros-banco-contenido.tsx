// Componente modular de filtros para el banco de contenido Saber Pro (HU-20).
//
// Permite filtrar por competencia, afirmación, evidencia o parte (Inglés).
// Se adapta a la estructura del área del curso y es totalmente responsive.
// Diseño modular y reutilizable para facilitar la revisión por el docente.

import { useMemo } from 'react'
import { Filter, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { CriteriosAreaSaberPro, AfirmacionCatalogoSaberPro, EvidenciaCatalogoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro, selectContenidoAncho, selectItemLargo, selectTriggerLargo } from '../utilidades'

interface FiltrosBancoContenidoProps {
  criterios: CriteriosAreaSaberPro | null
  tipoEstructura: 'competencias' | 'partes' | 'consigna'
  competenciaId: number | null
  afirmacionId: number | null
  evidenciaId: number | null
  parte: number | null
  onCompetenciaChange: (id: number | null) => void
  onAfirmacionChange: (id: number | null) => void
  onEvidenciaChange: (id: number | null) => void
  onParteChange: (id: number | null) => void
  onLimpiar: () => void
}

export function FiltrosBancoContenido({
  criterios,
  tipoEstructura,
  competenciaId,
  afirmacionId,
  evidenciaId,
  parte,
  onCompetenciaChange,
  onAfirmacionChange,
  onEvidenciaChange,
  onParteChange,
  onLimpiar,
}: FiltrosBancoContenidoProps) {
  const competencias = criterios?.competencias ?? []
  const partes = criterios?.partes ?? []

  const afirmacionesDisponibles = useMemo<AfirmacionCatalogoSaberPro[]>(() => {
    if (!competenciaId) return []
    const competencia = competencias.find((c) => c.id === competenciaId)
    return competencia?.afirmaciones ?? []
  }, [competenciaId, competencias])

  const evidenciasDisponibles = useMemo<EvidenciaCatalogoSaberPro[]>(() => {
    if (!afirmacionId) return []
    const afirmacion = afirmacionesDisponibles.find((a) => a.id === afirmacionId)
    return afirmacion?.evidencias ?? []
  }, [afirmacionId, afirmacionesDisponibles])

  const hayFiltrosActivos = competenciaId !== null || afirmacionId !== null || evidenciaId !== null || parte !== null

  if (tipoEstructura === 'consigna') {
    return null
  }

  return (
    <section
      className={`rounded-2xl border p-4 md:p-5 ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
      aria-label="Filtros del banco de contenido"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`flex h-9 w-9 items-center justify-center rounded-full ${paletaSaberPro.chipAccion}`}>
            <Filter className="h-4 w-4" />
          </span>
          <div>
            <h2 className={`text-sm font-bold ${paletaSaberPro.titulo}`}>Filtrar preguntas</h2>
            <p className={`text-xs ${paletaSaberPro.apoyo}`}>
              {tipoEstructura === 'partes'
                ? 'Filtra por parte del examen de Inglés'
                : 'Filtra por competencia, afirmación y evidencia'}
            </p>
          </div>
        </div>
        {hayFiltrosActivos && (
          <Button
            type="button"
            size="sm"
            className={`h-8 gap-1.5 px-3 text-xs ${paletaSaberPro.botonNeutro}`}
            onClick={onLimpiar}
          >
            <X className="h-3.5 w-3.5" />
            Limpiar filtros
          </Button>
        )}
      </header>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {tipoEstructura === 'partes' && (
          <div className="space-y-1.5">
            <Label className={`text-xs ${paletaSaberPro.titulo}`}>Parte</Label>
            <Select
              items={partes.map((p) => ({ value: String(p.numero), label: `Parte ${p.numero} · ${p.nombre}` }))}
              value={parte ? String(parte) : ''}
              onValueChange={(valor) => onParteChange(valor ? Number(valor) : null)}
            >
              <SelectTrigger className={selectTriggerLargo}>
                <SelectValue placeholder="Todas las partes" />
              </SelectTrigger>
              <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                {partes.map((p) => (
                  <SelectItem key={p.numero} value={String(p.numero)} className={selectItemLargo}>
                    Parte {p.numero} — {p.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {tipoEstructura === 'competencias' && (
          <>
            <div className="space-y-1.5">
              <Label className={`text-xs ${paletaSaberPro.titulo}`}>Competencia</Label>
              <Select
                items={competencias.map((c) => ({ value: String(c.id), label: c.nombre }))}
                value={competenciaId ? String(competenciaId) : ''}
                onValueChange={(valor) => {
                  const nuevoId = valor ? Number(valor) : null
                  onCompetenciaChange(nuevoId)
                  onAfirmacionChange(null)
                  onEvidenciaChange(null)
                }}
              >
                <SelectTrigger className={selectTriggerLargo}>
                  <SelectValue placeholder="Todas las competencias" />
                </SelectTrigger>
                <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                  {competencias.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)} className={selectItemLargo}>
                      {c.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className={`text-xs ${paletaSaberPro.titulo}`}>Afirmación</Label>
              <Select
                items={afirmacionesDisponibles.map((a) => ({ value: String(a.id), label: a.nombre }))}
                value={afirmacionId ? String(afirmacionId) : ''}
                onValueChange={(valor) => {
                  const nuevoId = valor ? Number(valor) : null
                  onAfirmacionChange(nuevoId)
                  onEvidenciaChange(null)
                }}
                disabled={!competenciaId || afirmacionesDisponibles.length === 0}
              >
                <SelectTrigger className={selectTriggerLargo}>
                  <SelectValue placeholder={competenciaId ? 'Todas las afirmaciones' : 'Selecciona competencia'} />
                </SelectTrigger>
                <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                  {afirmacionesDisponibles.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)} className={selectItemLargo}>
                      {a.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5 sm:col-span-2 lg:col-span-1">
              <Label className={`text-xs ${paletaSaberPro.titulo}`}>Evidencia</Label>
              <Select
                items={evidenciasDisponibles.map((e) => ({ value: String(e.id), label: e.nombre }))}
                value={evidenciaId ? String(evidenciaId) : ''}
                onValueChange={(valor) => onEvidenciaChange(valor ? Number(valor) : null)}
                disabled={!afirmacionId || evidenciasDisponibles.length === 0}
              >
                <SelectTrigger className={selectTriggerLargo}>
                  <SelectValue placeholder={afirmacionId ? 'Todas las evidencias' : 'Selecciona afirmación'} />
                </SelectTrigger>
                <SelectContent alignItemWithTrigger={false} className={selectContenidoAncho}>
                  {evidenciasDisponibles.map((e) => (
                    <SelectItem key={e.id} value={String(e.id)} className={selectItemLargo}>
                      {e.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </>
        )}
      </div>
    </section>
  )
}
