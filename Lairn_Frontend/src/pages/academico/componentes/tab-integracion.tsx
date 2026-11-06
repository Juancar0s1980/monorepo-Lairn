// Pestaña "Importar información": asistente de importación (URL, archivo o
// JSON pegado) + documentos institucionales procesados por IA (pensum,
// resolución, plan de aula) que se revisan antes de incorporarlos.

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
import { Eye, Loader2, Trash2, Upload } from 'lucide-react'
import type { Academico } from '../use-academico'
import { DialogoRevisionCargue } from './revision-cargue'
import { AsistenteImportacion } from './asistente-importacion'

export function TabIntegracion({ ac }: { ac: Academico }) {
  const inputPdf = useRef<HTMLInputElement>(null)
  const [archivoNombre, setArchivoNombre] = useState('')

  return (
    <div className="space-y-4">
      {/* Importación guiada desde URL / archivo / pegado */}
      <AsistenteImportacion im={ac.importacion} />

      {/* Cargues documentales */}
      <Card>
        <CardHeader>
          <CardTitle>Documentos institucionales</CardTitle>
          <CardDescription>
            Sube el pensum, la resolución o un plan de aula en PDF. La IA propone la información
            y tú la revisas antes de incorporarla al programa.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Subida de PDF: antes no tenía UI y el endpoint parecía no usarse */}
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted p-3">
            <Select
              value={ac.tipoPdf}
              items={[
                { value: 'pensum', label: 'Pensum' },
                { value: 'resolucion', label: 'Resolución' },
                { value: 'plan_aula', label: 'Plan de aula' },
              ]}
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

          <div className="overflow-x-auto">
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
          </div>
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
