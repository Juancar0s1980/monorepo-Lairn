// Tab de laboratorios de código del curso (vista del estudiante).
//
// Lista los laboratorios disponibles; cada card lleva a la página de
// resolución estilo "juez en línea" en /mis-cursos/{cursoId}/laboratorios/{id}.
//
// Endpoint: GET /laboratorios/mis-cursos/{cursoId}/laboratorios/.

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Code2, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import type { Laboratorio } from '@/types/laboratorio'

interface TabLaboratoriosEstudianteProps {
  cursoId: string
}

export function TabLaboratoriosEstudiante({ cursoId }: TabLaboratoriosEstudianteProps) {
  const navigate = useNavigate()
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<Laboratorio[]>(
          `/laboratorios/mis-cursos/${cursoId}/laboratorios/`,
          { signal: controlador.signal }
        )
        setLaboratorios(data)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudieron cargar los laboratorios')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId])

  if (cargando) {
    return (
      <div className="flex h-[30vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (laboratorios.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <Code2 className="h-10 w-10 text-muted-foreground/50" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          Aún no hay laboratorios disponibles
        </p>
        <p className="text-xs text-muted-foreground">
          Aparecerán aquí cuando el docente los publique
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {laboratorios.map((lab) => (
        <Card
          key={lab.id}
          className="cursor-pointer overflow-hidden transition-colors hover:border-primary/40"
          onClick={() => navigate(`/mis-cursos/${cursoId}/laboratorios/${lab.id}`)}
        >
          <CardHeader className="pb-3">
            <CardTitle className="text-sm line-clamp-1">{lab.titulo}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="line-clamp-2 text-xs text-muted-foreground">
              {lab.instrucciones || 'Sin instrucciones adicionales'}
            </p>
            <Badge variant="outline" className="text-xs">
              {lab.total_preguntas} pregunta{lab.total_preguntas === 1 ? '' : 's'}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
