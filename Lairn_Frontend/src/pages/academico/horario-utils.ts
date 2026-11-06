// Cálculos del horario de una evaluación formal (HU-06.3), sin dependencias de React.
//
// El formulario trabaja con fecha (AAAA-MM-DD) y hora (HH:MM, 24 h) locales,
// duración y tolerancia en minutos. El backend sigue recibiendo
// fecha_inicio, fecha_fin y duracion_minutos:
//   fecha_fin = inicio + duración + tolerancia
// Quien inicia dentro de la tolerancia tiene su tiempo completo, porque el
// intento vence en min(inicio del intento + duración, fecha_fin).

export const DURACIONES_PRESET = [60, 90, 120]
export const TOLERANCIAS_PRESET = [0, 10, 15, 30]
export const DURACION_PREDETERMINADA = 90
export const TOLERANCIA_PREDETERMINADA = 15
export const DURACION_MINIMA = 5
export const DURACION_MAXIMA = 600

const dos = (n: number) => String(n).padStart(2, '0')

export function fechaLocal(d: Date): string {
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`
}

export function sumarDias(base: Date, dias: number): Date {
  const d = new Date(base)
  d.setDate(d.getDate() + dias)
  return d
}

// Fecha + hora locales → Date (null si falta algo).
export function componerInicio(fecha: string, hora: string): Date | null {
  if (!fecha || !hora) return null
  const d = new Date(`${fecha}T${hora}`)
  return Number.isNaN(d.getTime()) ? null : d
}

// ISO del backend → fecha y hora locales del formulario.
export function separarInicio(iso: string): { fecha: string; hora: string } {
  const d = new Date(iso)
  return { fecha: fechaLocal(d), hora: `${dos(d.getHours())}:${dos(d.getMinutes())}` }
}

// Sugerencias de hora de inicio cada 30 min.
// Hoy: solo futuras, desde la siguiente hora exacta (6:28 → 7:00, 7:30, …).
// Otro día: horario común de 7:00 a 20:00.
export function sugerenciasHora(fecha: string, ahora: Date): string[] {
  const esHoy = fecha === fechaLocal(ahora)
  const desde = esHoy ? (ahora.getHours() + 1) * 60 : 7 * 60
  const hasta = esHoy ? 23 * 60 + 30 : 20 * 60
  const lista: string[] = []
  for (let m = desde; m <= hasta; m += 30) lista.push(`${dos(Math.floor(m / 60))}:${dos(m % 60)}`)
  return lista
}

// "19:00" → "7:00 p. m."
export function hora12(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number)
  const sufijo = h < 12 ? 'a. m.' : 'p. m.'
  return `${h % 12 === 0 ? 12 : h % 12}:${dos(m)} ${sufijo}`
}

// 90 → "1 h 30"; 60 → "1 h"; 45 → "45 min".
export function textoDuracion(minutos: number): string {
  const h = Math.floor(minutos / 60)
  const m = minutos % 60
  if (!h) return `${m} min`
  return m ? `${h} h ${dos(m)}` : `${h} h`
}

// "Martes 4 nov"
export function textoDia(d: Date): string {
  const dia = new Intl.DateTimeFormat('es-CO', { weekday: 'long' }).format(d)
  const mes = new Intl.DateTimeFormat('es-CO', { month: 'short' }).format(d).replace('.', '')
  return `${dia.charAt(0).toUpperCase()}${dia.slice(1)} ${d.getDate()} ${mes}`
}

function horaDe(d: Date): string {
  return hora12(`${dos(d.getHours())}:${dos(d.getMinutes())}`)
}

export interface ResumenHorario {
  inicio: Date
  fin: Date
  texto: string
}

export function resumenHorario(fecha: string, hora: string, duracion: number, tolerancia: number): ResumenHorario | null {
  const inicio = componerInicio(fecha, hora)
  if (!inicio || !duracion) return null
  const limite = new Date(inicio.getTime() + tolerancia * 60000)
  const fin = new Date(limite.getTime() + duracion * 60000)
  // Si el cierre cae otro día, se nombra el día para que no haya ambigüedad.
  const finTexto = fechaLocal(fin) === fecha ? horaDe(fin) : `${textoDia(fin)}, ${horaDe(fin)}`
  const partes = [
    textoDia(inicio),
    `inicia ${horaDe(inicio)}`,
    `dura ${textoDuracion(duracion)}`,
    tolerancia ? `se puede iniciar hasta ${horaDe(limite)}` : 'sin tolerancia para llegar tarde',
    `termina a más tardar ${finTexto}`,
  ]
  return { inicio, fin, texto: partes.join(' · ') }
}

// Al editar: tolerancia guardada = (cierre - inicio) - duración, en minutos.
export function deducirTolerancia(inicioIso: string, finIso: string, duracion: number): number {
  const ventana = Math.round((new Date(finIso).getTime() - new Date(inicioIso).getTime()) / 60000)
  return Math.max(0, ventana - duracion)
}
