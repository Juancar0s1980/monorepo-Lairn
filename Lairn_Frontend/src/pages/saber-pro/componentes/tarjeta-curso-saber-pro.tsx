// Tarjeta de un curso Saber Pro del docente (HU-17).
//
// Muestra el resumen de un curso en la lista: área, nombre, descripción y el
// código de acceso vigente (con botón de copiar). El botón "Gestionar" abre el
// modal de detalle (HU-17.3 a HU-17.6). Diseño institucional con los tokens de
// `paletaSaberPro`, consistente en claro y oscuro.

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GraduationCap, Copy, Check, Settings2, Users } from 'lucide-react'
import { toast } from 'sonner'
import type { CursoSaberPro } from '@/types/saber-pro'
import { paletaSaberPro } from '../utilidades'
import { ModalDetalleCursoSaberPro } from './modal-detalle-curso-saber-pro'

interface TarjetaCursoSaberProProps {
  curso: CursoSaberPro
  onCursoActualizado: () => void
}

export function TarjetaCursoSaberPro({ curso, onCursoActualizado }: TarjetaCursoSaberProProps) {
  const [copiado, setCopiado] = useState(false)
  const [detalleAbierto, setDetalleAbierto] = useState(false)

  // Copia el código vigente al portapapeles (HU-17.3: consultar el código).
  const copiarCodigo = async () => {
    try {
      await navigator.clipboard.writeText(curso.codigo)
      setCopiado(true)
      toast.success('Código copiado al portapapeles')
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      toast.error('No se pudo copiar el código')
    }
  }

  return (
    <article
      className={`flex flex-col gap-4 rounded-2xl border p-5 transition-colors ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
    >
      <div className="flex items-start justify-between gap-3">
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${paletaSaberPro.iconoChip}`}
        >
          <GraduationCap className="h-6 w-6" />
        </span>
        <div className="flex flex-col items-end gap-1.5">
          <Badge
            variant="outline"
            className={`text-[11px] font-semibold ${paletaSaberPro.badge}`}
          >
            {curso.area.nombre}
          </Badge>
          {!curso.activo && (
            <Badge variant="outline" className="h-5 border-red-400/50 text-[10px] text-red-600 dark:text-red-300">
              Inactivo
            </Badge>
          )}
        </div>
      </div>

      <div>
        <h3 className={`text-base font-bold leading-snug ${paletaSaberPro.titulo}`}>
          {curso.nombre}
        </h3>
        <p className={`mt-1 line-clamp-2 text-sm leading-relaxed ${paletaSaberPro.apoyo}`}>
          {curso.descripcion || 'Sin descripción.'}
        </p>
      </div>

      {/* Código de acceso vigente, con copia rápida (HU-17.3) */}
      <div
        className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2.5 ${paletaSaberPro.bandaAlterna} ${paletaSaberPro.borde}`}
      >
        <div className="min-w-0">
          <p className={`text-[10px] font-semibold uppercase tracking-[0.14em] ${paletaSaberPro.apoyoTitulo}`}>
            Código de acceso
          </p>
          <p
            className={`font-mono text-lg font-bold tracking-[0.28em] ${paletaSaberPro.titulo}`}
            aria-label={`Código de acceso ${curso.codigo}`}
          >
            {curso.codigo}
          </p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className={`shrink-0 ${paletaSaberPro.botonNeutro}`}
          onClick={copiarCodigo}
          aria-label="Copiar código de acceso"
        >
          {copiado ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>

      <div className="flex gap-2">
        <Button
          type="button"
          className={`h-10 flex-1 gap-2 ${paletaSaberPro.botonAccion}`}
          onClick={() => setDetalleAbierto(true)}
        >
          <Settings2 className="h-4 w-4" />
          Gestionar
        </Button>
        <Button
          type="button"
          variant="outline"
          className={`h-10 shrink-0 ${paletaSaberPro.botonNeutro}`}
          onClick={() => setDetalleAbierto(true)}
          aria-label="Ver estudiantes inscritos"
        >
          <Users className="h-4 w-4" />
        </Button>
      </div>

      <ModalDetalleCursoSaberPro
        curso={curso}
        abierto={detalleAbierto}
        onCerrar={() => setDetalleAbierto(false)}
        onCursoActualizado={onCursoActualizado}
      />
    </article>
  )
}