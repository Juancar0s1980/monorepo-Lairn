// Dashboard del Docente.
//
// Muestra una vista completa de la gestión académica con 3 secciones:
//   1. Header personalizado con saludo y fecha
//   2. Stats rápidas (cursos, exámenes, estudiantes, promedio general)
//   3. Mis Cursos con carrusel de cards
//

import { Link } from "react-router-dom";
import { useAuth } from "@/context/contexto-auth/use-auth";
import { useDashboardDocente } from "@/hooks/use-dashboard-docente";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CardCursoDocente } from "@/components/card-curso-docente";
import { CardStat } from "@/components/card-stat";
import { EncabezadoPagina } from "@/components/encabezado-pagina";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "@/components/ui/carousel";
import {
  BookOpen,
  FileText,
  Users,
  TrendingUp,
  Calendar,
  ArrowRight,
  AlertCircle,
} from "lucide-react";

// Devuelve el saludo según la hora del día.
function obtenerSaludo(): string {
  const hora = new Date().getHours();
  if (hora < 12) return "Buenos días";
  if (hora < 18) return "Buenas tardes";
  return "Buenas noches";
}

// Formatea la fecha actual en español.
function formatearFecha(): string {
  return new Date().toLocaleDateString("es-CO", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

// Devuelve la primera parte del nombre (primer nombre).
function obtenerNombre(usuario: { first_name: string } | null): string {
  if (!usuario?.first_name) return "Docente";
  return usuario.first_name;
}

// Componente de skeleton para estado de carga.
function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="h-8 w-16 rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function PaginaDashboardDocente() {
  const { usuario } = useAuth();
  const { cursos, stats, cargando, error } = useDashboardDocente();

  // --- Estado de carga ---
  if (cargando) {
    return (
      <div className="space-y-6">
        {/* Skeleton header */}
        <div className="animate-pulse space-y-2">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-4 w-48 rounded bg-muted" />
        </div>
        {/* Skeleton stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        {/* Skeleton contenido */}
        <div className="grid gap-4 lg:grid-cols-2">
          <SkeletonCard className="h-64" />
          <SkeletonCard className="h-64" />
        </div>
      </div>
    );
  }

  // --- Estado de error ---
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {error}
        </p>
        <p className="text-xs text-muted-foreground/70">
          Intenta recargar la página
        </p>
      </div>
    );
  }

  const saludo = obtenerSaludo();
  const fecha = formatearFecha();
  const nombre = obtenerNombre(usuario);

  return (
    <div className="space-y-6">
      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 1 — Header personalizado
          ═══════════════════════════════════════════════════════════ */}
      <EncabezadoPagina
        eyebrow="Panel del docente"
        titulo={`${saludo}, ${nombre}`}
        subtitulo={
          <span className="flex items-center gap-1.5 capitalize">
            <Calendar className="h-3.5 w-3.5" />
            {fecha}
          </span>
        }
        accion={
          stats.totalCursos > 0 && (
            <p className="font-accent text-base text-primary">
              {stats.promedioGeneral >= 4.0
                ? "¡Excelente rendimiento en tus cursos!"
                : stats.promedioGeneral >= 3.0
                  ? "Buen progreso, sigue así."
                  : "Tus cursos están en progreso."}
            </p>
          )
        }
      />

      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 2 — Stats rápidas (4 cards)
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Cursos creados */}
        <CardStat
          titulo="Mis cursos"
          valor={stats.totalCursos}
          icono={BookOpen}
          variante="primary"
          subtitulo={
            stats.totalCursos === 1 ? "curso activo" : "cursos activos"
          }
        />

        {/* Exámenes creados */}
        <CardStat
          titulo="Exámenes creados"
          valor={stats.totalExamenes}
          icono={FileText}
          subtitulo="en todos los cursos"
        />

        {/* Total estudiantes */}
        <CardStat
          titulo="Estudiantes"
          valor={stats.totalEstudiantes}
          icono={Users}
          variante="primary"
          subtitulo="inscritos en tus cursos"
        />

        {/* Promedio general */}
        <CardStat
          titulo="Promedio general"
          valor={
            stats.totalCursos > 0 ? stats.promedioGeneral.toFixed(1) : "—"
          }
          icono={TrendingUp}
          subtitulo={
            stats.totalCursos > 0 ? "promedio de tus cursos" : "sin datos aún"
          }
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 3 — Mis Cursos
          ═══════════════════════════════════════════════════════════ */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-heading text-lg">Mis Cursos</h3>
          {cursos.length > 0 && (
            <Link to="/mis-cursos">
              <Button variant="ghost" size="sm" className="gap-1 text-xs">
                Ver todos
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          )}
        </div>

        {/* Estado vacío */}
        {cursos.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-10 text-center">
            <BookOpen className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              No has creado ningún curso
            </p>
            <Link to="/mis-cursos" className="mt-3">
              <Button size="sm">Crear mi primer curso</Button>
            </Link>
          </div>
        )}

        {/* Carrusel de cursos */}
        {cursos.length > 0 && (
          <Carousel
            opts={{
              align: "start",
              slidesToScroll: 1,
            }}
            className="w-full"
          >
            <CarouselContent className="-ml-4">
              {cursos.map((curso) => (
                <CarouselItem
                  key={curso.id}
                  className="pl-4 basis-full sm:basis-1/2 lg:basis-1/3"
                >
                  <CardCursoDocente
                    id={curso.id}
                    nombre={curso.nombre}
                    descripcion={curso.descripcion}
                    codigo={curso.codigo}
                    totalInscritos={curso.totalInscritos}
                    totalExamenes={curso.totalExamenes}
                    notaPromedio={curso.notaPromedio}
                    tasaAprobados={curso.tasaAprobados}
                  />
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="-left-4" />
            <CarouselNext className="-right-4" />
          </Carousel>
        )}
      </div>
    </div>
  );
}
