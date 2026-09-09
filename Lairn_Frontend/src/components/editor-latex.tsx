// Editor de respuesta con soporte de notación matemática (LaTeX).
//
// Pensado para preguntas tipo='respuesta_libre' en cursos donde el
// procedimiento importa (Cálculo, Física, Mecánica de Suelos, etc.): el
// Textarea plano que se usaba antes obligaba a escribir ecuaciones como
// texto ambiguo ("integral de 3x^2 dx" en una sola línea). Acá el estudiante
// mezcla texto normal con LaTeX entre $...$ (en línea) o $$...$$ (bloque, se
// centra en su propia línea) y ve al lado cómo se renderiza, en vivo.
//
// La calificación no cambia: sigue siendo texto plano contra la rúbrica en
// `agente_evaluador.py` (la IA entiende LaTeX igual o mejor que texto ASCII
// ambiguo) — este componente es solo la experiencia de escritura/lectura.
//
// Seguridad: katex.renderToString con `trust: false` (default) deshabilita
// comandos que podrían inyectar HTML/URLs arbitrarios (\href, \includegraphics,
// etc.), así que renderizar contenido ajeno (ej. el docente revisando la
// respuesta de un estudiante) con este mismo componente es seguro.

import { useRef, useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { cn } from "@/lib/utils";
import {
  Sigma,
  Divide,
  SquareRadical,
  Superscript,
  Subscript,
  ChevronsUp,
} from "lucide-react";

interface BotonSnippet {
  icono: typeof Sigma;
  titulo: string;
  /** Se inserta en el cursor. "@" marca dónde queda el cursor después de insertar. */
  snippet: string;
}

// Snippets más usados en un procedimiento de cálculo/física — cubren la
// mayoría de lo que un estudiante necesita sin memorizar comandos LaTeX.
const BOTONES: BotonSnippet[] = [
  { icono: Divide, titulo: "Fracción", snippet: "$\\frac{@}{}$" },
  { icono: Superscript, titulo: "Exponente", snippet: "$x^{@}$" },
  { icono: Subscript, titulo: "Subíndice", snippet: "$x_{@}$" },
  { icono: SquareRadical, titulo: "Raíz", snippet: "$\\sqrt{@}$" },
  { icono: Sigma, titulo: "Sumatoria", snippet: "$\\sum_{i=@}^{n}$" },
  { icono: ChevronsUp, titulo: "Integral", snippet: "$\\int_{@}^{} \\, dx$" },
];

// Separa texto normal de segmentos LaTeX delimitados por $$...$$ (bloque) o
// $...$ (en línea). Los bloques van primero en la alternancia para que el
// regex no confunda "$$" con dos "$" sueltos.
const PATRON_LATEX = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;

function renderizarMixto(texto: string): { html: string } {
  if (!texto) return { html: "" };

  const partes = texto.split(PATRON_LATEX);
  const html = partes
    .map((parte) => {
      const esBloque = parte.startsWith("$$") && parte.endsWith("$$");
      const esLinea = !esBloque && parte.startsWith("$") && parte.endsWith("$") && parte.length > 1;

      if (esBloque || esLinea) {
        const formula = esBloque ? parte.slice(2, -2) : parte.slice(1, -1);
        try {
          return katex.renderToString(formula, {
            throwOnError: false,
            displayMode: esBloque,
            trust: false,
          });
        } catch {
          return `<span class="text-destructive">${formula}</span>`;
        }
      }

      // Texto normal: escapar HTML y preservar saltos de línea.
      const escapado = parte
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      return escapado.replace(/\n/g, "<br/>");
    })
    .join("");

  return { html };
}

interface EditorLatexProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
}

export function EditorLatex({
  value,
  onChange,
  placeholder = "Escribe tu procedimiento. Usa $...$ para una fórmula en línea o $$...$$ para una fórmula en su propia línea, ej: $$\\int_0^2 3x^2\\,dx = 8$$",
  disabled,
  rows = 12,
}: EditorLatexProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { html } = useMemo(() => renderizarMixto(value), [value]);

  // Inserta un snippet en la posición del cursor (o reemplazando la
  // selección) y deja el cursor en el "@" del snippet, listo para escribir.
  const insertarSnippet = (snippet: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const inicio = textarea.selectionStart;
    const fin = textarea.selectionEnd;
    const cursorEnSnippet = snippet.indexOf("@");
    const snippetLimpio = snippet.replace("@", "");

    const nuevoValor = value.slice(0, inicio) + snippetLimpio + value.slice(fin);
    onChange(nuevoValor);

    const nuevaPosicion = inicio + cursorEnSnippet;
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.setSelectionRange(nuevaPosicion, nuevaPosicion);
    });
  };

  return (
    <div className="space-y-2">
      {/* Barra de símbolos comunes */}
      <div className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-muted/40 p-1">
        {BOTONES.map(({ icono: Icono, titulo, snippet }) => (
          <button
            key={titulo}
            type="button"
            title={titulo}
            disabled={disabled}
            onClick={() => insertarSnippet(snippet)}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-background hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
          >
            <Icono className="h-4 w-4" />
          </button>
        ))}
        <span className="ml-auto pr-1 text-[11px] text-muted-foreground">
          $fórmula$ en línea · $$fórmula$$ en bloque
        </span>
      </div>

      {/* Entrada + vista previa, lado a lado en pantallas medianas+ */}
      <div className="grid gap-2 md:grid-cols-2">
        <textarea
          ref={textareaRef}
          rows={rows}
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "w-full resize-y rounded-lg border border-input bg-input/40 px-2.5 py-2 font-mono text-sm transition-colors outline-none placeholder:text-muted-foreground placeholder:font-sans focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30",
          )}
        />
        <div
          className={cn(
            "min-h-[theme(spacing.16)] overflow-auto rounded-lg border border-dashed border-border bg-muted/20 px-3 py-2 text-sm",
            !value && "flex items-center justify-center text-muted-foreground",
          )}
          style={{ minHeight: `${rows * 1.5}rem` }}
        >
          {value ? (
            <div className="katex-preview" dangerouslySetInnerHTML={{ __html: html }} />
          ) : (
            <span className="text-xs">La vista previa aparece aquí mientras escribes</span>
          )}
        </div>
      </div>
    </div>
  );
}
