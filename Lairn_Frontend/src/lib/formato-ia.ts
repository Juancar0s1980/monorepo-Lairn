// Renderiza texto generado por IA (Markdown ligero + LaTeX) a HTML seguro.
//
// Usado donde se muestra contenido de un agente de IA de formato libre —el
// tutor de Campo de Estudio, el contenido de un tema— que naturalmente
// escribe en Markdown y LaTeX sin que se lo pidamos explícitamente (así
// responden estos modelos por defecto ante contenido matemático/técnico).
// Antes esos textos se mostraban como texto plano: el estudiante veía
// literalmente "### Título" o "\[ x^2 \]" en vez de un título o una fórmula.
//
// Soporta AMBOS estilos de delimitador LaTeX que los modelos usan indistinto:
// $...$/$$...$$ (el que ya entendía editor-latex.tsx) y \(...\)/\[...\] (el
// estilo nativo de LaTeX, que es el que de hecho está devolviendo la IA en
// este chat). Markdown soportado: encabezados, negrita, cursiva, código en
// línea, listas (con/sin numerar) y regla horizontal — el subconjunto que
// estos agentes realmente producen, no CommonMark completo.
//
// Seguridad: SOLO se debe usar con contenido de la IA/docente, nunca con lo
// que escribe el propio estudiante (ver dónde se usa en los componentes) —
// el texto se escapa como HTML antes de insertar las etiquetas de Markdown,
// pero esto no es un sanitizador general de HTML arbitrario.

import katex from "katex";
import "katex/dist/katex.min.css";

// Bloques ($$.../\[...\]) antes que en línea ($.../\(...\)) para que la
// alternancia no confunda "$$" con dos "$" sueltos — mismo criterio que
// PATRON_LATEX en editor-latex.tsx, extendido con los delimitadores \( \).
const PATRON_MATH = /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^$\n]+?\$|\\\([\s\S]+?\\\))/g;

// Separador invisible (U+2063) escrito como código de escape: un NUL literal
// en el archivo de código fuente lo hace ver como binario para herramientas
// como grep, aunque JS/TS lo acepte dentro de un string.
const MARCADOR = "⁣";

// Extrae y renderiza cada fórmula a HTML de KaTeX, dejando un marcador de
// una sola pieza (sin espacios/saltos de línea) en su lugar para que el
// procesamiento de Markdown que sigue no lo parta ni lo escape.
function extraerFormulas(texto: string): { conMarcadores: string; formulas: string[] } {
  const formulas: string[] = [];

  const conMarcadores = texto
    .split(PATRON_MATH)
    .map((parte) => {
      let formula: string | null = null;
      let displayMode = false;

      if (parte.startsWith("$$") && parte.endsWith("$$") && parte.length > 3) {
        formula = parte.slice(2, -2);
        displayMode = true;
      } else if (parte.startsWith("\\[") && parte.endsWith("\\]")) {
        formula = parte.slice(2, -2);
        displayMode = true;
      } else if (parte.startsWith("\\(") && parte.endsWith("\\)")) {
        formula = parte.slice(2, -2);
        displayMode = false;
      } else if (parte.startsWith("$") && parte.endsWith("$") && parte.length > 1) {
        formula = parte.slice(1, -1);
        displayMode = false;
      }

      if (formula === null) return parte;

      let html: string;
      try {
        html = katex.renderToString(formula, { throwOnError: false, displayMode, trust: false });
      } catch {
        html = `<span class="text-destructive">${formula}</span>`;
      }
      const indice = formulas.length;
      formulas.push(html);
      return `${MARCADOR}${indice}${MARCADOR}`;
    })
    .join("");

  return { conMarcadores, formulas };
}

// Transformaciones en línea dentro de un bloque: escapa HTML primero (el
// marcador de fórmula no usa caracteres que el escape toque), y recién
// encima aplica negrita/cursiva/código.
function procesarEnLinea(texto: string): string {
  let out = texto.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  out = out.replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/`([^`]+?)`/g, "<code>$1</code>");
  out = out.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, "$1<em>$2</em>");
  return out;
}

// Un "bloque" es un párrafo/lista/encabezado separado por línea(s) en
// blanco. Markdown real usa reglas más finas; este subconjunto cubre lo que
// estos agentes realmente generan.
function procesarBloque(bloque: string): string {
  const lineas = bloque.split("\n").filter((l) => l.trim() !== "");
  if (lineas.length === 0) return "";

  if (/^(-{3,}|\*{3,}|_{3,})$/.test(bloque.trim())) {
    return '<hr class="ia-hr"/>';
  }

  const encabezado = bloque.trim().match(/^(#{1,6})\s+(.*)$/);
  if (encabezado && lineas.length === 1) {
    const nivel = Math.min(encabezado[1].length, 6);
    return `<h${nivel} class="ia-heading ia-heading-${nivel}">${procesarEnLinea(encabezado[2])}</h${nivel}>`;
  }

  const esListaBullet = lineas.every((l) => /^[-*]\s+/.test(l.trim()));
  const esListaNumerada = !esListaBullet && lineas.every((l) => /^\d+\.\s+/.test(l.trim()));
  if (esListaBullet || esListaNumerada) {
    const tag = esListaBullet ? "ul" : "ol";
    const items = lineas
      .map((l) => `<li>${procesarEnLinea(l.trim().replace(/^([-*]|\d+\.)\s+/, ""))}</li>`)
      .join("");
    return `<${tag} class="ia-lista">${items}</${tag}>`;
  }

  return `<p class="ia-parrafo">${lineas.map(procesarEnLinea).join("<br/>")}</p>`;
}

/** Convierte texto de un agente de IA (Markdown ligero + LaTeX) a HTML listo para `dangerouslySetInnerHTML`. */
export function renderizarContenidoIA(texto: string): string {
  if (!texto?.trim()) return "";

  const { conMarcadores, formulas } = extraerFormulas(texto);
  let html = conMarcadores
    .split(/\n{2,}/)
    .map(procesarBloque)
    .join("");

  formulas.forEach((formulaHtml, indice) => {
    html = html.split(`${MARCADOR}${indice}${MARCADOR}`).join(formulaHtml);
  });

  return html;
}
