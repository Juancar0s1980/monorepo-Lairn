// Vista previa de un cargue de estudiantes (ADR-009 + ADR-012), reutilizada en:
//   - el cargue de convocados de una evaluación (Coordinador/Administrador);
//   - la validación global de un archivo (Administrador).
// Muestra por fila: estado, datos del archivo (nombre, programa, semestre,
// código si vienen) frente a la cuenta del sistema y las diferencias, que
// SOLO se informan: nunca se sobrescriben datos ni se crean cuentas.

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { EstadoCargue, InformeCargue } from '@/types/supervision'
import { ESTADOS_CARGUE } from './estados-cargue'

const CAMPOS: { clave: 'nombre' | 'codigo' | 'programa' | 'semestre'; etiqueta: string }[] = [
  { clave: 'nombre', etiqueta: 'Nombre' },
  { clave: 'codigo', etiqueta: 'Código' },
  { clave: 'programa', etiqueta: 'Programa' },
  { clave: 'semestre', etiqueta: 'Semestre' },
]

export function ResumenCargue({ informe }: { informe: InformeCargue }) {
  return (
    <div className="flex flex-wrap gap-1.5" role="status">
      {(Object.keys(ESTADOS_CARGUE) as EstadoCargue[])
        .filter((k) => (informe.totales[k] ?? 0) > 0)
        .map((k) => (
          <Badge key={k} className={cn('border-transparent', ESTADOS_CARGUE[k].clase)}>
            {ESTADOS_CARGUE[k].texto}: {informe.totales[k]}
          </Badge>
        ))}
      {informe.con_diferencias > 0 && (
        <Badge variant="outline" className="border-warning/60 text-foreground">
          Datos distintos al sistema: {informe.con_diferencias}
        </Badge>
      )}
    </div>
  )
}

export function TablaVistaPrevia({ informe }: { informe: InformeCargue }) {
  return (
    <div className="max-h-80 overflow-y-auto rounded-xl border border-border">
      <ul className="divide-y divide-border text-sm">
        {informe.filas.map((f) => {
          const conArchivo = CAMPOS.filter((c) => f.archivo?.[c.clave])
          return (
            <li key={f.fila} className="space-y-1.5 p-2.5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <span className="min-w-0">
                  <span className="block break-all text-foreground">{f.correo || '(sin correo)'}</span>
                  <span className="block text-xs text-muted-foreground">
                    Fila {f.fila}
                    {f.nombre && ` · Cuenta: ${f.nombre}`}
                    {f.origen && ` · convocado por ${f.origen === 'curso' ? 'curso' : 'cargue anterior'}`}
                  </span>
                </span>
                <Badge className={cn('shrink-0 border-transparent', ESTADOS_CARGUE[f.estado].clase)}>
                  {ESTADOS_CARGUE[f.estado].texto}
                </Badge>
              </div>
              {conArchivo.length > 0 && (
                <dl className="grid grid-cols-1 gap-x-4 gap-y-0.5 text-xs sm:grid-cols-2">
                  {conArchivo.map((c) => {
                    const difiere = f.diferencias?.includes(c.clave)
                    const enSistema = f.sistema?.[c.clave]
                    return (
                      <div key={c.clave} className="flex min-w-0 gap-1">
                        <dt className="shrink-0 text-muted-foreground">{c.etiqueta}:</dt>
                        <dd className={cn('min-w-0 break-words', difiere ? 'text-foreground' : 'text-muted-foreground')}>
                          {f.archivo[c.clave]} <span className="italic">(dato del archivo)</span>
                          {difiere && (
                            <span className="block text-warning">
                              En el sistema: {enSistema ?? 'sin dato'} · no se sobrescribe
                            </span>
                          )}
                        </dd>
                      </div>
                    )
                  })}
                </dl>
              )}
              {f.sistema && !f.sistema.tiene_perfil && conArchivo.some((c) => c.clave !== 'nombre') && (
                <p className="text-xs text-muted-foreground">La cuenta no tiene perfil académico: el código, programa y semestre se muestran solo como dato del archivo.</p>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
