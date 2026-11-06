// Panel de supervisión de una evaluación formal (ADR-009), para Coordinador y
// Administrador. Se muestra también con la evaluación publicada:
//   - Supervisión en sala: asigna o quita el docente supervisor (docentes con
//     cursos). Con supervisor, el estudiante solo inicia si fue llamado a lista
//     como presente o tarde.
//   - Convocados (OPCIONAL): por defecto están los inscritos en los cursos de
//     las asignaturas evaluadas; publicar e iniciar no exigen cargue. El cargue
//     por CSV/Excel solo agrega a quien falte (vista previa → Confirmar) y va
//     plegado detrás del botón "Agregar estudiantes".
//   - Seguimiento en vivo: conteos y tabla por convocado (asistencia, progreso,
//     tiempo restante con el reloj del servidor y nota), refresco cada 10 s.
//   - Integridad (ADR-010): incidentes y decisiones por intento. Si la
//     evaluación tiene supervisor, decide el docente; si no, el gestor.

import { useEffect, useRef, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Activity, FileSpreadsheet, Loader2, ShieldCheck, Trash2, Upload, UserMinus } from 'lucide-react'
import type { EvaluacionFormal } from '@/types/evaluacion-formal'
import type { InformeCargue, Seguimiento, SupervisorDisponible } from '@/types/supervision'
import { ResumenCargue, TablaVistaPrevia } from '@/pages/estudiantes/vista-previa-cargue'
import { mensajeError } from '../academico-utils'
import { ChipAsistencia, ProgresoIntento, TarjetasConteo } from '@/pages/supervision/componentes-supervision'
import { ETIQUETA_EXCUSA, formatoHora, useConsultaPeriodica, useRelojServidor } from '@/pages/supervision/supervision-utils'
import { ChipIntegridad, PanelIntegridad } from '@/pages/supervision/integridad-supervision'

function SeccionSupervisor({ evaluacion, alCambiar }: { evaluacion: EvaluacionFormal; alCambiar: () => void }) {
  const [docentes, setDocentes] = useState<SupervisorDisponible[]>([])
  const [guardando, setGuardando] = useState(false)
  // Hora de apertura del panel: basta para saber si la ventana ya cerró.
  const [abiertoEn] = useState(() => Date.now())
  const cerrada = new Date(evaluacion.fecha_fin).getTime() <= abiertoEn

  useEffect(() => {
    api
      .get<SupervisorDisponible[]>('/evaluacion/supervisores-disponibles/')
      .then((r) => setDocentes(r.data))
      .catch((err: unknown) => toast.error(mensajeError(err, 'No se pudieron cargar los docentes')))
  }, [])

  const asignar = async (supervisor: number | null) => {
    setGuardando(true)
    try {
      await api.patch(`/evaluacion/evaluaciones/${evaluacion.id}/supervisor/`, { supervisor })
      toast.success(supervisor ? 'Supervisor asignado' : 'Supervisor quitado: la evaluación ya no exige llamado a lista')
      alCambiar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo cambiar el supervisor'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="h-4 w-4 text-primary" aria-hidden />
          Supervisión en sala
        </CardTitle>
        <CardDescription>
          El docente supervisor hace el llamado a lista. Con supervisor asignado, cada estudiante solo puede iniciar
          cuando lo marcan presente o tarde.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {evaluacion.tipo !== 'cuestionario' ? (
          <p className="text-sm text-muted-foreground">Las evaluaciones por tarea no se presentan en sala.</p>
        ) : (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Select
              value={evaluacion.supervisor ? String(evaluacion.supervisor) : null}
              onValueChange={(v) => v && v !== String(evaluacion.supervisor) && void asignar(Number(v))}
              items={docentes.map((d) => ({ value: String(d.id), label: d.nombre }))}
              disabled={guardando || cerrada}
            >
              <SelectTrigger className="w-full sm:w-80" aria-label="Docente supervisor">
                <SelectValue placeholder={docentes.length ? 'Elige el docente supervisor' : 'No hay docentes con cursos'} />
              </SelectTrigger>
              <SelectContent>
                {docentes.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.nombre} · {d.total_cursos} curso{d.total_cursos === 1 ? '' : 's'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {evaluacion.supervisor && (
              <Button variant="outline" onClick={() => void asignar(null)} disabled={guardando || cerrada}>
                {guardando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <UserMinus className="mr-1.5 h-4 w-4" aria-hidden />}
                Quitar supervisor
              </Button>
            )}
          </div>
        )}
        {cerrada && <p className="text-xs text-muted-foreground">La evaluación ya cerró: el supervisor no se puede cambiar.</p>}
        {!evaluacion.supervisor && evaluacion.tipo === 'cuestionario' && (
          <p className="text-xs text-muted-foreground">Sin supervisor, los convocados inician sin llamado a lista.</p>
        )}
      </CardContent>
    </Card>
  )
}

function SeccionConvocados({ evaluacion, alCargar }: { evaluacion: EvaluacionFormal; alCargar: () => void }) {
  const entrada = useRef<HTMLInputElement>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [informe, setInforme] = useState<InformeCargue | null>(null)
  const [enviando, setEnviando] = useState(false)
  // El cargue es opcional: el área se despliega solo si el gestor la pide.
  const [abierto, setAbierto] = useState(false)

  const enviar = async (confirmar: boolean) => {
    if (!archivo) return
    const datos = new FormData()
    datos.append('archivo', archivo)
    datos.append('confirmar', confirmar ? 'true' : 'false')
    setEnviando(true)
    try {
      const r = await api.post<InformeCargue>(`/evaluacion/evaluaciones/${evaluacion.id}/convocados/cargue/`, datos, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (confirmar) {
        toast.success(`${r.data.agregados} estudiante(s) agregado(s) a la convocatoria`)
        setInforme(null)
        setArchivo(null)
        setAbierto(false)
        alCargar()
      } else {
        setInforme(r.data)
      }
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo procesar el archivo'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileSpreadsheet className="h-4 w-4 text-primary" aria-hidden />
          Convocados
          <Badge variant="outline" className="font-normal">Opcional</Badge>
        </CardTitle>
        <CardDescription>
          Ya están convocados los estudiantes inscritos en los cursos de las asignaturas evaluadas. No necesitas cargar
          a nadie para publicar o iniciar el momento; usa el cargue solo si falta alguien.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!abierto ? (
          <Button variant="outline" onClick={() => setAbierto(true)}>
            <Upload className="mr-1.5 h-4 w-4" aria-hidden />
            Agregar estudiantes (CSV o Excel)
          </Button>
        ) : (
        <>
        <p className="text-xs text-muted-foreground">
          Columna obligatoria <span className="font-mono">correo</span> (o los correos en la primera columna). Opcionales:
          nombre, programa, semestre y código estudiantil: se comparan con la cuenta y nunca se sobrescriben. Quien ya
          está convocado queda igual; solo se agrega a quien falte.
        </p>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            ref={entrada}
            type="file"
            accept=".csv,.xlsx"
            aria-label="Archivo de convocados (.csv o .xlsx)"
            className="min-w-0 text-sm file:mr-3 file:rounded-lg file:border file:border-border file:bg-muted file:px-3 file:py-1.5 file:text-sm"
            onChange={(e) => {
              setArchivo(e.target.files?.[0] ?? null)
              setInforme(null)
            }}
          />
          <Button variant="outline" onClick={() => void enviar(false)} disabled={!archivo || enviando}>
            {enviando && !informe ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Upload className="mr-1.5 h-4 w-4" aria-hidden />}
            Revisar archivo
          </Button>
        </div>

        {informe && (
          <div className="space-y-3">
            <ResumenCargue informe={informe} />
            <TablaVistaPrevia informe={informe} />
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button variant="outline" onClick={() => setInforme(null)} disabled={enviando}>
                Revisar otro archivo
              </Button>
              <Button onClick={() => void enviar(true)} disabled={enviando || !informe.totales.agregar}>
                {enviando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
                Confirmar: agregar {informe.totales.agregar ?? 0}
              </Button>
            </div>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setAbierto(false)
            setInforme(null)
            setArchivo(null)
          }}
          disabled={enviando}
        >
          Cerrar sin cargar
        </Button>
        </>
        )}
      </CardContent>
    </Card>
  )
}

function SeccionSeguimiento({ evaluacion, version }: { evaluacion: EvaluacionFormal; version: number }) {
  const [datos, setDatos] = useState<Seguimiento | null>(null)
  const [error, setError] = useState('')
  const { ahoraServidor, sincronizar } = useRelojServidor()
  // Intentos con incidentes de integridad (ADR-010), para la sección de decisión.
  const conIncidentes = (datos?.filas ?? []).flatMap((fila) =>
    fila.intento?.integridad && fila.intento.integridad.incidentes.length > 0
      ? [{ fila, integridad: fila.intento.integridad }]
      : [],
  )

  const cargar = async () => {
    try {
      const r = await api.get<Seguimiento>(`/evaluacion/evaluaciones/${evaluacion.id}/seguimiento/`)
      setDatos(r.data)
      sincronizar(r.data.ahora_servidor)
      setError('')
    } catch (err: unknown) {
      setError(mensajeError(err, 'No se pudo cargar el seguimiento'))
    }
  }
  // `version` cambia tras un cargue o cambio de supervisor: recarga inmediata.
  useConsultaPeriodica(cargar, true, version)

  const quitar = async (estudiante: number) => {
    try {
      await api.delete(`/evaluacion/evaluaciones/${evaluacion.id}/convocados/${estudiante}/`)
      toast.success('Convocado quitado')
      void cargar()
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo quitar'))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" aria-hidden />
          Seguimiento en vivo
        </CardTitle>
        <CardDescription>Se actualiza cada 10 segundos.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        {!datos ? (
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Cargando" />
        ) : (
          <>
            <TarjetasConteo conteos={datos.conteos} />
            {datos.filas.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aún no hay estudiantes convocados.</p>
            ) : (
              <>
                {/* Móvil: tarjetas apiladas, sin scroll horizontal. */}
                <ul className="space-y-2 md:hidden">
                  {datos.filas.map((f) => (
                    <li key={f.estudiante} className="space-y-2 rounded-xl border border-border p-3">
                      <div className="flex items-start justify-between gap-2">
                        <span className="min-w-0">
                          <span className="block font-medium text-foreground">{f.nombre}</span>
                          <span className="block break-all text-xs text-muted-foreground">{f.email}</span>
                        </span>
                        <span className="flex flex-col items-end gap-1">
                          <ChipAsistencia estado={f.asistencia?.estado} />
                          <ChipIntegridad estado={f.intento?.integridad?.estado} />
                        </span>
                      </div>
                      <ProgresoIntento intento={f.intento} ahoraServidor={ahoraServidor} />
                      <p className="text-xs text-muted-foreground">
                        {f.origen === 'cargue' ? 'Convocado por cargue' : 'Convocado por curso'}
                        {f.intento?.nota != null && ` · Nota ${f.intento.nota}`}
                      </p>
                    </li>
                  ))}
                </ul>
                <div className="hidden md:block">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Estudiante</TableHead>
                        <TableHead>Asistencia</TableHead>
                        <TableHead>Progreso</TableHead>
                        <TableHead className="text-right">Nota</TableHead>
                        <TableHead className="w-10"><span className="sr-only">Acciones</span></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {datos.filas.map((f) => (
                        <TableRow key={f.estudiante}>
                          <TableCell className="whitespace-normal">
                            <span className="block font-medium text-foreground">{f.nombre}</span>
                            <span className="block text-xs text-muted-foreground">
                              {f.email} · {f.origen === 'cargue' ? 'cargue' : 'curso'}
                            </span>
                          </TableCell>
                          <TableCell className="whitespace-normal">
                            <ChipAsistencia estado={f.asistencia?.estado} />{' '}
                            <ChipIntegridad estado={f.intento?.integridad?.estado} />
                            {f.asistencia?.tipo_excusa && (
                              <span className="mt-1 block text-xs text-muted-foreground">{ETIQUETA_EXCUSA[f.asistencia.tipo_excusa]}</span>
                            )}
                            {f.asistencia?.llegada_en && (
                              <span className="mt-1 block text-xs text-muted-foreground">
                                Llegó {formatoHora.format(new Date(f.asistencia.llegada_en))}
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
                            <ProgresoIntento intento={f.intento} ahoraServidor={ahoraServidor} />
                          </TableCell>
                          <TableCell className="text-right font-medium">{f.intento?.nota ?? '—'}</TableCell>
                          <TableCell>
                            {f.origen === 'cargue' && !f.intento && (
                              <Button
                                variant="ghost"
                                size="icon"
                                aria-label={`Quitar a ${f.nombre} de la convocatoria`}
                                onClick={() => void quitar(f.estudiante)}
                              >
                                <Trash2 className="h-4 w-4" aria-hidden />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </>
            )}
            {conIncidentes.length > 0 && (
              <section aria-label="Integridad académica" className="space-y-2">
                <h3 className="text-sm font-medium text-foreground">Integridad académica</h3>
                {conIncidentes.map(({ fila, integridad }) => (
                  <div key={fila.estudiante} className="space-y-1">
                    <p className="flex flex-wrap items-center gap-2 text-sm text-foreground">
                      {fila.nombre} <ChipIntegridad estado={integridad.estado} />
                    </p>
                    <PanelIntegridad
                      integridad={integridad}
                      nombre={fila.nombre}
                      urlResolver={`/evaluacion/evaluaciones/${evaluacion.id}/intentos/${fila.estudiante}/resolver/`}
                      puedeResolver={!evaluacion.supervisor}
                      motivoNoPuede={`Decide el docente supervisor (${evaluacion.supervisor_nombre ?? 'asignado'}).`}
                      alResolver={() => void cargar()}
                    />
                  </div>
                ))}
              </section>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function PanelSupervision({ evaluacion, alCambiar }: { evaluacion: EvaluacionFormal; alCambiar: () => void }) {
  const [version, setVersion] = useState(0)
  const refrescar = () => {
    setVersion((n) => n + 1)
    alCambiar()
  }
  return (
    <div className="space-y-4">
      <SeccionSupervisor evaluacion={evaluacion} alCambiar={refrescar} />
      <SeccionConvocados evaluacion={evaluacion} alCargar={refrescar} />
      {evaluacion.estado === 'publicada' && <SeccionSeguimiento key={evaluacion.id} evaluacion={evaluacion} version={version} />}
    </div>
  )
}
