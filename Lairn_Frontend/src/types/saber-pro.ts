// Tipos del módulo Saber Pro tal como los devuelve `GET /saber-pro/panel/` (HU-16).
//
// HU-16.2: el panel es accesible para Docente y Estudiante sin depender de un
// curso académico. HU-16.3: cuando el usuario aún no tiene cursos Saber Pro
// (`tiene_cursos: false`), el front muestra el estado vacío con la `accion_vacia`
// correspondiente al rol (crear curso para docente, unirse con código para el
// estudiante). Los campos del backend son `snake_case`.

export interface FuncionalidadSaberPro {
  clave: string
  titulo: string
  descripcion: string
  disponible: boolean
}

export type TipoAccionVaciaSaberPro = 'crear_curso' | 'unirse_codigo'

export interface AccionVaciaSaberPro {
  tipo: TipoAccionVaciaSaberPro
  titulo: string
  descripcion: string
  etiqueta_accion: string
}

export interface PanelSaberPro {
  rol: string
  tiene_cursos: boolean
  accion_vacia: AccionVaciaSaberPro | null
  funcionalidades: FuncionalidadSaberPro[]
}

// ---------------------------------------------------------------------------
// Contratos de la HU-17 (creación y gestión de cursos Saber Pro del docente).
// Reflejan las respuestas de /saber-pro/areas/, /saber-pro/docente/cursos/ y
// /saber-pro/docente/cursos/{id}/estudiantes/. Campos del backend en snake_case.
// ---------------------------------------------------------------------------

export interface AreaSaberPro {
  id: number
  nombre: string
}

export interface CursoSaberPro {
  id: number
  nombre: string
  descripcion: string
  area: AreaSaberPro
  codigo: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export interface EstudianteInscrito {
  id: number
  estudiante: {
    id: number
    nombre_completo: string
    email: string
  }
  fecha: string
}

export interface CodigoRegenerado {
  id: number
  codigo: string
  codigo_anterior: string
}