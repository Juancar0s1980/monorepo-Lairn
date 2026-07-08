// Card de curso para la vista del docente.
//
// Muestra header con gradiente, avatar con inicial, código del curso
// con icono para copiar al portapapeles, y stats del curso:
// inscritos, total exámenes, nota promedio y tasa de aprobados.
//
// Uso:
//   <CardCursoDocente
//     id={1}
//     nombre="Programación I"
//     descripcion="Curso de intro"
//     codigo="ABC123"
//     totalInscritos={25}
//     totalExamenes={5}
//     notaPromedio={3.8}
//     tasaAprobados={72}
//   />

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ArrowRight,
  CheckCircle,
  ClipboardCheck,
  Copy,
  TrendingUp,
  Users,
} from 'lucide-react'

// Props del componente.
export interface CardCursoDocenteProps {
  id: number
  nombre: string
  descripcion: string
  codigo: string
  totalInscritos: number
  totalExamenes: number
  notaPromedio?: number
  tasaAprobados?: number
  /** Ruta base para el link. Por defecto '/mis-cursos/{id}/examenes' */
  rutaBase?: string
}

// Paleta de gradientes pasteles para los headers (azul y amarillo, tono universidad).
const gradientes = [
  'from-secondary to-muted',
  'from-accent/25 to-secondary',
  'from-primary/15 to-secondary',
  'from-muted to-secondary',
]

// Genera un gradiente consistente basado en el nombre del curso.
function obtenerGradiente(nombre: string): string {
  let hash = 0
  for (let i = 0; i < nombre.length; i++) {
    hash = nombre.charCodeAt(i) + ((hash << 5) - hash)
  }
  return gradientes[Math.abs(hash) % gradientes.length]
}

// Devuelve la inicial del nombre del curso.
function obtenerInicial(nombre: string): string {
  return nombre.charAt(0).toUpperCase()
}

// Devuelve el color de la nota según su valor.
function colorNota(nota: number): string {
  if (nota >= 4.0) return 'text-emerald-600 dark:text-emerald-400'
  if (nota >= 3.0) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

// Devuelve el color de la barra de progreso.
function colorBarra(porcentaje: number): string {
  if (porcentaje >= 80) return 'bg-emerald-500'
  if (porcentaje >= 60) return 'bg-amber-500'
  return 'bg-red-500'
}

export function CardCursoDocente({
  id,
  nombre,
  descripcion,
  codigo,
  totalInscritos,
  totalExamenes,
  notaPromedio,
  tasaAprobados,
  rutaBase,
}: CardCursoDocenteProps) {
  const [copiado, setCopiado] = useState(false)
  const destino = rutaBase ? `${rutaBase}/${id}` : `/mis-cursos/${id}/examenes`

  // Copia el código al portapapeles y muestra feedback visual.
  const copiarCodigo = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(codigo)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      // Fallback silencioso si el clipboard no está disponible.
    }
  }

  return (
    <Link to={destino}>
      <Card className="h-full overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:border-primary/30 hover:-translate-y-0.5 cursor-pointer group p-0">
        {/* Header con gradiente y avatar */}
        <div
          className={`relative h-28 bg-gradient-to-br ${obtenerGradiente(nombre)} p-5 flex items-end`}
        >
          {/* Avatar con inicial */}
          <div className="absolute top-4 left-5 flex h-11 w-11 items-center justify-center rounded-full bg-card border border-border font-heading text-lg text-primary shadow-sm">
            {obtenerInicial(nombre)}
          </div>

          {/* Badge con código + botón copiar */}
          <div className="absolute top-4 right-5 flex items-center gap-1.5">
            <Badge
              variant="secondary"
              className="text-[11px] font-mono bg-card text-primary border-border shadow-sm"
            >
              {codigo}
            </Badge>
            <button
              onClick={copiarCodigo}
              className="flex h-6 w-6 items-center justify-center rounded-full bg-card border border-border text-muted-foreground hover:text-primary shadow-sm transition-colors"
              title={copiado ? '¡Copiado!' : 'Copiar código'}
            >
              {copiado ? (
                <CheckCircle className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          </div>

          {/* Flecha indicadora */}
          <ArrowRight className="absolute bottom-4 right-5 h-5 w-5 text-primary/40 group-hover:text-primary group-hover:translate-x-0.5 transition-all duration-300" />
        </div>

        {/* Contenido */}
        <CardContent className="p-5 space-y-4">
          {/* Nombre y descripción */}
          <div className="space-y-1">
            <h3 className="font-heading text-lg line-clamp-1 group-hover:text-primary transition-colors">
              {nombre}
            </h3>
            <p className="font-accent text-base text-primary/80 line-clamp-2 leading-relaxed">
              {descripcion || 'Sin descripción'}
            </p>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5" />
              <span>
                {totalInscritos}{' '}
                {totalInscritos === 1 ? 'inscrito' : 'inscritos'}
              </span>
            </div>
            <div className="h-3 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span>
                {totalExamenes}{' '}
                {totalExamenes === 1 ? 'examen' : 'exámenes'}
              </span>
            </div>
          </div>

          {/* Segunda fila de stats: promedio y aprobados */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {notaPromedio !== undefined && (
              <div className="flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>
                  Promedio:{' '}
                  <span className={`font-semibold ${colorNota(notaPromedio)}`}>
                    {notaPromedio.toFixed(1)}
                  </span>
                </span>
              </div>
            )}
            {tasaAprobados !== undefined && (
              <>
                {notaPromedio !== undefined && (
                  <div className="h-3 w-px bg-border" />
                )}
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>
                    Aprobados:{' '}
                    <span className="font-semibold">{tasaAprobados}%</span>
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Barra de tasa de aprobados */}
          {tasaAprobados !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Tasa de aprobados</span>
                <span className="font-medium">{tasaAprobados}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${colorBarra(tasaAprobados)}`}
                  style={{ width: `${tasaAprobados}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}
