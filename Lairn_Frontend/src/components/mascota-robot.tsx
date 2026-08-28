// Mascota robot del proyecto: SVG propio (no hay ningún archivo de imagen
// del robot en el repo). Silueta única cabeza+cuerpo (sin piezas sueltas),
// cara simple y amigable, y un birrete de graduación como guiño académico
// en vez de accesorios flotando por separado.
//
// Colores FIJOS a propósito (no tokens de tema como fill-card/fill-primary):
// es un elemento de marca que vive sobre el panel de branding del login,
// que también es de colores fijos — así el robot se ve igual sin importar
// si el resto de la app está en modo claro u oscuro (evita el bug de un
// robot "invisible" al fundirse con un fondo oscuro).
//
// Uso: <MascotaRobot className="h-[420px] w-auto" />

export function MascotaRobot({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Mascota robot de PseudoTutor"
    >
      {/* Sombra de apoyo */}
      <ellipse cx="100" cy="228" rx="46" ry="7" fill="#14212E" fillOpacity="0.1" />

      {/* Pies (más abajo que el borde inferior del cuerpo, para que no queden tapados) */}
      <ellipse cx="76" cy="227" rx="15" ry="9" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2" />
      <ellipse cx="124" cy="227" rx="15" ry="9" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2" />

      {/* Brazos: bultos redondeados pegados al cuerpo, nada colgando suelto */}
      <rect x="34" y="150" width="18" height="42" rx="9" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2" transform="rotate(-8 43 171)" />
      <rect x="148" y="150" width="18" height="42" rx="9" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2" transform="rotate(8 157 171)" />

      {/* Cuerpo */}
      <rect x="46" y="140" width="108" height="82" rx="38" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2.5" />

      {/* Luz de pecho ("sistema activo") */}
      <circle cx="100" cy="176" r="13" fill="#F6F9FC" stroke="#DCE7F0" strokeWidth="1.5" />
      <circle cx="100" cy="176" r="5" fill="#2B7CD3">
        <animate attributeName="opacity" values="1;0.5;1" dur="2.6s" repeatCount="indefinite" />
      </circle>

      {/* Cabeza — silueta continua con el cuerpo (se solapan, sin cuello separado) */}
      <rect x="36" y="34" width="128" height="110" rx="50" fill="#FFFFFF" stroke="#DCE7F0" strokeWidth="2.5" />

      {/* Orejas */}
      <circle cx="40" cy="86" r="9" fill="#2B7CD3" />
      <circle cx="160" cy="86" r="9" fill="#2B7CD3" />

      {/* Visor */}
      <rect x="58" y="66" width="84" height="46" rx="23" fill="#14212E" />

      {/* Ojo izquierdo, abierto */}
      <circle cx="82" cy="89" r="9" fill="#4FC3D9" />
      <circle cx="85" cy="86" r="2.5" fill="#FFFFFF" />

      {/* Ojo derecho, guiño amigable */}
      <path d="M108 90 Q118 82 128 90" stroke="#4FC3D9" strokeWidth="4" strokeLinecap="round" />

      {/* Sonrisa */}
      <path d="M90 120 Q100 126 110 120" stroke="#5A6B7C" strokeWidth="3" strokeLinecap="round" />

      {/* Birrete de graduación, ligeramente inclinado, apoyado sobre la cabeza (se solapan, sin hueco) */}
      <g transform="rotate(-8 100 30)">
        <rect x="92" y="24" width="16" height="16" rx="4" fill="#2B7CD3" />
        <rect x="60" y="18" width="80" height="10" rx="4" fill="#2B7CD3" />
        <line x1="133" y1="21" x2="140" y2="39" stroke="#1F63AE" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="140" cy="40" r="4" fill="#4FC3D9" />
      </g>
    </svg>
  )
}
