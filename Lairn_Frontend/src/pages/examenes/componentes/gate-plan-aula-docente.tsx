// Pantalla de bloqueo que se muestra en un curso recién creado hasta que el
// docente sube el PDF del plan de aula.
//
// La IA lee el PDF, extrae los objetivos de aprendizaje del documento y los
// guarda directamente como ObjetivoCurso (sin paso de curación: el docente
// ya aprobó el contenido al elegir ese PDF). El archivo nunca se conserva.
//
// Endpoint: POST /examenes/cursos/{cursoId}/plan-aula/ (multipart/form-data,
// campo "archivo").

import { useRef, useState } from 'react'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { FileText, Loader2, Upload } from 'lucide-react'
import { toast } from 'sonner'

interface GatePlanAulaDocenteProps {
  cursoId: string
  nombreCurso: string
  onCargado: () => void
}

export function GatePlanAulaDocente({ cursoId, nombreCurso, onCargado }: GatePlanAulaDocenteProps) {
  const [archivo, setArchivo] = useState<File | null>(null)
  const [subiendo, setSubiendo] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const elegirArchivo = (e: React.ChangeEvent<HTMLInputElement>) => {
    setArchivo(e.target.files?.[0] ?? null)
  }

  const subirPlanDeAula = async () => {
    if (!archivo) return
    setSubiendo(true)
    try {
      const formData = new FormData()
      formData.append('archivo', archivo)
      // El cliente `api` fija Content-Type: application/json por defecto en todas
      // las peticiones; hay que quitarlo explícitamente para que el navegador le
      // ponga el boundary correcto de multipart/form-data al mandar un FormData.
      const { data } = await api.post<unknown[]>(
        `/examenes/cursos/${cursoId}/plan-aula/`,
        formData,
        { headers: { 'Content-Type': undefined } }
      )
      toast.success(
        `Se generaron ${data.length} objetivo${data.length === 1 ? '' : 's'} de aprendizaje a partir del plan de aula`
      )
      onCargado()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detalle?: string } } }
      toast.error(axiosErr.response?.data?.detalle ?? 'No se pudo procesar el plan de aula')
      setArchivo(null)
      if (inputRef.current) inputRef.current.value = ''
    } finally {
      setSubiendo(false)
    }
  }

  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Card className="w-full max-w-lg">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full border border-primary/20 bg-primary/10">
            <FileText className="h-7 w-7 text-primary" />
          </div>
          <div className="space-y-1.5">
            <h2 className="font-heading text-lg">Sube el plan de aula de "{nombreCurso}"</h2>
            <p className="text-sm text-muted-foreground">
              Antes de continuar, sube el PDF del plan de aula del curso. La IA leerá el
              documento y generará los objetivos de aprendizaje automáticamente. El resto de
              las secciones del curso se habilitan justo después de este paso.
            </p>
          </div>

          <label
            htmlFor="archivo-plan-aula"
            className="flex w-full cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed p-6 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5"
          >
            <Upload className="h-6 w-6" />
            {archivo ? (
              <span className="font-medium text-foreground">{archivo.name}</span>
            ) : (
              <span>Haz clic para elegir el PDF</span>
            )}
            <input
              id="archivo-plan-aula"
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={elegirArchivo}
              disabled={subiendo}
            />
          </label>

          <Button onClick={subirPlanDeAula} disabled={!archivo || subiendo} className="w-full">
            {subiendo ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generando objetivos...
              </>
            ) : (
              'Subir y generar objetivos'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
