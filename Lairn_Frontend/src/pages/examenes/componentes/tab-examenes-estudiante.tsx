// Tab de exámenes para el estudiante.
//
// Muestra un grid de cards con los exámenes disponibles del curso.
// Cada card muestra estado de intentos previos y botón contextual.

import { CardExamen } from '@/components/card-examen'
import { FileText } from 'lucide-react'
import type { Examen } from '@/types/examen'
import type { EstadoExamen } from '@/hooks/use-examenes-curso'

interface TabExamenesEstudianteProps {
  examenes: Examen[]
  estadoPorExamen: Map<number, EstadoExamen>
  cursoId: number
}

export function TabExamenesEstudiante({
  examenes,
  estadoPorExamen,
  cursoId,
}: TabExamenesEstudianteProps) {
  return (
    <div className="space-y-4">
      {/* Estado vacío */}
      {examenes.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
          <FileText className="h-10 w-10 text-muted-foreground/50" />
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            No hay exámenes disponibles
          </p>
          <p className="text-xs text-muted-foreground">
            Tu docente aún no ha publicado exámenes en este curso
          </p>
        </div>
      )}

      {/* Grid de cards de exámenes */}
      {examenes.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {examenes.map((examen) => {
            const estado = estadoPorExamen.get(examen.id)
            return (
              <CardExamen
                key={examen.id}
                id={examen.id}
                cursoId={cursoId}
                titulo={examen.titulo}
                tema={examen.tema}
                dificultad={examen.dificultad_inicial}
                numPreguntas={examen.num_preguntas}
                tiempo={examen.tiempo}
                maxIntentos={examen.max_intentos}
                fechaLimite={examen.fecha_limite}
                ultimaNota={estado?.ultimaNota}
                intentosUsados={estado?.intentosUsados}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
