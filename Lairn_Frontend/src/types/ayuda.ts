// Centro de ayuda (ADR-018).

export interface PasoAyuda {
  titulo: string
  detalle: string
}

export interface ArticuloAyuda {
  slug: string
  titulo: string
  categoria: string
  categoria_nombre: string
  resumen: string
  ruta: string
  roles: string[]
  tiene_video: boolean
  publicado: boolean
  orden: number
  actualizado_en: string
  // Solo en el detalle.
  pasos?: PasoAyuda[]
  notas?: string
  video_nombre?: string
}

export interface ListaAyuda {
  categorias: { clave: string; nombre: string; total: number }[]
  articulos: ArticuloAyuda[]
  puede_editar: boolean
}
