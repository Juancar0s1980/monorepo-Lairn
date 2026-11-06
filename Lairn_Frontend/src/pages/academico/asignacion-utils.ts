// Utilidades de la asignación masiva de docentes (ADR-017).
import type { EstadoAsignacion, FilaAsignacion } from '@/types/asignacion'

export const ESTADOS_ASIGNACION: { clave: EstadoAsignacion; etiqueta: string; variante: 'success' | 'warning' | 'secondary' | 'outline' | 'destructive' }[] = [
  { clave: 'valida', etiqueta: 'Válida', variante: 'success' },
  { clave: 'advertencia', etiqueta: 'Con advertencia', variante: 'warning' },
  { clave: 'ya_asignada', etiqueta: 'Ya asignada', variante: 'secondary' },
  { clave: 'omitida', etiqueta: 'Sin docente', variante: 'outline' },
  { clave: 'error', etiqueta: 'Con error', variante: 'destructive' },
]

export function etiquetaEstado(estado: EstadoAsignacion) {
  return ESTADOS_ASIGNACION.find((e) => e.clave === estado) ?? ESTADOS_ASIGNACION[4]
}

function celda(valor: unknown): string {
  const texto = valor === null || valor === undefined ? '' : String(valor)
  return /[",;\n]/.test(texto) ? `"${texto.replaceAll('"', '""')}"` : texto
}

// Resumen descargable (CSV con BOM para que Excel lea las tildes).
export function descargarResumen(filas: FilaAsignacion[], nombre: string, aplicado: boolean) {
  const encabezado = ['fila', 'asignatura_codigo', 'asignatura', 'docente_email', 'docente', 'curso_codigo', 'curso',
    'docente_anterior', 'estado', aplicado ? 'aplicada' : 'se_aplicara', 'detalle']
  const lineas = filas.map((f) => [
    f.fila, f.asignatura_codigo, f.asignatura?.nombre ?? '', f.docente_email, f.docente?.nombre ?? '',
    f.curso?.codigo ?? (f.crear_curso ? '(nuevo)' : ''), f.curso?.nombre ?? '', f.anterior?.docente_email ?? '',
    etiquetaEstado(f.estado).etiqueta,
    aplicado ? (f.aplicada ? 'sí' : 'no') : (f.estado === 'valida' || f.estado === 'advertencia' ? 'sí' : 'no'),
    f.mensaje,
  ].map(celda).join(','))
  const blob = new Blob(['\ufeff' + [encabezado.join(','), ...lineas].join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}
