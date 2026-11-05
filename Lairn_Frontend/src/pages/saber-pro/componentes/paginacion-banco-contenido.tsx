// Componente de paginación para el banco de contenido Saber Pro (HU-20).
//
// Navegación modular y responsive: muestra rango de elementos, páginas
// disponibles y controles anterior/siguiente con diseño institucional.

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { paletaSaberPro } from '../utilidades'

interface PaginacionBancoContenidoProps {
  pagina: number
  totalPaginas: number
  totalElementos: number
  elementosPorPagina: number
  onPaginaChange: (pagina: number) => void
}

export function PaginacionBancoContenido({
  pagina,
  totalPaginas,
  totalElementos,
  elementosPorPagina,
  onPaginaChange,
}: PaginacionBancoContenidoProps) {
  if (totalPaginas <= 1) return null

  const inicio = (pagina - 1) * elementosPorPagina + 1
  const fin = Math.min(pagina * elementosPorPagina, totalElementos)

  const obtenerPaginas = () => {
    const paginas: number[] = []
    const maxVisibles = 5
    let inicioPagina = Math.max(1, pagina - Math.floor(maxVisibles / 2))
    const finPagina = Math.min(totalPaginas, inicioPagina + maxVisibles - 1)

    if (finPagina - inicioPagina + 1 < maxVisibles) {
      inicioPagina = Math.max(1, finPagina - maxVisibles + 1)
    }

    for (let i = inicioPagina; i <= finPagina; i += 1) {
      paginas.push(i)
    }
    return paginas
  }

  const paginas = obtenerPaginas()

  return (
    <nav
      className={`mt-6 flex flex-col items-center justify-between gap-4 rounded-2xl border p-4 sm:flex-row ${paletaSaberPro.superficie} ${paletaSaberPro.borde}`}
      aria-label="Paginación del banco de contenido"
    >
      <p className={`text-xs ${paletaSaberPro.apoyo}`}>
        Mostrando <span className={`font-semibold ${paletaSaberPro.titulo}`}>{inicio}</span> -{' '}
        <span className={`font-semibold ${paletaSaberPro.titulo}`}>{fin}</span> de{' '}
        <span className={`font-semibold ${paletaSaberPro.titulo}`}>{totalElementos}</span> resultados
      </p>

      <div className="flex items-center gap-1.5">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className={`h-9 gap-1 px-2.5 text-xs ${paletaSaberPro.botonNeutro}`}
          onClick={() => onPaginaChange(pagina - 1)}
          disabled={pagina <= 1}
          aria-label="Página anterior"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Anterior</span>
        </Button>

        <div className="flex items-center gap-1">
          {paginas[0] > 1 && (
            <>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className={`h-9 w-9 px-0 text-xs ${pagina === 1 ? paletaSaberPro.botonAccion : paletaSaberPro.botonNeutro}`}
                onClick={() => onPaginaChange(1)}
              >
                1
              </Button>
              {paginas[0] > 2 && <span className={`px-1 text-xs ${paletaSaberPro.apoyo}`}>...</span>}
            </>
          )}

          {paginas.map((numPagina) => (
            <Button
              key={numPagina}
              type="button"
              size="sm"
              variant="ghost"
              className={`h-9 w-9 px-0 text-xs ${
                pagina === numPagina ? paletaSaberPro.botonAccion : paletaSaberPro.botonNeutro
              }`}
              onClick={() => onPaginaChange(numPagina)}
              aria-current={pagina === numPagina ? 'page' : undefined}
            >
              {numPagina}
            </Button>
          ))}

          {paginas[paginas.length - 1] < totalPaginas && (
            <>
              {paginas[paginas.length - 1] < totalPaginas - 1 && <span className={`px-1 text-xs ${paletaSaberPro.apoyo}`}>...</span>}
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className={`h-9 w-9 px-0 text-xs ${pagina === totalPaginas ? paletaSaberPro.botonAccion : paletaSaberPro.botonNeutro}`}
                onClick={() => onPaginaChange(totalPaginas)}
              >
                {totalPaginas}
              </Button>
            </>
          )}
        </div>

        <Button
          type="button"
          size="sm"
          variant="ghost"
          className={`h-9 gap-1 px-2.5 text-xs ${paletaSaberPro.botonNeutro}`}
          onClick={() => onPaginaChange(pagina + 1)}
          disabled={pagina >= totalPaginas}
          aria-label="Página siguiente"
        >
          <span className="hidden sm:inline">Siguiente</span>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </nav>
  )
}
