// Ícono de marca de PseudoTutor: versión mínima, estilo lucide (stroke +
// currentColor), de la cara de la mascota robot (ver mascota-robot.tsx) —
// cabeza redondeada, orejas punto y guiño. Reemplaza al genérico
// BrainCircuit de lucide-react en los puntos donde se usa como LOGO
// (badge del login, header, loader de rutas), no donde BrainCircuit se usa
// como ícono de contenido para representar "IA/redes neuronales".
//
// Usa currentColor (no colores fijos) a propósito: a diferencia de la
// mascota del panel de branding (colores fijos), este ícono vive en
// superficies que sí cambian con el tema (header, loader) y debe seguir
// `text-primary` como cualquier ícono de lucide.

export function LogoMarca({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      role="img"
      aria-label="PseudoTutor"
    >
      <rect x="4" y="6" width="16" height="13" rx="6" />
      <circle cx="3.5" cy="12.5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="20.5" cy="12.5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="9.2" cy="12.5" r="1.15" fill="currentColor" stroke="none" />
      <path d="M13.2 11.7q1.8-1.6 3.6 0" />
    </svg>
  )
}
