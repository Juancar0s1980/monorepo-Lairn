// Diálogo de revisión de un cargue documental antes de aprobar.
//
// Flujo en 2 pasos: el PDF subido queda en `procesado` con su propuesta IA;
// aquí el administrador la revisa (asignaturas / momentos / RA-DCE), elige
// el programa destino (y la asignatura destino si es plan de aula) y recién
// ahí aprueba. Sin este paso el cargue quedaba "procesado" para siempre y el
// plan de aula nunca llegaba al programa.

import { useEffect, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { AlertTriangle, Check, Loader2, Trash2 } from 'lucide-react'
import type { AsignaturaMalla, CorreccionPropuesta } from '@/types/academico'
import type { Academico } from '../use-academico'

// Formas de la propuesta IA según tipo de documento (ver agentes_*).
interface AsignaturaPropuesta {
  codigo?: string
  nombre?: string
  creditos?: number
  intensidad?: number
  tipo?: string
  semestre?: number
}

interface MomentoPropuesto {
  semestre?: number
  nombre?: string
  descripcion?: string
}

interface ResultadoPropuesto {
  descripcion?: string
  competencia_sugerida?: string
  tipo_competencia?: string
  evidencia_observable?: string
  tarea_sugerida?: string
  criterios_rubrica?: { criterio: string; niveles: string; peso: number }[]
}

function comoLista<T>(valor: unknown): T[] {
  return Array.isArray(valor) ? (valor as T[]) : []
}

export function DialogoRevisionCargue({ ac }: { ac: Academico }) {
  const cargue = ac.revisandoCargue
  const abierto = cargue !== null

  // Programa y asignatura destino (editables en la revisión).
  const [programaDestino, setProgramaDestino] = useState('')
  const [asignaturaDestino, setAsignaturaDestino] = useState('')
  const [asignaturasDestino, setAsignaturasDestino] = useState<AsignaturaMalla[]>([])
  const [cargandoAsignaturas, setCargandoAsignaturas] = useState(false)
  // Correcciones por fila de pensum (código/créditos/semestre que la IA no
  // extrajo se completan aquí y viajan en el aprobar).
  const [ediciones, setEdiciones] = useState<
    Record<number, { codigo: string; creditos: string; semestre: string }>
  >({})
  // Crear el programa desde la resolución en vez de asignar a uno existente.
  const [crearNuevo, setCrearNuevo] = useState(false)

  // Al abrir: programa del cargue o el activo; asignatura en blanco.
  useEffect(() => {
    if (cargue) {
      setProgramaDestino(cargue.programa ? String(cargue.programa) : ac.programaId)
      setAsignaturaDestino('')
      setEdiciones({})
      setCrearNuevo(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cargue?.id])

  // Asignaturas del programa destino (para plan de aula).
  useEffect(() => {
    if (!abierto || cargue?.tipo !== 'plan_aula' || !programaDestino) {
      setAsignaturasDestino([])
      return
    }
    // Si el destino es el programa activo, reutiliza lo ya cargado.
    if (programaDestino === ac.programaId) {
      setAsignaturasDestino(ac.asignaturas)
      return
    }
    setCargandoAsignaturas(true)
    api
      .get<AsignaturaMalla[]>(`/evaluacion/programas/${programaDestino}/asignaturas/`)
      .then((res) => setAsignaturasDestino(Array.isArray(res.data) ? res.data : []))
      .catch(() => setAsignaturasDestino([]))
      .finally(() => setCargandoAsignaturas(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierto, cargue?.tipo, programaDestino])

  if (!cargue) return null
  const propuesta = (cargue.propuesta_json ?? {}) as Record<string, unknown>
  const esPlanAula = cargue.tipo === 'plan_aula'
  const esPensum = cargue.tipo === 'pensum'
  const esResolucion = cargue.tipo === 'resolucion'
  const infoPrograma = propuesta.programa as { codigo?: string; nombre?: string } | undefined
  const puedeCrearPrograma =
    esResolucion && Boolean(infoPrograma?.codigo && infoPrograma?.nombre)
  const puedeAprobar =
    cargue.estado === 'procesado' &&
    (crearNuevo || programaDestino !== '') &&
    (!esPlanAula || asignaturaDestino !== '')
  // Correcciones digitadas por fila (solo filas tocadas viajan al backend).
  const correcciones: CorreccionPropuesta[] = Object.entries(ediciones)
    .filter(([, e]) => e.codigo.trim() !== '' || e.creditos !== '' || e.semestre !== '')
    .map(([idx, e]) => ({
      indice: Number(idx),
      ...(e.codigo.trim() !== '' ? { codigo: e.codigo.trim() } : {}),
      ...(e.creditos !== '' ? { creditos: Number(e.creditos) } : {}),
      ...(e.semestre !== '' ? { semestre: Number(e.semestre) } : {}),
    }))
  const setEdicion = (idx: number, campo: 'codigo' | 'creditos' | 'semestre', valor: string) =>
    setEdiciones((prev) => {
      const base = prev[idx] ?? { codigo: '', creditos: '', semestre: '' }
      return { ...prev, [idx]: { ...base, [campo]: valor } }
    })
  // El programa del cargue ya no está activo (se desactivó con cascada):
  // la incorporación quedó en histórico y el candado de auditoría se libera.
  const programaInactivo =
    cargue.programa != null && !ac.programas.some((p) => p.id === cargue.programa)

  return (
    <Dialog
      open={abierto}
      onOpenChange={(v) => {
        if (!v) ac.setRevisandoCargue(null)
      }}
    >
      <DialogContent className="sm:max-w-[720px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Revisar propuesta — {cargue.nombre_archivo}
          </DialogTitle>
          <DialogDescription>
            Verifica lo extraído por la IA, elige el destino y aprueba para que
            aparezca en el programa.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="capitalize">
              {cargue.tipo.replace('_', ' ')}
            </Badge>
            <Badge
              variant={cargue.estado === 'aprobado' ? 'secondary' : 'outline'}
              className={
                cargue.estado === 'aprobado'
                  ? 'bg-success/10 text-success border-transparent'
                  : ''
              }
            >
              {cargue.estado}
            </Badge>
            {cargue.programa_nombre && (
              <span className="text-xs text-muted-foreground">
                Programa actual: {cargue.programa_nombre}
              </span>
            )}
          </div>

          {/* Aprobado huérfano: su programa ya se desactivó */}
          {cargue.estado === 'aprobado' && programaInactivo && (
            <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3">
              <AlertTriangle className="h-4 w-4 mt-0.5 text-warning" />
              <p className="text-xs text-foreground">
                Su programa ya no está activo: lo incorporado quedó en histórico.
                Puedes anular la aprobación o eliminar el cargue.
              </p>
            </div>
          )}

          {/* Error de un cargue fallido */}
          {cargue.estado === 'fallido' && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
              <AlertTriangle className="h-4 w-4 mt-0.5 text-destructive" />
              <p className="text-xs text-foreground">
                {cargue.detalle_error || 'La IA o el PDF fallaron sin detalle.'}
              </p>
            </div>
          )}

          {/* Destino */}
          {cargue.estado === 'procesado' && (
            <div className="space-y-3">
              {puedeCrearPrograma && (
                <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-border bg-muted p-3">
                  <input
                    type="checkbox"
                    checked={crearNuevo}
                    onChange={(e) => setCrearNuevo(e.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-primary"
                  />
                  <span className="text-xs text-foreground">
                    <span className="font-medium">Crear programa nuevo desde el PDF:</span>{' '}
                    {infoPrograma!.codigo} — {infoPrograma!.nombre} (luego incorpora
                    momentos y semestres sobre él)
                  </span>
                </label>
              )}
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground">
                    Programa destino
                  </label>
                  <Select
                    value={programaDestino}
                    onValueChange={(v) => setProgramaDestino(v ?? '')}
                    disabled={crearNuevo}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona programa" />
                    </SelectTrigger>
                    <SelectContent>
                      {ac.programas.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>
                          {p.codigo} — {p.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              {esPlanAula && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground">
                    Asignatura destino (obligatoria)
                  </label>
                  <Select value={asignaturaDestino} onValueChange={(v) => setAsignaturaDestino(v ?? '')}>
                    <SelectTrigger>
                      <SelectValue
                        placeholder={
                          cargandoAsignaturas ? 'Cargando...' : 'Selecciona asignatura'
                        }
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {asignaturasDestino.map((a) => (
                        <SelectItem key={a.id} value={String(a.id)}>
                          {a.codigo} — {a.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-[11px] text-muted-foreground">
                    Cada RA-DCE cuelga de una asignatura; sin ella no se puede incorporar.
                  </p>
                </div>
              )}
              </div>
            </div>
          )}

          {/* Propuesta: pensum (código/créditos/semestre editables) */}
          {esPensum && (
            <>
              <p className="text-xs text-muted-foreground">
                Completa los códigos que la IA no extrajo (sin código la fila se omite).
                {correcciones.length > 0 && (
                  <span className="font-medium text-foreground">
                    {' '}· {correcciones.length} fila(s) editada(s)
                  </span>
                )}
              </p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Asignatura</TableHead>
                    <TableHead className="text-right">Créd.</TableHead>
                    <TableHead>Sem.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comoLista<AsignaturaPropuesta>(propuesta.asignaturas).map((a, i) => {
                    const ed = ediciones[i] ?? { codigo: '', creditos: '', semestre: '' }
                    const sinCodigo = !a.codigo && ed.codigo.trim() === ''
                    return (
                      <TableRow key={i}>
                        <TableCell>
                          <Input
                            value={ed.codigo !== '' ? ed.codigo : (a.codigo as string | undefined) ?? ''}
                            placeholder={a.codigo ? undefined : 'Falta código'}
                            onChange={(e) => setEdicion(i, 'codigo', e.target.value)}
                            className={`h-8 w-[110px] font-mono text-xs ${sinCodigo ? 'border-warning' : ''}`}
                          />
                        </TableCell>
                        <TableCell className="font-medium">{a.nombre}</TableCell>
                        <TableCell className="text-right">
                          <Input
                            type="number"
                            min={0}
                            max={20}
                            value={ed.creditos !== '' ? ed.creditos : String(a.creditos ?? '')}
                            onChange={(e) => setEdicion(i, 'creditos', e.target.value)}
                            className="h-8 w-[64px] text-right text-xs"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min={1}
                            max={14}
                            value={ed.semestre !== '' ? ed.semestre : String(a.semestre ?? '')}
                            onChange={(e) => setEdicion(i, 'semestre', e.target.value)}
                            className="h-8 w-[64px] text-xs"
                          />
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </>
          )}

          {/* Propuesta: resolución */}
          {cargue.tipo === 'resolucion' && (
            <div className="space-y-2">
              {(propuesta.programa as Record<string, string> | undefined) && (
                <p className="text-xs text-muted-foreground">
                  Programa detectado:{' '}
                  <span className="font-medium text-foreground">
                    {(propuesta.programa as Record<string, string>).codigo} —{' '}
                    {(propuesta.programa as Record<string, string>).nombre}
                  </span>
                </p>
              )}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Momento</TableHead>
                    <TableHead>Semestre</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comoLista<MomentoPropuesto>(propuesta.momentos).map((m, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{m.nombre}</TableCell>
                      <TableCell>S{m.semestre}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Propuesta: plan de aula */}
          {esPlanAula && (
            <div className="space-y-3">
              {comoLista<ResultadoPropuesto>(propuesta.resultados).map((ra, i) => (
                <div key={i} className="rounded-lg border border-border bg-card p-3 space-y-1">
                  <p className="text-sm font-medium text-foreground">{ra.descripcion}</p>
                  <p className="text-xs text-muted-foreground">
                    Competencia sugerida:{' '}
                    <span className="font-medium">
                      {ra.competencia_sugerida || 'General'} ({ra.tipo_competencia || 'especifica'})
                    </span>
                  </p>
                  {ra.evidencia_observable && (
                    <p className="text-xs text-muted-foreground">
                      <span className="font-semibold">Evidencia:</span> {ra.evidencia_observable}
                    </p>
                  )}
                  {(ra.criterios_rubrica?.length ?? 0) > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {ra.criterios_rubrica!.map((c, j) => (
                        <Badge key={j} variant="secondary">
                          {c.criterio} {c.peso}%
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {comoLista(propuesta.resultados).length === 0 && (
                <p className="text-sm text-muted-foreground">
                  La propuesta no trae resultados para revisar.
                </p>
              )}
            </div>
          )}

          {/* Advertencias de la IA */}
          {comoLista<string>(propuesta.advertencias).length > 0 && (
            <ul className="space-y-1">
              {comoLista<string>(propuesta.advertencias).map((a, i) => (
                <li key={i} className="text-xs text-warning">
                  • {a}
                </li>
              ))}
            </ul>
          )}
        </div>

        <DialogFooter className="flex-wrap">
          <Button variant="outline" onClick={() => ac.setRevisandoCargue(null)}>
            Cerrar
          </Button>
          {(cargue.estado === 'procesado' || cargue.estado === 'rechazado') && (
            <Button
              variant="outline"
              disabled={ac.guardando}
              onClick={() =>
                ac.actualizarCargue(cargue.id, { programa_id: programaDestino || null })
              }
              title="Guarda el programa destino sin incorporar nada todavía"
            >
              {ac.guardando && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              Guardar
            </Button>
          )}
          {cargue.estado === 'procesado' && (
            <Button
              variant="outline"
              disabled={ac.guardando}
              onClick={() => ac.actualizarCargue(cargue.id, { estado: 'rechazado' })}
              title="Descarta la propuesta sin incorporar nada (reversible)"
            >
              Rechazar
            </Button>
          )}
          {cargue.estado === 'rechazado' && (
            <Button
              variant="outline"
              disabled={ac.guardando}
              onClick={() => ac.actualizarCargue(cargue.id, { estado: 'procesado' })}
              title="Vuelve a poner la propuesta en revisión"
            >
              Reabrir
            </Button>
          )}
          {cargue.estado === 'aprobado' && programaInactivo && (
            <>
              <Button
                variant="outline"
                disabled={ac.guardando}
                onClick={() => ac.actualizarCargue(cargue.id, { estado: 'rechazado' })}
                title="Anula la aprobación (el programa ya no está activo)"
              >
                Anular aprobación
              </Button>
              <Button
                variant="destructive"
                disabled={ac.eliminando}
                onClick={() => {
                  ac.setRevisandoCargue(null)
                  ac.setConfirmacion({ tipo: 'cargue', id: cargue.id, nombre: cargue.nombre_archivo })
                }}
                title="Elimina el cargue (su programa ya no está activo)"
              >
                <Trash2 className="h-4 w-4 mr-1.5" />
                Eliminar
              </Button>
            </>
          )}
          {cargue.estado === 'procesado' && (
            <Button
              disabled={!puedeAprobar || ac.aprobandoCargue === cargue.id}
              onClick={() =>
                ac.aprobarCargue(
                  cargue.id,
                  crearNuevo ? undefined : programaDestino || undefined,
                  esPlanAula ? asignaturaDestino || undefined : undefined,
                  {
                    ...(esPensum && correcciones.length > 0 ? { correcciones } : {}),
                    ...(crearNuevo ? { crearPrograma: true } : {}),
                  },
                )
              }
            >
              {ac.aprobandoCargue === cargue.id ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Check className="h-4 w-4 mr-1.5" />
              )}
              Aprobar e incorporar
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
