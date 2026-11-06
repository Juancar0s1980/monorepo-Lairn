// Estudiantes convocados e inscritos (ADR-012).
//
// - Administrador y Coordinador: todos los programas; filtros por programa,
//   momento y evaluación (`GET /evaluacion/estudiantes/`).
// - Docente: solo los estudiantes de sus cursos y de las evaluaciones que
//   supervisa (`GET /evaluacion/docente/estudiantes/`).
// - Filtro por estado (inscrito, convocado por curso/cargue, presente,
//   presentó, no ha presentado, suspendido, anulado), búsqueda, paginación en
//   el servidor y exportación CSV/Excel con los mismos filtros.
// - Administrador: validación global de un archivo de estudiantes (solo informa).
// No confundir: inscripción (curso) ≠ convocatoria (evaluación) ≠ asistencia
// (llamado a lista) ≠ participación (presentó). Las cuentas las crea TI.

import { useEffect, useRef, useState } from 'react'
import api from '@/services/api'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EncabezadoPagina } from '@/components/encabezado-pagina'
import { ChevronLeft, ChevronRight, FileSpreadsheet, FileText, Loader2, Search, ShieldCheck, Upload } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/contexto-auth/use-auth'
import { ROLES } from '@/types/usuario'
import type { EstadoEstudiante, FilaEstudiante, ListadoEstudiantes } from '@/types/estudiantes'
import type { InformeCargue } from '@/types/supervision'
import { mensajeError } from '@/pages/academico/academico-utils'
import { descargarArchivo } from '@/pages/tareas/utilidades-tareas'
import { ResumenCargue, TablaVistaPrevia } from './vista-previa-cargue'

const TODOS = 'todos'
const ORDEN_ESTADOS: EstadoEstudiante[] = [
  'inscrito',
  'convocado_curso',
  'convocado_cargue',
  'presente',
  'presento',
  'no_presento',
  'suspendido',
  'anulado',
]
const CLASE_ESTADO: Record<EstadoEstudiante, string> = {
  inscrito: 'bg-muted text-foreground',
  convocado_curso: 'bg-primary/10 text-primary',
  convocado_cargue: 'bg-primary/10 text-primary',
  presente: 'bg-success/10 text-success',
  presento: 'bg-success/10 text-success',
  no_presento: 'bg-warning/15 text-foreground',
  suspendido: 'bg-destructive/10 text-destructive',
  anulado: 'bg-destructive/10 text-destructive',
}

type Opcion = { id: number; nombre: string }

function SelectorSimple({
  id,
  etiqueta,
  valor,
  opciones,
  alCambiar,
  deshabilitado,
}: {
  id: string
  etiqueta: string
  valor: string
  opciones: Opcion[]
  alCambiar: (v: string) => void
  deshabilitado?: boolean
}) {
  const items = [{ value: TODOS, label: 'Todos' }, ...opciones.map((o) => ({ value: String(o.id), label: o.nombre }))]
  return (
    <div className="min-w-0 space-y-1">
      <Label htmlFor={id} className="text-xs text-muted-foreground">
        {etiqueta}
      </Label>
      <Select value={valor || TODOS} onValueChange={(v) => alCambiar(!v || v === TODOS ? '' : v)} items={items} disabled={deshabilitado}>
        <SelectTrigger id={id} className="w-full min-w-0">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {items.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

function EstadosFila({ fila, etiquetas }: { fila: FilaEstudiante; etiquetas: ListadoEstudiantes['estados'] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {ORDEN_ESTADOS.filter((e) => fila.estados.includes(e)).map((e) => (
        <Badge key={e} className={cn('border-transparent font-normal', CLASE_ESTADO[e])}>
          {etiquetas[e]}
        </Badge>
      ))}
    </div>
  )
}

function textoEnEvaluacion(f: FilaEstudiante): string | null {
  const ev = f.en_evaluacion
  if (!ev) return null
  const partes = [ev.origen ? `Convocado por ${ev.origen}` : 'No convocado']
  partes.push(ev.presente ? 'presente en sala' : 'sin asistencia registrada')
  if (ev.integridad === 'anulado_fraude') partes.push('anulado por fraude')
  else if (ev.integridad === 'suspendido') partes.push('suspendido')
  else if (ev.intento === 'enviado') partes.push('presentó')
  else if (ev.intento === 'en_curso') partes.push('en curso')
  else partes.push('sin iniciar')
  return partes.join(' · ')
}

function ValidacionGlobal() {
  const entrada = useRef<HTMLInputElement>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [informe, setInforme] = useState<InformeCargue | null>(null)
  const [enviando, setEnviando] = useState(false)

  const validar = async () => {
    if (!archivo) return
    const datos = new FormData()
    datos.append('archivo', archivo)
    setEnviando(true)
    try {
      const r = await api.post<InformeCargue>('/evaluacion/estudiantes/validar/', datos, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setInforme(r.data)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo validar el archivo'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="h-4 w-4 text-primary" aria-hidden />
          Validar archivo de estudiantes
        </CardTitle>
        <CardDescription>
          Revisa un CSV o Excel contra el sistema: si cada correo tiene cuenta y es de estudiante, y si el nombre, código,
          programa o semestre del archivo coinciden con su perfil. Solo informa: no crea ni modifica cuentas (eso es de TI).
          Para convocar a una evaluación, usa el cargue dentro de la evaluación.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            ref={entrada}
            type="file"
            accept=".csv,.xlsx"
            aria-label="Archivo de estudiantes (.csv o .xlsx)"
            className="min-w-0 text-sm file:mr-3 file:rounded-lg file:border file:border-border file:bg-muted file:px-3 file:py-1.5 file:text-sm"
            onChange={(e) => {
              setArchivo(e.target.files?.[0] ?? null)
              setInforme(null)
            }}
          />
          <Button variant="outline" onClick={() => void validar()} disabled={!archivo || enviando}>
            {enviando ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <Upload className="mr-1.5 h-4 w-4" aria-hidden />}
            Validar
          </Button>
        </div>
        {informe && (
          <div className="space-y-3">
            <ResumenCargue informe={informe} />
            <TablaVistaPrevia informe={informe} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function PaginaEstudiantes() {
  const { rol } = useAuth()
  const esDocente = rol === ROLES.DOCENTE
  const esAdmin = rol === ROLES.ADMIN
  const base = esDocente ? '/evaluacion/docente/estudiantes/' : '/evaluacion/estudiantes/'

  const [programa, setPrograma] = useState('')
  const [momento, setMomento] = useState('')
  const [evaluacion, setEvaluacion] = useState('')
  const [estado, setEstado] = useState<EstadoEstudiante | ''>('')
  const [texto, setTexto] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)
  const [programas, setProgramas] = useState<Opcion[]>([])
  const [momentos, setMomentos] = useState<Opcion[]>([])
  const [datos, setDatos] = useState<ListadoEstudiantes | null>(null)
  const [error, setError] = useState('')
  const [claveCargada, setClaveCargada] = useState<string | null>(null)
  const [exportando, setExportando] = useState<'csv' | 'xlsx' | null>(null)

  // La búsqueda se aplica 400 ms después de dejar de escribir.
  useEffect(() => {
    const id = window.setTimeout(() => {
      setBuscar(texto.trim())
      setPagina(1)
    }, 400)
    return () => window.clearTimeout(id)
  }, [texto])

  useEffect(() => {
    if (esDocente) return
    api
      .get<{ id: number; codigo: string; nombre: string }[]>('/evaluacion/programas/')
      .then((r) => setProgramas((Array.isArray(r.data) ? r.data : []).map((p) => ({ id: p.id, nombre: `${p.codigo} · ${p.nombre}` }))))
      .catch(() => setProgramas([]))
  }, [esDocente])

  useEffect(() => {
    if (esDocente || !programa) return
    api
      .get<{ id: number; nombre: string }[]>(`/evaluacion/programas/${programa}/momentos/`)
      .then((r) => setMomentos((Array.isArray(r.data) ? r.data : []).map((m) => ({ id: m.id, nombre: m.nombre }))))
      .catch(() => setMomentos([]))
  }, [esDocente, programa])

  const params = new URLSearchParams()
  if (programa) params.set('programa', programa)
  if (momento) params.set('momento', momento)
  if (evaluacion) params.set('evaluacion', evaluacion)
  if (estado) params.set('estado', estado)
  if (buscar) params.set('buscar', buscar)
  const consulta = params.toString()
  const claveActual = `${base}?${consulta}&pagina=${pagina}`
  const cargando = claveCargada !== claveActual

  useEffect(() => {
    let activo = true
    const q = new URLSearchParams(consulta)
    q.set('pagina', String(pagina))
    q.set('tamano', '25')
    const clave = `${base}?${consulta}&pagina=${pagina}`
    api
      .get<ListadoEstudiantes>(`${base}?${q.toString()}`)
      .then((r) => {
        if (activo) {
          setDatos(r.data)
          setError('')
        }
      })
      .catch((err: unknown) => activo && setError(mensajeError(err, 'No se pudo cargar el listado.')))
      .finally(() => activo && setClaveCargada(clave))
    return () => {
      activo = false
    }
  }, [base, consulta, pagina])

  const cambiar = (accion: () => void) => {
    accion()
    setPagina(1)
  }

  const exportar = async (formato: 'csv' | 'xlsx') => {
    setExportando(formato)
    try {
      const q = new URLSearchParams(consulta)
      q.set('formato', formato)
      await descargarArchivo(`${base}?${q.toString()}`, `estudiantes.${formato}`)
    } catch (err: unknown) {
      toast.error(mensajeError(err, 'No se pudo exportar'))
    } finally {
      setExportando(null)
    }
  }

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        eyebrow={esDocente ? 'Panel del docente' : 'Gestión académica'}
        titulo="Estudiantes convocados e inscritos"
        subtitulo={
          esDocente
            ? 'Estudiantes de tus cursos y de las evaluaciones que supervisas.'
            : 'Inscripción en cursos, convocatoria a evaluaciones, asistencia en sala y participación.'
        }
        accion={
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" onClick={() => void exportar('csv')} disabled={!datos?.total || exportando !== null}>
              {exportando === 'csv' ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <FileText className="mr-1.5 h-4 w-4" aria-hidden />}
              Exportar CSV
            </Button>
            <Button variant="outline" onClick={() => void exportar('xlsx')} disabled={!datos?.total || exportando !== null}>
              {exportando === 'xlsx' ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden /> : <FileSpreadsheet className="mr-1.5 h-4 w-4" aria-hidden />}
              Exportar Excel
            </Button>
          </div>
        }
      />

      <Card>
        <CardContent className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
          {!esDocente && (
            <>
              <SelectorSimple
                id="est-programa"
                etiqueta="Programa"
                valor={programa}
                opciones={programas}
                alCambiar={(v) => cambiar(() => { setPrograma(v); setMomento(''); setEvaluacion(''); setMomentos([]) })}
              />
              <SelectorSimple
                id="est-momento"
                etiqueta="Momento"
                valor={momento}
                opciones={momentos}
                deshabilitado={!programa}
                alCambiar={(v) => cambiar(() => { setMomento(v); setEvaluacion('') })}
              />
            </>
          )}
          <SelectorSimple
            id="est-evaluacion"
            etiqueta="Evaluación"
            valor={evaluacion}
            opciones={datos?.evaluaciones ?? []}
            alCambiar={(v) => cambiar(() => setEvaluacion(v))}
          />
          <div className="min-w-0 space-y-1">
            <Label htmlFor="est-buscar" className="text-xs text-muted-foreground">Buscar</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
              <Input id="est-buscar" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Nombre, correo o código" className="pl-8" />
            </div>
          </div>
        </CardContent>
      </Card>

      {datos && (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar por estado">
          <button
            type="button"
            aria-pressed={!estado}
            onClick={() => cambiar(() => setEstado(''))}
            className={cn('rounded-full border px-3 py-1 text-xs focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none', !estado ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted')}
          >
            Todos
          </button>
          {ORDEN_ESTADOS.map((e) => (
            <button
              key={e}
              type="button"
              aria-pressed={estado === e}
              onClick={() => cambiar(() => setEstado(estado === e ? '' : e))}
              className={cn('rounded-full border px-3 py-1 text-xs focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none', estado === e ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted')}
            >
              {datos.estados[e]} <span className="tabular-nums">({datos.conteos[e]})</span>
            </button>
          ))}
        </div>
      )}

      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {!datos && cargando ? (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Cargando" />
        </div>
      ) : datos && datos.filas.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            {esDocente
              ? 'No hay estudiantes en tus cursos ni en evaluaciones que supervises con estos filtros.'
              : 'No hay estudiantes inscritos o convocados con estos filtros.'}
          </CardContent>
        </Card>
      ) : datos ? (
        <div className={cn('space-y-3 transition-opacity', cargando && 'opacity-60')}>
          {datos.evaluacion && <p className="text-sm text-muted-foreground">Detalle de la evaluación: <strong className="text-foreground">{datos.evaluacion.nombre}</strong></p>}
          {/* Móvil: tarjetas */}
          <ul className="space-y-2 md:hidden">
            {datos.filas.map((f) => (
              <li key={f.estudiante} className="space-y-1.5 rounded-xl border border-border bg-card p-3">
                <p className="font-medium text-foreground">{f.nombre}</p>
                <p className="text-xs break-all text-muted-foreground">
                  {f.email}
                  {f.codigo && ` · ${f.codigo}`}
                </p>
                {f.cursos.length > 0 && <p className="text-xs text-muted-foreground">Cursos: {f.cursos.join(', ')}</p>}
                <p className="text-xs text-muted-foreground">
                  {textoEnEvaluacion(f) ?? `${f.convocatorias} convocatoria(s) · presentó ${f.presento}`}
                </p>
                <EstadosFila fila={f} etiquetas={datos.estados} />
              </li>
            ))}
          </ul>
          <div className="hidden md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Estudiante</TableHead>
                  <TableHead>Cursos inscritos</TableHead>
                  <TableHead className="text-right">{datos.evaluacion ? 'En la evaluación' : 'Convoc. / presentó'}</TableHead>
                  <TableHead>Estados</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datos.filas.map((f) => (
                  <TableRow key={f.estudiante}>
                    <TableCell className="whitespace-normal">
                      <span className="block font-medium text-foreground">{f.nombre}</span>
                      <span className="block text-xs text-muted-foreground">
                        {f.email}
                        {f.codigo && ` · ${f.codigo}`}
                        {f.programa && ` · ${f.programa}`}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs whitespace-normal text-muted-foreground">{f.cursos.join(', ') || '—'}</TableCell>
                    <TableCell className="text-right text-xs whitespace-normal tabular-nums">
                      {textoEnEvaluacion(f) ?? `${f.convocatorias} / ${f.presento}`}
                    </TableCell>
                    <TableCell className="whitespace-normal">
                      <EstadosFila fila={f} etiquetas={datos.estados} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <nav aria-label="Paginación" className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="text-muted-foreground">
              {datos.total} estudiante(s) · página {datos.pagina} de {datos.paginas}
            </span>
            <span className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPagina((p) => p - 1)} disabled={datos.pagina <= 1 || cargando}>
                <ChevronLeft className="mr-1 h-4 w-4" aria-hidden />
                Anterior
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPagina((p) => p + 1)} disabled={datos.pagina >= datos.paginas || cargando}>
                Siguiente
                <ChevronRight className="ml-1 h-4 w-4" aria-hidden />
              </Button>
            </span>
          </nav>
        </div>
      ) : null}

      {esAdmin && <ValidacionGlobal />}
    </div>
  )
}
