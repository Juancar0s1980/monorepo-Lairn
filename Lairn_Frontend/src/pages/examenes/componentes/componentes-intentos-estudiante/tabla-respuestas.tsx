// Tabla de detalle de respuestas de un intento de examen.
//
// Muestra: concepto, pregunta, respuesta del usuario, respuesta correcta,
// dificultad, tiempo por pregunta y resultado (correcta/incorrecta).

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Check, X } from 'lucide-react'
import type { Respuesta } from '@/types/analitica'

export function TablaRespuestas({
  respuestas,
}: {
  respuestas: Respuesta[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Detalle de respuestas</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 pr-3 font-medium">Concepto</th>
                <th className="pb-2 pr-3 font-medium">Pregunta</th>
                <th className="pb-2 pr-3 font-medium">Tu respuesta</th>
                <th className="pb-2 pr-3 font-medium">Correcta</th>
                <th className="pb-2 pr-3 font-medium">Dificultad</th>
                <th className="pb-2 pr-3 font-medium">Tiempo</th>
                <th className="pb-2 font-medium">Resultado</th>
              </tr>
            </thead>
            <tbody>
              {respuestas.map((resp, i) => {
                const esCorrecta = !resp.respuesta_incorrecta
                return (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2.5 pr-3 align-top">
                      <span className="text-xs">{resp.concepto}</span>
                    </td>
                    <td className="py-2.5 pr-3 align-top">
                      <span className="line-clamp-2">{resp.pregunta}</span>
                    </td>
                    <td className="py-2.5 pr-3 align-top">
                      <span
                        className={
                          esCorrecta
                            ? 'text-foreground'
                            : 'text-destructive'
                        }
                      >
                        {esCorrecta ? '—' : resp.respuesta_incorrecta}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 align-top">
                      <span className="text-foreground">
                        {resp.respuesta_correcta}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 align-top">
                      <span className="rounded-md bg-muted px-1.5 py-0.5 text-xs">
                        {resp.dificultad === 1
                          ? 'Básico'
                          : resp.dificultad === 2
                            ? 'Intermedio'
                            : 'Avanzado'}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 align-top">
                      <span className="text-muted-foreground">
                        {resp.tiempo_por_pregunta}s
                      </span>
                    </td>
                    <td className="py-2.5 align-top">
                      {esCorrecta ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600 dark:text-green-400">
                          <Check className="h-3 w-3" /> Correcta
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
                          <X className="h-3 w-3" /> Incorrecta
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
