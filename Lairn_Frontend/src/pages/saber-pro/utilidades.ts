// Helpers de identidad visual y de contenido del módulo Saber Pro (HU-16).
//
// Implementación directa de la paleta institucional
// (.opencode/skills/institutional-ui) con dos modos SIMÉTRICOS por rol, para
// que la sección sea visualmente consistente en claro y en oscuro:
//
//   Modo claro  -> fondo beige (#f3ede1), superficies blancas, texto navy
//                  (#1e3a5f) y cuerpo #2c3e50, acentos dorado #c89b14 y
//                  naranja #e8740e, bordes rgba(30,58,95,0.09).
//   Modo oscuro -> la misma jerarquía invertida por rol: fondo navy profundo
//                  (#172A45), texto crema (#f3ede1 / #F5EFE0), superficies en
//                  navy elevado (#243A5E) y acentos gold/naranja aclarados
//                  (#E3C063 / #F29A52) para mantener contraste AA.
//
// Cada token claro tiene así su equivalente oscuro del mismo rol, sin colores
// sueltos y con la misma estructura de capas en ambos temas. Junto a la
// paleta viven dos datos de presentación de HU-16: las áreas de Saber Pro
// (para el hero) y los pasos de inicio según el rol (estado vacío HU-16.3).

export const paletaSaberPro = {
  banda: 'bg-[#f3ede1] dark:bg-[#172A45]',
  bandaAlterna: 'bg-[#ede6d8] dark:bg-[#1E3351]',
  bandaProfunda: 'bg-[#e7dfcc] dark:bg-[#17263F]',
  superficie: 'bg-white dark:bg-[#243A5E]',
  superficieSutil: 'bg-white/80 dark:bg-[#243A5E]/70',
  titulo: 'text-[#1e3a5f] dark:text-[#F5EFE0]',
  texto: 'text-[#2c3e50] dark:text-[#CFC9BA]',
  apoyoTitulo: 'text-[#c89b14] dark:text-[#E3C063]',
  apoyo: 'text-[#6b7a8d] dark:text-[#B9B2A2]',
  accion: 'text-[#e8740e] dark:text-[#F29A52]',
  separador: 'bg-[#c89b14] dark:bg-[#E3C063]',
  iconoChip: 'bg-[#1e3a5f]/10 text-[#1e3a5f] dark:bg-[#F3EDE1]/12 dark:text-[#F5EFE0]',
  chipAccion: 'bg-[#e8740e]/15 text-[#e8740e] dark:bg-[#F29A52]/20 dark:text-[#F29A52]',
  chipGold: 'bg-[#c89b14]/15 text-[#c89b14] dark:bg-[#E3C063]/20 dark:text-[#E3C063]',
  borde: 'border-[rgba(30,58,95,0.09)] dark:border-[rgba(243,237,225,0.15)]',
  badge: 'border-[#c89b14]/40 text-[#c89b14] dark:border-[#E3C063]/50 dark:text-[#E3C063]',
  botonAccion:
    'bg-[#e8740e] text-white hover:bg-[#cf5f07] dark:bg-[#F29A52] dark:text-[#172A45] dark:hover:bg-[#F7AC6B]',
  botonNeutro:
    'border-[rgba(30,58,95,0.18)] bg-transparent text-[#1e3a5f] hover:bg-white dark:border-[rgba(243,237,225,0.28)] dark:text-[#F5EFE0] dark:hover:bg-[#243A5E]',
  franja:
    'bg-gradient-to-r from-[#1e3a5f] via-[#c89b14] to-[#e8740e] dark:from-[#F3EDE1] dark:via-[#E3C063] dark:to-[#F29A52]',
  numeracionPaso:
    'bg-[#1e3a5f] text-[#F3EDE1] dark:bg-[#E3C063] dark:text-[#172A45]',
  sello:
    'bg-[#1e3a5f] text-[#c89b14] ring-[#c89b14]/40 dark:bg-[#F3EDE1] dark:text-[#1e3a5f] dark:ring-[#E3C063]/60',
  esqueleto: 'bg-[#1e3a5f]/10 dark:bg-[#F3EDE1]/12',
  fuenteHero: "font-['Montserrat'] font-black",
} as const

// El Select de Shadcn (base-ui) no se adapta solo a textos largos. Tres capas
// recortan el contenido por defecto:
//   1. el trigger es de una sola línea (`h-8` + `whitespace-nowrap` y el valor
//      con `line-clamp-1`), así que el criterio elegido no se puede leer;
//   2. el popup hereda el ancho del trigger (`w-(--anchor-width)`);
//   3. cada opción usa `whitespace-nowrap` + `shrink-0`.
// Estos tokens permiten leer el texto completo: `selectTriggerLargo` deja que el
// trigger crezca en varias líneas (y con él su tarjeta/modal), `selectContenidoAncho`
// ensancha el popup hasta el borde de la pantalla y `selectItemLargo` hace que las
// opciones hagan salto de línea en vez de cortarse. `selectTriggerAncho` es la
// variante de una sola línea para campos cortos.
export const selectContenidoAncho = 'w-auto! min-w-(--anchor-width) max-w-[calc(100vw-2rem)]'
export const selectItemLargo = '[&>div]:whitespace-normal [&>div]:shrink [&>div]:break-words'
export const selectTriggerAncho = 'w-full min-w-0 bg-white dark:bg-[#243A5E]'
export const selectTriggerLargo =
  'w-full min-w-0 h-auto! min-h-8! items-start! py-2 whitespace-normal bg-white dark:bg-[#243A5E] ' +
  '*:data-[slot=select-value]:line-clamp-none! *:data-[slot=select-value]:whitespace-normal ' +
  '*:data-[slot=select-value]:break-words'

// Áreas de Saber Pro que un docente puede indicar al crear su curso (HU-17).
// Se muestran como chips de contexto en el hero del panel (HU-16).
export const AREAS_SABER_PRO = [
  'Razonamiento Cuantitativo',
  'Lectura Crítica',
  'Competencias Ciudadanas',
  'Comunicación Escrita',
  'Inglés',
] as const

// Cómo funciona el módulo, según el rol (estado vacío HU-16.3).
// Explica el camino de entrada de cada rol hasta llegar a los simulacros.
export function obtenerPasosInicio(rol: string) {
  if (rol === 'Docente') {
    return [
      {
        titulo: 'Crea un curso Saber Pro',
        descripcion:
          'Elige el área de Saber Pro, define el nombre del curso y el sistema generará automáticamente el código de acceso (HU-17).',
      },
      {
        titulo: 'Comparte el código con tus estudiantes',
        descripcion:
          'Tus estudiantes se unen con el código de acceso automático: tú no gestionas inscripciones manualmente.',
      },
      {
        titulo: 'Prepara y evalúa a tu curso',
        descripcion:
          'Genera contenido con IA, crea simulacros y consulta la analítica y el ranking de tu grupo (HU-19 a HU-24).',
      },
    ]
  }
  return [
    {
      titulo: 'Recibe el código de tu docente',
      descripcion:
        'Pídele a tu docente el código de acceso vigente de su curso Saber Pro de preparación (HU-18).',
    },
    {
      titulo: 'Únete con el código',
      descripcion:
        'Ingresa el código en el módulo y el curso de preparación queda disponible en tu panel Saber Pro.',
    },
    {
      titulo: 'Prepárate con simulacros',
      descripcion:
        'Presenta simulacros con temporizador y consulta tu percentil de desempeño frente a tu curso (HU-21 a HU-23).',
    },
  ]
}