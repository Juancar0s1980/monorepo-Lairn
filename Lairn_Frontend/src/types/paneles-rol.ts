// Tipos de los resúmenes de inicio por rol (ADR-014).
// Coinciden con apps.evaluacion_resultados.services.servicio_paneles_rol.

import type { Medida } from '@/types/reporte'
import type { PanelCoordinador } from '@/types/panel-coordinador'

export interface PanelAdmin {
  generado_en: string
  usuarios: { rol: string; activos: number; inactivos: number }[]
  importaciones: {
    id: number
    creado_en: string
    origen: string
    entidad: string
    modo: string
    recibidos: number
    creados: number
    actualizados: number
    omitidos: number
    errores: number
    ejecutado_por: string | null
  }[]
  cargues: {
    por_estado: Record<string, number>
    recientes: { id: number; nombre_archivo: string; tipo: string; estado: string; programa: string | null; creado_en: string }[]
  }
  evaluaciones: PanelCoordinador['evaluaciones']
  abiertas: PanelCoordinador['proximas']
  convocados_por_cargue: number
  alertas_abiertas: number
  integridad: PanelCoordinador['integridad']
}

export interface PanelDocente {
  generado_en: string
  asignaturas: { id: number; codigo: string; nombre: string; curso: string; preguntas: Record<'pendiente' | 'aprobada' | 'descartada', number> }[]
  banco: Record<'pendiente' | 'aprobada' | 'descartada', number>
  tareas: {
    borradores: number
    publicadas: number
    entregas_sin_calificar: number
    proximas: { id: number; titulo: string; asignatura: string; fecha_limite: string; entregas: number; sin_calificar: number }[]
  }
  supervisiones: { id: number; nombre: string; momento: string; fecha_inicio: string; fecha_fin: string; abierta: boolean }[]
  resultados: {
    aviso: string
    umbral_logro_porcentaje: number
    general: Medida | null
    por_ra: (Medida & { id: number; descripcion: string; asignatura: string })[]
    preguntas_error: { pregunta: number; enunciado: string; asignatura: string; presentadas: number; porcentaje_error: number }[]
  }
}

export interface PanelEstudiante {
  generado_en: string
  pendientes: {
    evaluaciones: {
      id: number
      nombre: string
      tipo: 'cuestionario' | 'tarea'
      momento: string
      fecha_inicio: string
      fecha_fin: string
      activa: boolean
      duracion_minutos: number
      requiere_asistencia: boolean
      asistencia: string | null
      intento: 'en_curso' | 'suspendido' | null
      tarea: number | null
    }[]
    tareas: { id: number; titulo: string; asignatura: string; fecha_limite: string; plazo: 'abierta' | 'tardia' }[]
  }
  historial: {
    evaluaciones: { id: number; nombre: string; momento: string; enviado_en: string; envio_automatico: boolean; anulada: boolean }[]
    tareas: { id: number; titulo: string; asignatura: string; enviada_en: string; con_retraso: boolean; nota: string | null; calificada: boolean }[]
  }
  resumen: { evaluaciones_pendientes: number; tareas_pendientes: number; evaluaciones_presentadas: number; tareas_entregadas: number }
}
