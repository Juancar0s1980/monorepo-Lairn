// Card de curso para la vista del estudiante.
//
// Muestra header con gradiente, avatar con inicial, nombre del docente
// como badge, y stats del progreso: exámenes rendidos, nota promedio
// y barra de progreso.
//
// Uso:
//   <CardCursoEstudiante
//     id={1}
//     nombre="Programación I"
//     descripcion="Curso de intro"
//     docente="Prof. García"
//     examenesRendidos={3}
//     totalExamenes={5}
//     notaPromedio={4.2}
//   />

import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, ClipboardCheck, TrendingUp } from 'lucide-react'

// Props del componente.
export interface CardCursoEstudianteProps {
  id: number
  nombre: string
  descripcion: string
  docente: string
  examenesRendidos: number
  totalExamenes: number
  notaPromedio?: number
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

export function CardCursoEstudiante({
  id,
  nombre,
  descripcion,
  docente,
  examenesRendidos,
  totalExamenes,
  notaPromedio,
  rutaBase,
}: CardCursoEstudianteProps) {
  const porcentaje =
    totalExamenes > 0
      ? Math.round((examenesRendidos / totalExamenes) * 100)
      : 0
  const tieneDatos = examenesRendidos > 0
  const destino = rutaBase
    ? `${rutaBase}/${id}`
    : `/mis-cursos/${id}/examenes`

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

          {/* Badge con nombre del docente */}
          <Badge
            variant="secondary"
            className="absolute top-4 right-5 text-[10px] font-mono bg-card text-primary border-border shadow-sm"
          >
            {docente}
          </Badge>

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
            <p className="font-accent text-base text-[#325986] dark:text-primary/80 line-clamp-2 leading-relaxed">
              {descripcion || 'Sin descripción'}
            </p>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span>
                {examenesRendidos}/{totalExamenes} exámenes
              </span>
            </div>
            {tieneDatos && notaPromedio !== undefined && (
              <>
                <div className="h-3 w-px bg-border" />
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>
                    Promedio:{' '}
                    <span
                      className={`font-semibold ${colorNota(notaPromedio)}`}
                    >
                      {notaPromedio.toFixed(2)}
                    </span>
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Barra de progreso */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progreso</span>
              <span className="font-medium">{porcentaje}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${colorBarra(porcentaje)}`}
                style={{ width: `${porcentaje}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
