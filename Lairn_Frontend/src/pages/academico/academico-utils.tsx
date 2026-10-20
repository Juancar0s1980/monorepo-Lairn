// Utilidades compartidas del módulo Académico (/academico, solo Administrador).
//
// Centraliza lo que antes estaba duplicado dentro de pagina-academico.tsx:
// etiquetas de origen, badge de revisión, extractor de errores del backend,
// formularios vacíos y el tipo de confirmación de borrado lógico.
// Así los tabs y modales importan de aquí y la página queda delgada.
/* eslint-disable react-refresh/only-export-components */

import { Badge } from '@/components/ui/badge'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import type { AsignaturaMalla } from '@/types/academico'

// Etiqueta humana de la vía de origen del registro.
export function etiquetaOrigen(origen: string): string {
  const mapa: Record<string, string> = {
    manual: 'Manual',
    documento_ia: 'Documento + IA',
    api_nova: 'API NOVA',
    semilla: 'Semilla',
  }
  return mapa[origen] ?? origen
}

// Muestra "Aprobado"/"Pendiente" con color según estado de revisión.
export function BadgeRevision({ estado }: { estado: string }) {
  if (estado === 'aprobado')
    return (
      <Badge variant="secondary" className="bg-success/10 text-success border-transparent">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        Aprobado
      </Badge>
    )
  if (estado === 'borrador_ia' || estado === 'pendiente')
    return (
      <Badge variant="secondary" className="bg-warning/10 text-warning border-transparent">
        <AlertTriangle className="h-3 w-3 mr-1" />
        Pendiente
      </Badge>
    )
  return (
    <Badge variant="secondary" className="bg-muted text-muted-foreground border-transparent">
      {estado}
    </Badge>
  )
}

// Extrae el mensaje de error de validación del backend (objeto campo -> lista).
export function mensajeError(err: unknown, generico: string): string {
  const axiosErr = err as { response?: { data?: unknown } }
  const data = axiosErr.response?.data
  if (data && typeof data === 'object') {
    // El backend a veces devuelve {"detalle": "..."} en errores no DRF.
    const obj = data as Record<string, unknown>
    if (typeof obj.detalle === 'string' && obj.detalle.trim()) return obj.detalle
    if (Array.isArray(data)) return (data as unknown[]).map(String).join('. ')
    const valores = Object.values(obj).flat().map(String).join('. ')
    if (valores) return valores
  }
  if (typeof data === 'string' && data.trim()) return data
  return generico
}

// Formulario vacío de programa (se reutiliza para crear y editar).
export const FORM_PROGRAMA_VACIO = {
  codigo: '',
  nombre: '',
  modalidad: 'Presencial',
  sede: 'Principal',
  duracion_semestres: 8,
  fecha_vigencia: '',
}

// Formulario vacío de asignatura.
export const FORM_ASIGNATURA_VACIO = {
  codigo: '',
  nombre: '',
  creditos: 3,
  intensidad_horaria: 0,
  tipo: 'obligatoria' as AsignaturaMalla['tipo'],
  semestre: '' as string,
}

// Formulario vacío de resultado de aprendizaje.
export const FORM_RESULTADO_VACIO = {
  competencia: '',
  asignatura: '',
  descripcion: '',
  evidencia_observable: '',
  tarea_sugerida: '',
}

// Formulario vacío de momento.
export const FORM_MOMENTO_VACIO = {
  semestre_referencia: 4,
  nombre: '',
  periodo: '',
  descripcion: '',
}

// Confirmación genérica de borrado para todas las entidades.
// Ojo: 'cargue' es borrado físico (el PDF nunca se guardó); el resto es
// borrado lógico que conserva histórico (HU-01.8).
export interface ConfirmacionBorrado {
  tipo:
    | 'programa'
    | 'semestre'
    | 'asignatura'
    | 'competencia'
    | 'resultado'
    | 'momento'
    | 'vinculo'
    | 'cargue'
  id: number
  nombre: string
}
