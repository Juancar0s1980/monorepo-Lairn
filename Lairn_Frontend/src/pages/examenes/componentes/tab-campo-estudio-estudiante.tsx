// Tab de Campo de Estudio del curso (vista del estudiante).
//
// Lista los temas de estudio APROBADOS del curso; cada card abre el chat
// del tema en /mis-cursos/{cursoId}/campo-estudio/{temaId}. Si el docente no
// activó la función, el backend responde 403 y se muestra un estado vacío
// explicativo en vez de una lista.
//
// Endpoint: GET /campo-estudio/mis-cursos/{cursoId}/temas/.

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Lightbulb, Loader2, MessageCircleQuestion } from 'lucide-react'
import { toast } from 'sonner'
import type { TemaEstudio } from '@/types/campo-estudio'

interface TabCampoEstudioEstudianteProps {
  cursoId: string
}

export function TabCampoEstudioEstudiante({ cursoId }: TabCampoEstudioEstudianteProps) {
  const navigate = useNavigate()
  const [temas, setTemas] = useState<TemaEstudio[]>([])
  const [cargando, setCargando] = useState(true)
  const [desactivado, setDesactivado] = useState(false)

  useEffect(() => {
    const controlador = new AbortController()
    const cargar = async () => {
      try {
        const { data } = await api.get<TemaEstudio[]>(
          `/campo-estudio/mis-cursos/${cursoId}/temas/`,
          { signal: controlador.signal }
        )
        setTemas(data)
      } catch (err: unknown) {
        if (controlador.signal.aborted) return
        const axiosErr = err as { response?: { status?: number } }
        if (axiosErr.response?.status === 403) {
          setDesactivado(true)
        } else {
          toast.error('No se pudieron cargar los temas de estudio')
        }
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

  if (desactivado) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <Lightbulb className="h-10 w-10 text-muted-foreground/50" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          Tu docente aún no ha activado el Campo de Estudio para este curso
        </p>
      </div>
    )
  }

  if (temas.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <Lightbulb className="h-10 w-10 text-muted-foreground/50" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          Aún no hay temas de estudio publicados
        </p>
        <p className="text-xs text-muted-foreground">
          Aparecerán aquí cuando tu docente apruebe alguno
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground max-w-prose">
        Elige un tema para repasarlo y preguntarle a la IA lo que necesites sobre él.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {temas.map((tema) => (
          <Card
            key={tema.id}
            className="cursor-pointer overflow-hidden transition-colors hover:border-primary/40"
            onClick={() => navigate(`/mis-cursos/${cursoId}/campo-estudio/${tema.id}`)}
          >
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm line-clamp-1">
                <MessageCircleQuestion className="h-4 w-4 shrink-0 text-primary" />
                {tema.titulo}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="line-clamp-3 text-xs text-muted-foreground">{tema.contenido}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
