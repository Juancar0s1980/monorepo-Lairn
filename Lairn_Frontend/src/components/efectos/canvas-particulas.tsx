// Canvas de partículas con efecto de constelación / red neuronal.
//
// Renderiza puntos flotantes que se conectan con líneas tenues cuando
// están cerca. Ideal para fondos de branding con temática de IA/tech.
//
// Uso:
//   <div className="relative overflow-hidden ...">
//     <CanvasParticulas />
//     {/* contenido encima con z-10 */}
//   </div>
//
// Props opcionales para personalizar cantidad, distancias, colores y opacidades.
// Usa requestAnimationFrame para animación suave y ResizeObserver para adaptarse
// al tamaño del contenedor. Se limpia automáticamente al desmontar.

import { useRef, useEffect } from "react";

interface PropsCanvasParticulas {
  /** Número de partículas. Por defecto 45. */
  cantidad?: number;
  /** Distancia máxima (px) para dibujar conexión entre partículas. Por defecto 120. */
  distanciaMaxima?: number;
  /** Tamaño mínimo de partícula en px. Por defecto 1.2. */
  tamanoMin?: number;
  /** Tamaño máximo de partícula en px. Por defecto 2.5. */
  tamanoMax?: number;
  /** Velocidad mínima en px/frame. Por defecto 0.12. */
  velocidadMin?: number;
  /** Velocidad máxima en px/frame. Por defecto 0.28. */
  velocidadMax?: number;
  /** Color de las partículas en formato RGB (ej: "255, 255, 255"). Por defecto blanco. */
  color?: string;
  /** Opacidad mínima de partículas. Por defecto 0.25. */
  opacidadMin?: number;
  /** Opacidad máxima de partículas. Por defecto 0.5. */
  opacidadMax?: number;
  /** Opacidad máxima de las líneas de conexión. Por defecto 0.12. */
  opacidadLineaMax?: number;
}

interface Particula {
  x: number;
  y: number;
  vx: number;
  vy: number;
  tamano: number;
  opacidad: number;
}

// Genera un número aleatorio entre min y max.
function aleatorio(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

// Valores por defecto.
const DEFAULTS = {
  cantidad: 45,
  distanciaMaxima: 120,
  tamanoMin: 1.2,
  tamanoMax: 2.5,
  velocidadMin: 0.12,
  velocidadMax: 0.28,
  color: "255, 255, 255",
  opacidadMin: 0.25,
  opacidadMax: 0.5,
  opacidadLineaMax: 0.12,
};

export function CanvasParticulas(props: PropsCanvasParticulas = {}) {
  const {
    cantidad = DEFAULTS.cantidad,
    distanciaMaxima = DEFAULTS.distanciaMaxima,
    tamanoMin = DEFAULTS.tamanoMin,
    tamanoMax = DEFAULTS.tamanoMax,
    velocidadMin = DEFAULTS.velocidadMin,
    velocidadMax = DEFAULTS.velocidadMax,
    color = DEFAULTS.color,
    opacidadMin = DEFAULTS.opacidadMin,
    opacidadMax = DEFAULTS.opacidadMax,
    opacidadLineaMax = DEFAULTS.opacidadLineaMax,
  } = props;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animacionRef = useRef<number>(0);
  const particulasRef = useRef<Particula[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Crea una partícula con posición y velocidad aleatorias.
    const crearParticula = (ancho: number, alto: number): Particula => ({
      x: aleatorio(0, ancho),
      y: aleatorio(0, alto),
      vx:
        aleatorio(velocidadMin, velocidadMax) *
        (Math.random() > 0.5 ? 1 : -1),
      vy:
        aleatorio(velocidadMin, velocidadMax) *
        (Math.random() > 0.5 ? 1 : -1),
      tamano: aleatorio(tamanoMin, tamanoMax),
      opacidad: aleatorio(opacidadMin, opacidadMax),
    });

    // Ajusta el tamaño del canvas al contenedor.
    const ajustarTamano = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      const { width, height } = parent.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;
    };

    ajustarTamano();

    // Inicializa partículas.
    particulasRef.current = Array.from({ length: cantidad }, () =>
      crearParticula(canvas.width, canvas.height)
    );

    // Bucle principal de animación.
    const animar = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      const particulas = particulasRef.current;

      // Actualizar posiciones.
      for (const p of particulas) {
        p.x += p.vx;
        p.y += p.vy;

        // Rebotar en los bordes.
        if (p.x <= 0 || p.x >= width) p.vx *= -1;
        if (p.y <= 0 || p.y >= height) p.vy *= -1;

        // Mantener dentro de los límites.
        p.x = Math.max(0, Math.min(width, p.x));
        p.y = Math.max(0, Math.min(height, p.y));
      }

      // Dibujar conexiones entre partículas cercanas.
      ctx.lineWidth = 0.6;
      for (let i = 0; i < particulas.length; i++) {
        for (let j = i + 1; j < particulas.length; j++) {
          const dx = particulas[i].x - particulas[j].x;
          const dy = particulas[i].y - particulas[j].y;
          const distancia = Math.sqrt(dx * dx + dy * dy);

          if (distancia < distanciaMaxima) {
            // Opacidad proporcional a la cercanía.
            const opacidad =
              (1 - distancia / distanciaMaxima) * opacidadLineaMax;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(${color}, ${opacidad})`;
            ctx.moveTo(particulas[i].x, particulas[i].y);
            ctx.lineTo(particulas[j].x, particulas[j].y);
            ctx.stroke();
          }
        }
      }

      // Dibujar partículas.
      for (const p of particulas) {
        ctx.beginPath();
        ctx.fillStyle = `rgba(${color}, ${p.opacidad})`;
        ctx.arc(p.x, p.y, p.tamano, 0, Math.PI * 2);
        ctx.fill();
      }

      animacionRef.current = requestAnimationFrame(animar);
    };

    animacionRef.current = requestAnimationFrame(animar);

    // Observer para ajustar el tamaño si el contenedor cambia.
    const observer = new ResizeObserver(ajustarTamano);
    const parent = canvas.parentElement;
    if (parent) observer.observe(parent);

    return () => {
      cancelAnimationFrame(animacionRef.current);
      observer.disconnect();
    };
  }, [
    cantidad,
    distanciaMaxima,
    tamanoMin,
    tamanoMax,
    velocidadMin,
    velocidadMax,
    color,
    opacidadMin,
    opacidadMax,
    opacidadLineaMax,
  ]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 z-0 pointer-events-none"
      aria-hidden="true"
    />
  );
}
