// Asignación masiva de docentes a las asignaturas del programa (ADR-017).
// Pasos: 1) plantilla y archivo → 2) vista previa por fila → 3) resultado.
// La asignación individual (editar asignatura → Docente) sigue igual.

import { useRef, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet, FileText, Loader2, Upload } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AnalisisAsignacion, EstadoAsignacion, ResultadoAsignacion } from '@/types/asignacion'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'
import { mensajeError } from '../academico-utils'
import { ESTADOS_ASIGNACION, descargarResumen, etiquetaEstado } from '../asignacion-utils'

const BASE = '/evaluacion/asignacion-docentes'

export function AsignacionDocentes({
  abierto,
  alCerrar,
  programa,
  alAplicar,
}: {
  abierto: boolean
  alCerrar: () => void
  programa: { id: number | string; codigo: string; nombre: string } | null
  alAplicar: () => void
}) {
  const entrada = useRef<HTMLInputElement>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [analisis, setAnalisis] = useState<AnalisisAsignacion | null>(null)
  const [resultado, setResultado] = useState<ResultadoAsignacion | null>(null)
  const [filtro, setFiltro] = useState<EstadoAsignacion | 'todas'>('todas')
  const [ocupado, setOcupado] = useState<'analizar' | 'confirmar' | 'plantilla' | null>(null)

  const reiniciar = () => {
    setArchivo(null)
    setAnalisis(null)
    setResultado(null)
    setFiltro('todas')
    if (entrada.current) entrada.current.value = ''
  }
  const cerrar = () => {
    reiniciar()
    alCerrar()
  }

  const plantilla = async (formato: 'xlsx' | 'csv') => {
    if (!programa) return
    setOcupado('plantilla')
    try {
      await descargarArchivo(`${BASE}/plantilla/?programa=${programa.id}&formato=${formato}`,
        `asignacion_docentes_${programa.codigo}.${formato}`)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo descargar la plantilla'))
    } finally {
      setOcupado(null)
    }
  }

  const analizar = async () => {
    if (!archivo || !programa) return
    const datos = new FormData()
    datos.append('archivo', archivo)
    datos.append('programa', String(programa.id))
    setOcupado('analizar')
    try {
      const r = await api.post<AnalisisAsignacion>(`${BASE}/analizar/`, datos, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setAnalisis(r.data)
      setFiltro('todas')
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo analizar el archivo'))
    } finally {
      setOcupado(null)
    }
  }

  const confirmar = async () => {
    if (!analisis) return
    setOcupado('confirmar')
    try {
      const r = await api.post<ResultadoAsignacion>(`${BASE}/confirmar/`, {
        programa: analisis.programa.id, filas: analisis.entrada, huella: analisis.huella,
      })
      setResultado(r.data)
      toast.success(`${r.data.resumen.asignadas ?? 0} asignatura(s) con docente asignado`)
      alAplicar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo aplicar la asignación'))
    } finally {
      setOcupado(null)
    }
  }

  const vista = resultado ?? analisis
  const aplicables = analisis ? analisis.resumen.valida + analisis.resumen.advertencia : 0
  const filas = (vista?.filas ?? []).filter((f) => filtro === 'todas' || f.estado === filtro)

  return (
    <Dialog open={abierto} onOpenChange={(v) => !v && cerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Asignar docentes por archivo</DialogTitle>
          <DialogDescription>
            {programa ? `${programa.codigo} · ${programa.nombre}. ` : ''}
            Asigna el docente de varias asignaturas a la vez. Revisa la vista previa antes de confirmar: se aplica todo o nada.
          </DialogDescription>
        </DialogHeader>

        {!vista && (
          <div className="space-y-4">
            <ol className="space-y-2 text-sm text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">1. Descarga la plantilla.</span> Trae las asignaturas
                activas del programa y su docente actual. La versión Excel incluye la lista de docentes.
              </li>
              <li>
                <span className="font-medium text-foreground">2. Escribe el correo del docente</span> en
                {' '}<code className="text-xs">docente_email</code>. Déjalo vacío para no cambiar esa asignatura.
                {' '}<code className="text-xs">curso_codigo</code> es opcional (para elegir uno de varios cursos del docente).
              </li>
              <li>
                <span className="font-medium text-foreground">3. Súbelo y revisa</span> qué pasará con cada fila.
                También se acepta JSON: <code className="text-xs">{'{"asignaciones": [{"asignatura_codigo", "docente_email", "curso_codigo"}]}'}</code>.
              </li>
            </ol>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={() => plantilla('xlsx')} disabled={!programa || ocupado !== null}>
                <FileSpreadsheet className="mr-1.5 h-4 w-4" aria-hidden />
                Plantilla Excel
              </Button>
              <Button variant="outline" size="sm" onClick={() => plantilla('csv')} disabled={!programa || ocupado !== null}>
                <FileText className="mr-1.5 h-4 w-4" aria-hidden />
                Plantilla CSV
              </Button>
            </div>
            <div className="flex flex-col gap-2 rounded-xl border border-dashed border-border p-4 sm:flex-row sm:items-center">
              <input
                ref={entrada}
                type="file"
                accept=".csv,.xlsx,.json"
                aria-label="Archivo de asignaciones (.csv, .xlsx o .json)"
                className="min-w-0 flex-1 text-sm file:mr-3 file:rounded-lg file:border file:border-border file:bg-muted file:px-3 file:py-1.5 file:text-sm"
                onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
              />
              <Button onClick={analizar} disabled={!archivo || ocupado !== null}>
                {ocupado === 'analizar' ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Upload className="mr-1.5 h-4 w-4" aria-hidden />}
                Analizar archivo
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Máximo 2 MB y 2000 filas. Solo se leen las columnas de código de asignatura, correo del docente y código de curso.</p>
          </div>
        )}

        {vista && (
          <div className="min-w-0 space-y-3">
            {resultado ? (
              <div className="flex items-start gap-2 rounded-xl border border-success/40 bg-success/5 p-3 text-sm">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden />
                <p>
                  Se asignó docente a <strong>{resultado.resumen.asignadas ?? 0}</strong> asignatura(s)
                  {(resultado.resumen.cursos_creados ?? 0) > 0 && <> y se crearon <strong>{resultado.resumen.cursos_creados}</strong> curso(s)</>}.
                  {' '}Las filas con error o sin docente no se aplicaron.
                </p>
              </div>
            ) : (
              (analisis?.resumen.cursos_nuevos || analisis?.resumen.cambios_docente) ? (
                <div className="flex items-start gap-2 rounded-xl border border-warning/50 bg-warning/5 p-3 text-sm">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
                  <p>
                    Al confirmar
                    {analisis.resumen.cursos_nuevos > 0 && <> se crearán <strong>{analisis.resumen.cursos_nuevos}</strong> curso(s) para docentes que no tenían uno</>}
                    {analisis.resumen.cursos_nuevos > 0 && analisis.resumen.cambios_docente > 0 && ' y'}
                    {analisis.resumen.cambios_docente > 0 && <> <strong>{analisis.resumen.cambios_docente}</strong> asignatura(s) cambiarán de docente</>}.
                  </p>
                </div>
              ) : null
            )}

            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar filas por estado">
              {[{ clave: 'todas' as const, etiqueta: 'Todas', n: vista.resumen.total },
                ...ESTADOS_ASIGNACION.map((e) => ({ clave: e.clave, etiqueta: e.etiqueta, n: vista.resumen[e.clave] }))]
                .map((e) => (
                  <button
                    key={e.clave}
                    type="button"
                    onClick={() => setFiltro(e.clave)}
                    aria-pressed={filtro === e.clave}
                    className={cn(
                      'rounded-full border px-3 py-1 text-xs transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                      filtro === e.clave ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground hover:bg-muted',
                    )}
                  >
                    {e.etiqueta} · {e.n}
                  </button>
                ))}
            </div>

            <div className="max-h-[45vh] overflow-auto rounded-xl border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Fila</TableHead>
                    <TableHead>Asignatura</TableHead>
                    <TableHead>Docente</TableHead>
                    <TableHead>Curso</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="min-w-[16rem]">Detalle</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filas.map((f) => {
                    const e = etiquetaEstado(f.estado)
                    return (
                      <TableRow key={f.fila}>
                        <TableCell className="font-mono text-xs">{f.fila}</TableCell>
                        <TableCell>
                          <span className="font-mono text-xs">{f.asignatura_codigo || '—'}</span>
                          {f.asignatura && <span className="block text-xs text-muted-foreground">{f.asignatura.nombre}</span>}
                        </TableCell>
                        <TableCell className="text-xs">
                          {f.docente ? (
                            <>
                              {f.docente.nombre}
                              <span className="block text-muted-foreground">{f.docente.email}</span>
                            </>
                          ) : (f.docente_email || '—')}
                        </TableCell>
                        <TableCell className="text-xs">
                          {f.curso ? (
                            <>
                              {f.curso.nombre}
                              <span className="block font-mono text-muted-foreground">{f.curso.codigo ?? 'nuevo'}</span>
                            </>
                          ) : '—'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={e.variante}>{e.etiqueta}</Badge>
                          {resultado && f.aplicada && <span className="block pt-1 text-[11px] text-success">Aplicada</span>}
                        </TableCell>
                        <TableCell className="text-xs whitespace-normal text-muted-foreground">{f.mensaje}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              {!filas.length && <p className="p-4 text-sm text-muted-foreground">No hay filas con este estado.</p>}
            </div>
          </div>
        )}

        <DialogFooter className="flex-col gap-2 sm:flex-row sm:justify-between">
          {vista ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => descargarResumen(vista.filas, `${resultado ? 'resultado' : 'vista_previa'}_asignacion_${vista.programa.codigo}.csv`, !!resultado)}
            >
              <Download className="mr-1.5 h-4 w-4" aria-hidden />
              {resultado ? 'Descargar resumen (CSV)' : 'Descargar vista previa (CSV)'}
            </Button>
          ) : <span />}
          <div className="flex flex-col gap-2 sm:flex-row">
            {analisis && !resultado && (
              <Button variant="outline" onClick={reiniciar} disabled={ocupado !== null}>Cambiar archivo</Button>
            )}
            {analisis && !resultado ? (
              <Button onClick={confirmar} disabled={!aplicables || ocupado !== null}>
                {ocupado === 'confirmar' && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                {aplicables ? `Confirmar ${aplicables} asignación(es)` : 'Nada que aplicar'}
              </Button>
            ) : (
              <Button variant={resultado ? 'default' : 'outline'} onClick={cerrar}>{resultado ? 'Listo' : 'Cancelar'}</Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
