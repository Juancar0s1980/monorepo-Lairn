// Etiquetas y colores de los estados del cargue de estudiantes (ADR-009 + ADR-012).

import type { EstadoCargue } from '@/types/supervision'

export const ESTADOS_CARGUE: Record<EstadoCargue, { texto: string; clase: string }> = {
  agregar: { texto: 'Válido · se agregará', clase: 'bg-success/10 text-success' },
  existe: { texto: 'Ya existe en el sistema', clase: 'bg-success/10 text-success' },
  ya_convocado: { texto: 'Ya convocado (no se toca)', clase: 'bg-muted text-muted-foreground' },
  no_encontrado: { texto: 'No existe la cuenta', clase: 'bg-warning/15 text-foreground' },
  no_es_estudiante: { texto: 'No es estudiante', clase: 'bg-warning/15 text-foreground' },
  duplicado_en_archivo: { texto: 'Duplicado en el archivo', clase: 'bg-muted text-muted-foreground' },
  invalido: { texto: 'Formato inválido', clase: 'bg-destructive/10 text-destructive' },
  campo_obligatorio_faltante: { texto: 'Falta el correo', clase: 'bg-destructive/10 text-destructive' },
}
