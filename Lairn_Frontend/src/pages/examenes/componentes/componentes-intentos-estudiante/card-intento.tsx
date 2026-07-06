// Card reutilizable que muestra el resumen de un intento de examen.
//
// Muestra: header con gradiente, fila compacta de métricas (puntaje, correctas,
// nota) y badge de Aprobado/Reprobado.

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import type { Resultado } from '@/types/analitica'
import { UMBRAL_APROBACION } from '../../utilidades'

export function CardIntento({
  intento,
  indice,
  color,
}: {
  intento: Resultado
  indice: number
  color: string
}) {
  const aprobado = intento.nota >= UMBRAL_APROBACION

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="pb-3"
        style={{
          background: `linear-gradient(135deg, ${color}22, ${color}08)`,
        }}
      >
        <CardTitle className="flex items-center justify-between text-sm">
          <span>Intento #{indice + 1}</span>
          <span className="text-xs font-normal text-muted-foreground">
            {new Date(intento.completado_en).toLocaleDateString('es-CL')}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        {/* Resumen compacto: misma lógica visual que el resto de cards (métricas + separadores). */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground ">
          <div className="flex items-center gap-1.5">
            <span>Puntaje:</span>
            <span className="font-semibold" style={{ color }}>
              {intento.puntaje}%
            </span>
          </div>
          <div className="hidden sm:block h-3 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <span>Correctas:</span>
            <span className="font-semibold text-foreground">
              {intento.correctas}/{intento.total_preguntas}
            </span>
          </div>
          <div className="hidden sm:block h-3 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <span>Nota:</span>
            <span className="font-semibold text-foreground">{intento.nota}</span>
          </div>
          <div className="hidden sm:block h-3 w-px bg-border" />
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              aprobado
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                : 'bg-destructive/10 text-destructive'
            }`}
          >
            {aprobado ? 'Aprobado' : 'Reprobado'}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
