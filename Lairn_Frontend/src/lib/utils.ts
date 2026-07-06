// Utilidad de Shadcn/UI para combinar clases de Tailwind.
// clsx genera el string de clases condicionalmente,
// twMerge elimina conflictos entre clases de Tailwind (ej. "p-2 p-4" → "p-4").

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
