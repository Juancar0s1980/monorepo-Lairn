// Asistente "Importar información" (programas, asignaturas y usuarios).
//
// Cuatro pasos reales, cada uno conectado al backend:
//   1. Elegir de dónde vienen los datos (URL recomendada, archivo o pegado).
//   2. Indicar la fuente y validarla (el backend descarga/valida sin guardar).
//   3. Revisar registro por registro qué se creará, actualizará o rechazará
//      y confirmar.
//   4. Consultar el resultado guardado.
// Un paso solo se marca completado cuando su operación terminó bien; se
// puede volver a pasos anteriores sin perder lo escrito.

import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  AlertCircle,
  ArrowLeft,
  Check,
  ClipboardPaste,
  FileJson,
  Globe,
  Loader2,
  RotateCcw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AccionImportacion, ResumenImportacion } from '@/types/academico'
import type { Importacion, ModalidadImportacion, PasoImportacion } from '../use-importacion'

const PASOS: { numero: PasoImportacion; titulo: string }[] = [
  { numero: 1, titulo: 'Origen de los datos' },
  { numero: 2, titulo: 'Fuente y validación' },
  { numero: 3, titulo: 'Revisar y confirmar' },
  { numero: 4, titulo: 'Resultado' },
]

const MODALIDADES: {
  valor: ModalidadImportacion
  titulo: string
  descripcion: string
  icono: typeof Globe
}[] = [
  {
    valor: 'url',
    titulo: 'Desde una dirección web',
    descripcion: 'Recomendado. Indica la URL (https) donde el sistema institucional publica el JSON.',
    icono: Globe,
  },
  {
    valor: 'archivo',
    titulo: 'Desde un archivo .json',
    descripcion: 'Selecciona un archivo descargado o enviado por TI (máx. 5 MB).',
    icono: FileJson,
  },
  {
    valor: 'pegado',
    titulo: 'Pegar contenido',
    descripcion: 'Para correcciones puntuales: pega el texto JSON directamente.',
    icono: ClipboardPaste,
  },
]

// Texto y estilo de cada acción, en futuro (vista previa) o pasado (resultado).
const ACCIONES: Record<AccionImportacion, { previa: string; hecho: string; clase: string }> = {
  crear: { previa: 'Se creará', hecho: 'Creado', clase: 'bg-success/10 text-success' },
  actualizar: { previa: 'Se actualizará', hecho: 'Actualizado', clase: 'bg-primary/10 text-primary' },
  sin_cambios: { previa: 'Ya registrado', hecho: 'Ya registrado', clase: 'bg-muted text-muted-foreground' },
  omitir: { previa: 'Pendiente', hecho: 'Pendiente', clase: 'bg-warning/15 text-foreground' },
  rechazar: { previa: 'Rechazado', hecho: 'Rechazado', clase: 'bg-destructive/10 text-destructive' },
}

const ENTIDADES = { programa: 'Programa', asignatura: 'Asignatura', usuario: 'Usuario', docente: 'Docente (ADR-017)' } as const

const EJEMPLO_JSON = `{
  "programas": [
    { "codigo": "ING-SIS", "nombre": "Ingeniería de Sistemas",
      "duracion": 10, "semestres": [1, 2] }
  ],
  "asignaturas": [
    { "codigo": "SIS101", "nombre": "Programación I", "creditos": 4,
      "programa_codigo": "ING-SIS", "semestre": 1 }
  ]
}`

function IndicadorPasos({ actual, alVolver }: { actual: PasoImportacion; alVolver: (p: PasoImportacion) => void }) {
  return (
    <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4" aria-label="Pasos de la importación">
      {PASOS.map((p) => {
        const completado = p.numero < actual
        const activo = p.numero === actual
        // Solo se puede volver a pasos previos, y no desde el resultado final.
        const navegable = completado && actual !== 4
        return (
          <li key={p.numero}>
            <button
              type="button"
              disabled={!navegable}
              onClick={() => alVolver(p.numero)}
              aria-current={activo ? 'step' : undefined}
              className={cn(
                'flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-xs transition-colors',
                activo && 'border-primary bg-primary/5 font-medium text-foreground',
                completado && 'border-success/40 text-foreground hover:bg-muted',
                !activo && !completado && 'border-border text-muted-foreground',
                !navegable && 'cursor-default',
              )}
            >
              <span
                className={cn(
                  'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px]',
                  completado ? 'bg-success text-primary-foreground' : activo ? 'bg-primary text-primary-foreground' : 'bg-muted',
                )}
              >
                {completado ? <Check className="h-3 w-3" aria-hidden /> : p.numero}
              </span>
              <span>{p.titulo}</span>
              {completado && <span className="sr-only">(completado)</span>}
            </button>
          </li>
        )
      })}
    </ol>
  )
}

function ConteoResumen({ r, hecho }: { r: ResumenImportacion; hecho: boolean }) {
  const cifras: { etiqueta: string; valor: number; clase: string }[] = [
    { etiqueta: hecho ? 'Creados' : 'Por crear', valor: r.creados, clase: 'text-success' },
    { etiqueta: hecho ? 'Actualizados' : 'Por actualizar', valor: r.actualizados, clase: 'text-primary' },
    { etiqueta: 'Ya registrados', valor: r.sin_cambios, clase: 'text-muted-foreground' },
    { etiqueta: 'Pendientes', valor: r.omitidos, clase: 'text-foreground' },
    { etiqueta: 'Rechazados', valor: r.rechazados, clase: 'text-destructive' },
  ]
  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {cifras.map((c) => (
        <div key={c.etiqueta} className="rounded-lg border border-border bg-card p-2 text-center">
          <dd className={cn('text-lg font-bold', c.clase)}>{c.valor}</dd>
          <dt className="text-[11px] text-muted-foreground">{c.etiqueta}</dt>
        </div>
      ))}
    </dl>
  )
}

function TablaRegistros({ r, hecho }: { r: ResumenImportacion; hecho: boolean }) {
  const [soloProblemas, setSoloProblemas] = useState(false)
  const filas = soloProblemas
    ? r.registros.filter((f) => f.accion === 'rechazar' || f.accion === 'omitir')
    : r.registros
  const hayProblemas = r.rechazados + r.omitidos > 0
  return (
    <div className="space-y-2">
      {hayProblemas && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Switch id="solo-problemas" size="sm" checked={soloProblemas} onCheckedChange={setSoloProblemas} />
          <Label htmlFor="solo-problemas" className="text-xs font-normal text-muted-foreground">
            Mostrar solo registros rechazados o pendientes
          </Label>
        </div>
      )}
      <div className="max-h-[420px] overflow-auto rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Registro</TableHead>
              <TableHead className="hidden sm:table-cell">Nombre</TableHead>
              <TableHead>Resultado</TableHead>
              <TableHead className="min-w-[180px]">Detalle</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filas.map((f, i) => (
              <TableRow key={`${f.entidad}-${f.clave}-${i}`}>
                <TableCell className="align-top">
                  <span className="block text-[11px] text-muted-foreground">{ENTIDADES[f.entidad]}</span>
                  <span className="font-mono text-xs break-all">{f.clave}</span>
                  {/* En móvil el nombre va bajo el código para no ocultarlo */}
                  <span className="block text-xs sm:hidden">{f.nombre}</span>
                </TableCell>
                <TableCell className="hidden align-top text-sm sm:table-cell">{f.nombre || '—'}</TableCell>
                <TableCell className="align-top">
                  <Badge className={cn('border-transparent whitespace-nowrap', ACCIONES[f.accion].clase)}>
                    {hecho ? ACCIONES[f.accion].hecho : ACCIONES[f.accion].previa}
                  </Badge>
                </TableCell>
                <TableCell className="align-top text-xs whitespace-normal text-muted-foreground">
                  {f.motivo || '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {r.registros_truncados && (
        <p className="text-xs text-muted-foreground">
          Se muestran los primeros {r.registros.length} registros; los conteos incluyen todos.
        </p>
      )}
    </div>
  )
}

export function AsistenteImportacion({ im }: { im: Importacion }) {
  const inputArchivo = useRef<HTMLInputElement>(null)
  const previa = im.previa
  const aImportar = previa ? previa.creados + previa.actualizados : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Importar programas y asignaturas</CardTitle>
        <CardDescription>
          Trae la oferta académica desde el sistema institucional. Primero se valida y revisa;
          nada se guarda hasta que confirmes.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <IndicadorPasos actual={im.paso} alVolver={im.setPaso} />

        {/* Paso 1: modalidad */}
        {im.paso === 1 && (
          <div role="radiogroup" aria-label="Origen de los datos" className="grid gap-3 md:grid-cols-3">
            {MODALIDADES.map((m) => (
              <button
                key={m.valor}
                type="button"
                role="radio"
                aria-checked={im.modalidad === m.valor}
                onClick={() => im.elegirModalidad(m.valor)}
                className={cn(
                  'flex flex-col items-start gap-2 rounded-xl border p-4 text-left transition-colors hover:border-primary hover:bg-primary/5 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                  im.modalidad === m.valor ? 'border-primary' : 'border-border',
                )}
              >
                <m.icono className="h-5 w-5 text-primary" aria-hidden />
                <span className="text-sm font-medium text-foreground">{m.titulo}</span>
                <span className="text-xs text-muted-foreground">{m.descripcion}</span>
              </button>
            ))}
          </div>
        )}

        {/* Paso 2: fuente + validar */}
        {im.paso === 2 && (
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault()
              im.validar()
            }}
          >
            {im.modalidad === 'url' && (
              <div className="space-y-1.5">
                <Label htmlFor="url-importacion">Dirección del recurso JSON</Label>
                <Input
                  id="url-importacion"
                  type="url"
                  inputMode="url"
                  autoComplete="off"
                  placeholder="https://api.institucion.edu.co/programas.json"
                  value={im.url}
                  onChange={(e) => im.setUrl(e.target.value)}
                  aria-invalid={!!im.errorFuente}
                  aria-describedby="ayuda-url"
                />
                <p id="ayuda-url" className="text-xs text-muted-foreground">
                  Debe empezar por https:// y responder con JSON. Por seguridad no se aceptan
                  direcciones de redes internas.
                </p>
              </div>
            )}

            {im.modalidad === 'archivo' && (
              <div className="space-y-1.5">
                <Label htmlFor="archivo-importacion">Archivo .json</Label>
                <input
                  id="archivo-importacion"
                  ref={inputArchivo}
                  type="file"
                  accept=".json,application/json"
                  className="sr-only"
                  onChange={(e) => im.leerArchivo(e.target.files?.[0] ?? null)}
                />
                <div className="flex flex-wrap items-center gap-2">
                  <Button type="button" variant="outline" onClick={() => inputArchivo.current?.click()}>
                    <FileJson className="mr-1.5 h-4 w-4" aria-hidden />
                    {im.archivo ? 'Cambiar archivo' : 'Seleccionar archivo'}
                  </Button>
                  <span className="text-xs break-all text-muted-foreground">
                    {im.archivo ? im.archivo.nombre : 'Ningún archivo seleccionado'}
                  </span>
                </div>
              </div>
            )}

            {im.modalidad === 'pegado' && (
              <div className="space-y-1.5">
                <Label htmlFor="texto-importacion">Contenido JSON</Label>
                <Textarea
                  id="texto-importacion"
                  placeholder={EJEMPLO_JSON}
                  value={im.textoPegado}
                  onChange={(e) => im.setTextoPegado(e.target.value)}
                  aria-invalid={!!im.errorFuente}
                  className="min-h-[180px] font-mono text-xs"
                />
              </div>
            )}

            <details className="rounded-lg border border-border bg-muted/50 p-3 text-xs">
              <summary className="cursor-pointer font-medium text-foreground">
                ¿Qué estructura debe tener el JSON?
              </summary>
              <div className="mt-2 space-y-2 text-muted-foreground">
                <p>
                  Listas <code>programas</code>, <code>asignaturas</code> y/o <code>usuarios</code>.
                  Obligatorios: <code>codigo</code> y <code>nombre</code>; las asignaturas además
                  <code> programa_codigo</code>. Si el código ya existe, el registro se actualiza
                  (nunca se duplica). Los usuarios solo se verifican: las cuentas las crea TI.
                </p>
                <pre className="overflow-x-auto rounded bg-card p-2 font-mono">{EJEMPLO_JSON}</pre>
              </div>
            </details>

            {im.errorFuente && (
              <p role="alert" className="flex items-start gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                {im.errorFuente}
              </p>
            )}

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <Button type="button" variant="ghost" onClick={() => im.setPaso(1)}>
                <ArrowLeft className="mr-1.5 h-4 w-4" aria-hidden />
                Cambiar origen
              </Button>
              <Button type="submit" disabled={im.validando}>
                {im.validando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
                {im.validando ? 'Validando…' : 'Validar datos'}
              </Button>
            </div>
          </form>
        )}

        {/* Paso 3: revisar + confirmar */}
        {im.paso === 3 && previa && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Se recibieron {previa.total_recibidos} registros. Revisa qué pasará con cada uno;
              aún no se ha guardado nada.
            </p>
            <ConteoResumen r={previa} hecho={false} />
            <TablaRegistros r={previa} hecho={false} />
            {previa.rechazados > 0 && (
              <p className="text-xs text-muted-foreground">
                Los registros rechazados no se importarán. Corrígelos en la fuente y vuelve a validar,
                o confirma para importar solo los válidos.
              </p>
            )}
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <Button type="button" variant="ghost" onClick={() => im.setPaso(2)} disabled={im.confirmando}>
                <ArrowLeft className="mr-1.5 h-4 w-4" aria-hidden />
                Volver a la fuente
              </Button>
              <Button onClick={im.confirmar} disabled={im.confirmando || aImportar === 0}>
                {im.confirmando && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" aria-hidden />}
                {aImportar === 0
                  ? 'No hay registros para importar'
                  : im.confirmando
                    ? 'Importando…'
                    : `Confirmar importación (${aImportar})`}
              </Button>
            </div>
          </div>
        )}

        {/* Paso 4: resultado */}
        {im.paso === 4 && im.resultado && (
          <div className="space-y-4">
            <p role="status" className="flex items-start gap-2 rounded-lg bg-success/10 p-3 text-sm text-foreground">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden />
              Importación guardada. Los programas y asignaturas ya aparecen en sus pestañas.
              (Bitácora #{im.resultado.registro_id})
            </p>
            <ConteoResumen r={im.resultado} hecho />
            <TablaRegistros r={im.resultado} hecho />
            <div className="flex justify-end">
              <Button variant="outline" onClick={im.reiniciar}>
                <RotateCcw className="mr-1.5 h-4 w-4" aria-hidden />
                Nueva importación
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
