// Tab de Integración: importar JSON NOVA + subir PDF + aprobar cargues.
// Antes solo existía el importar JSON; la subida de PDF y el aprobar
// existían en el backend pero no tenían UI, así que el flujo documental
// parecía roto.

import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Eye, FileUp, Loader2, Trash2, Upload } from 'lucide-react'
import type { Academico } from '../use-academico'
import { DialogoRevisionCargue } from './revision-cargue'

export function TabIntegracion({ ac }: { ac: Academico }) {
  const inputPdf = useRef<HTMLInputElement>(null)
  const [archivoNombre, setArchivoNombre] = useState('')

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Importar JSON NOVA */}
      <Card>
        <CardHeader>
          <CardTitle>Importar desde NOVA (JSON)</CardTitle>
          <CardDescription>
            Estructura del correo de TI: programas, asignaturas, usuarios
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Select
              value={ac.modoImportacion}
              onValueChange={(v) => ac.setModoImportacion(v as 'simulacro' | 'real')}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simulacro">Simulacro (dry-run)</SelectItem>
                <SelectItem value="real">Real (escribe)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {ac.modoImportacion === 'simulacro'
                ? 'Valida sin escribir nada'
                : 'Upsert idempotente por external_id'}
            </p>
          </div>
          <Textarea
            placeholder='{"programas": [{"codigo": "...", "nombre": "..."}], "asignaturas": [...], "usuarios": [...]}'
            value={ac.jsonNOVA}
            onChange={(e) => ac.setJsonNOVA(e.target.value)}
            className="min-h-[160px] font-mono text-xs"
          />
          <Button onClick={ac.importarNOVA} disabled={ac.importando}>
            {ac.importando ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <FileUp className="h-4 w-4 mr-1.5" />
            )}
            Importar
          </Button>

          {ac.resumenImportacion && (
            <Card className="border-border bg-muted">
              <CardContent className="space-y-2 p-4">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={ac.resumenImportacion.modo === 'simulacro' ? 'secondary' : 'default'}
                    className="bg-primary text-primary-foreground border-transparent"
                  >
                    {ac.resumenImportacion.modo}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Registro de bitácora #{ac.resumenImportacion.registro_id}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="rounded-lg bg-card p-2">
                    <p className="text-lg font-bold text-primary">{ac.resumenImportacion.creados}</p>
                    <p className="text-[10px] text-muted-foreground">Crear</p>
                  </div>
                  <div className="rounded-lg bg-card p-2">
                    <p className="text-lg font-bold text-accent-foreground">
                      {ac.resumenImportacion.actualizados}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Actualizar</p>
                  </div>
                  <div className="rounded-lg bg-card p-2">
                    <p className="text-lg font-bold text-muted-foreground">
                      {ac.resumenImportacion.omitidos}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Omitir</p>
                  </div>
                  <div className="rounded-lg bg-card p-2">
                    <p className="text-lg font-bold text-foreground">
                      {ac.resumenImportacion.total_recibidos}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Total</p>
                  </div>
                </div>
                {ac.resumenImportacion.errores.length > 0 && (
                  <ul className="space-y-1">
                    {ac.resumenImportacion.errores.map((e, i) => (
                      <li key={i} className="text-xs text-destructive">
                        • {e}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      {/* Cargues documentales */}
      <Card>
        <CardHeader>
          <CardTitle>Cargues documentales (IA)</CardTitle>
          <CardDescription>Pensum / resolución / plan de aula procesados</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Subida de PDF: antes no tenía UI y el endpoint parecía no usarse */}
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted p-3">
            <Select
              value={ac.tipoPdf}
              onValueChange={(v) =>
                ac.setTipoPdf(v as 'pensum' | 'resolucion' | 'plan_aula')
              }
            >
              <SelectTrigger className="w-[160px] bg-card">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pensum">Pensum</SelectItem>
                <SelectItem value="resolucion">Resolución</SelectItem>
                <SelectItem value="plan_aula">Plan de aula</SelectItem>
              </SelectContent>
            </Select>
            <input
              ref={inputPdf}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => setArchivoNombre(e.target.files?.[0]?.name ?? '')}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => inputPdf.current?.click()}
              title="Elegir PDF (máx 10 MB, con texto seleccionable)"
            >
              <Upload className="h-4 w-4 mr-1.5" />
              {archivoNombre || 'Elegir PDF'}
            </Button>
            <Button
              size="sm"
              disabled={ac.subiendoPdf || !archivoNombre}
              onClick={() => ac.subirPdf(inputPdf.current?.files?.[0] ?? null)}
            >
              {ac.subiendoPdf && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              Subir y procesar
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Documento</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Programa</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ac.cargues.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.nombre_archivo}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {c.tipo.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {c.programa_nombre ?? '—'}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        c.estado === 'aprobado'
                          ? 'secondary'
                          : c.estado === 'fallido'
                            ? 'destructive'
                            : 'outline'
                      }
                      className={
                        c.estado === 'aprobado'
                          ? 'bg-success/10 text-success border-transparent'
                          : ''
                      }
                    >
                      {c.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => ac.setRevisandoCargue(c)}
                        title="Revisar propuesta e incorporar al programa"
                      >
                        <Eye className="h-4 w-4 text-primary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          ac.setConfirmacion({ tipo: 'cargue', id: c.id, nombre: c.nombre_archivo })
                        }
                        title="Eliminar cargue (solo si aún no fue aprobado)"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {!ac.cargues.length && (
            <p className="text-sm text-muted-foreground">
              Sin cargues todavía. Sube un PDF para generar la propuesta IA, revísala
              y apruébala para que aparezca en el programa.
            </p>
          )}
        </CardContent>
      </Card>
      {/* Revisión previa antes de incorporar al programa */}
      <DialogoRevisionCargue ac={ac} />
    </div>
  )
}
