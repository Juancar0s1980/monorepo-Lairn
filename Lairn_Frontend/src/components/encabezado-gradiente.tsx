// Componente de encabezado reutilizable con gradiente, patrón de puntos,
// link de volver y badge opcional.
//
// Uso:
//   <EncabezadoGradiente
//     titulo="Álgebra Lineal"
//     subtitulo="Exámenes disponibles para rendir"
//     volverA="/mis-cursos"
//     volverTexto="Volver a mis cursos"
//     badgeTexto="3/5 exámenes rendidos"
//   />

import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

// Props del componente.
export interface EncabezadoGradienteProps {
  titulo: string
  subtitulo?: string
  volverA?: string
  volverTexto?: string
  badgeTexto?: string
  // Slot opcional para acciones contextuales (ej: menú de 3 puntos).
  acciones?: React.ReactNode
  children?: React.ReactNode
}

export function EncabezadoGradiente({
  titulo,
  subtitulo,
  volverA,
  volverTexto = 'Volver',
  badgeTexto,
  acciones,
  children,
}: EncabezadoGradienteProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-[#2d1b69] to-[#1a1145] p-6">
      {/* Patrón de puntos decorativo */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)',
          backgroundSize: '20px 20px',
        }}
      />

      {/* Link de volver */}
      {volverA && (
        <Link
          to={volverA}
          className="relative inline-flex items-center gap-1.5 text-sm text-white/70 hover:text-white transition-colors mb-3"
        >
          <ArrowLeft className="h-4 w-4" />
          {volverTexto}
        </Link>
      )}

      {/* Acciones opcionales (esquina superior derecha) */}
      {acciones && (
        <div className="absolute right-4 top-4 z-10">{acciones}</div>
      )}

      {/* Título y subtítulo */}
      <div className="relative space-y-1">
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {titulo}
        </h2>
        {subtitulo && (
          <p className="text-white/60 text-sm">{subtitulo}</p>
        )}
      </div>

      {/* Badge opcional */}
      {badgeTexto && (
        <Badge
          variant="secondary"
          className="relative mt-4 text-xs font-mono bg-white/10 text-white/80 border-white/20 backdrop-blur-sm"
        >
          {badgeTexto}
        </Badge>
      )}

      {/* Contenido adicional */}
      {children && (
        <div className="relative mt-4">{children}</div>
      )}
    </div>
  )
}
