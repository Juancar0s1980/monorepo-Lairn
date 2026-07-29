// Chat de un tema de estudio puntual, para el rol Estudiante.
//
// Muestra el contenido del tema (aprobado por el docente) y un hilo de chat
// PRIVADO del estudiante para seguir preguntando sobre ese tema específico.
// La IA está acotada al tema + curso (ver `agente_estudio.responder_pregunta_tema`
// en el backend): preguntas fuera de ese alcance se rechazan amablemente, esto
// no es un asistente de IA de propósito general.
//
// Endpoints: GET /campo-estudio/mis-cursos/{cursoId}/temas/ (para obtener el
//            tema — no hay un GET de detalle propio, se reutiliza la colección),
//            GET/POST /campo-estudio/temas/{temaId}/mensajes/.

import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { EncabezadoGradiente } from '@/components/encabezado-gradiente'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2, Send, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import type { MensajeTemaEstudio, TemaEstudio } from '@/types/campo-estudio'

export default function PaginaTemaEstudioEstudiante() {
  const { cursoId, temaId } = useParams<{ cursoId: string; temaId: string }>()
  const navigate = useNavigate()

  const [tema, setTema] = useState<TemaEstudio | null>(null)
  const [mensajes, setMensajes] = useState<MensajeTemaEstudio[]>([])
  const [cargando, setCargando] = useState(true)
  const [pregunta, setPregunta] = useState('')
  const [enviando, setEnviando] = useState(false)

  const finRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!cursoId || !temaId) return
    const controlador = new AbortController()

    const cargar = async () => {
      try {
        const [temasRes, mensajesRes] = await Promise.all([
          api.get<TemaEstudio[]>(`/campo-estudio/mis-cursos/${cursoId}/temas/`, { signal: controlador.signal }),
          api.get<MensajeTemaEstudio[]>(`/campo-estudio/temas/${temaId}/mensajes/`, { signal: controlador.signal }),
        ])
        const encontrado = temasRes.data.find((t) => t.id === Number(temaId)) ?? null
        setTema(encontrado)
        setMensajes(mensajesRes.data)
      } catch {
        if (!controlador.signal.aborted) toast.error('No se pudo cargar el tema de estudio')
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }
    cargar()
    return () => controlador.abort()
  }, [cursoId, temaId])

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  const enviarPregunta = async () => {
    const texto = pregunta.trim()
    if (!texto || !temaId) return

    setEnviando(true)
    try {
      const { data } = await api.post<MensajeTemaEstudio[]>(
        `/campo-estudio/temas/${temaId}/mensajes/`,
        { pregunta: texto }
      )
      setMensajes((prev) => [...prev, ...data])
      setPregunta('')
    } catch {
      toast.error('La IA no pudo responder, intenta de nuevo')
    } finally {
      setEnviando(false)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!tema || !cursoId) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3 text-center">
        <p className="text-sm font-medium text-muted-foreground">Tema de estudio no encontrado</p>
        <Button variant="outline" onClick={() => navigate(`/mis-cursos/${cursoId ?? ''}/examenes`)}>
          Volver al curso
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <EncabezadoGradiente
        titulo={tema.titulo}
        subtitulo="Campo de Estudio"
        volverA={`/mis-cursos/${cursoId}/examenes`}
        volverTexto="Volver al curso"
      />

      {/* Contenido del tema aprobado por el docente */}
      <Card>
        <CardContent className="whitespace-pre-line text-sm leading-relaxed">
          {tema.contenido}
        </CardContent>
      </Card>

      {/* Hilo de chat privado del estudiante sobre este tema */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-muted-foreground">
          Sigue preguntando sobre este tema
        </p>

        <div className="max-h-[50vh] space-y-3 overflow-y-auto rounded-xl border p-4">
          {mensajes.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <Sparkles className="h-8 w-8 text-muted-foreground/40" />
              <p className="text-xs text-muted-foreground">
                Escribe tu primera pregunta sobre "{tema.titulo}"
              </p>
            </div>
          )}
          {mensajes.map((m) => (
            <div key={m.id} className={`flex ${m.rol === 'estudiante' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-line ${
                  m.rol === 'estudiante'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                {m.contenido}
              </div>
            </div>
          ))}
          {enviando && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Pensando...
              </div>
            </div>
          )}
          <div ref={finRef} />
        </div>

        <div className="flex gap-2">
          <Textarea
            placeholder={`Escribe tu pregunta sobre "${tema.titulo}"...`}
            rows={2}
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                enviarPregunta()
              }
            }}
            disabled={enviando}
          />
          <Button onClick={enviarPregunta} disabled={enviando || !pregunta.trim()} className="shrink-0">
            {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Enviar
          </Button>
        </div>
      </div>
    </div>
  )
}
