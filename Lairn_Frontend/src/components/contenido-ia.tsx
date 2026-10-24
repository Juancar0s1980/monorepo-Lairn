// Muestra texto generado por un agente de IA con Markdown ligero + LaTeX ya
// renderizados (ver `lib/formato-ia.ts`). Úsalo SOLO con contenido de la
// IA/docente — nunca con lo que escribe el propio estudiante.

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { renderizarContenidoIA } from "@/lib/formato-ia";

interface ContenidoIAProps {
  texto: string;
  className?: string;
}

export function ContenidoIA({ texto, className }: ContenidoIAProps) {
  const html = useMemo(() => renderizarContenidoIA(texto), [texto]);
  return (
    <div
      className={cn("ia-contenido text-sm leading-relaxed", className)}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
