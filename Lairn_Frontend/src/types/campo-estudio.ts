// Tipos del Campo de Estudio: temas generados por IA (con aprobación del
// docente) y el hilo de chat privado de cada estudiante sobre un tema.

export type EstadoTemaEstudio = 'pendiente' | 'aprobado'

// Tema de estudio tal como lo devuelve el backend.
export interface TemaEstudio {
  id: number
  titulo: string
  contenido: string
  estado: EstadoTemaEstudio
  creado_en: string
  aprobado_en: string | null
}

export type RolMensajeTemaEstudio = 'estudiante' | 'ia'

// Mensaje del hilo de chat de un estudiante sobre un tema.
export interface MensajeTemaEstudio {
  id: number
  rol: RolMensajeTemaEstudio
  contenido: string
  creado_en: string
}
