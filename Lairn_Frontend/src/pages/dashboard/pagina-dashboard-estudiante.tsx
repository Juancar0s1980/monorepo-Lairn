// Dashboard del Estudiante.
//
// Muestra una vista completa del progreso académico con 6 secciones:
//   1. Header personalizado con saludo y fecha
//   2. Stats rápidas (cursos, exámenes, nota promedio, mejor nota)
//   3. Mis Cursos con barra de progreso
//   4. Actividad reciente (timeline de últimos intentos)
//   5. Exámenes disponibles por curso
//   6. Rendimiento por concepto (chart de barras)
//
// Todos los datos provienen de la API — sin datos quemados.

import { Link } from "react-router-dom";
import { useAuth } from "@/context/contexto-auth/use-auth";
import { useDashboardEstudiante } from "@/hooks/use-dashboard-estudiante";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardCursoEstudiante } from "@/components/card-curso-estudiante";
import { CardStat } from "@/components/card-stat";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "@/components/ui/carousel";

import {
  BookOpen,
  ClipboardCheck,
  GraduationCap,
  Trophy,
  Clock,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Calendar,
  Target,
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
  if (!usuario?.first_name) return "Estudiante";
  return usuario.first_name;
}

// Calcula tiempo relativo desde una fecha.
function tiempoRelativo(fechaISO: string): string {
  const ahora = Date.now();
  const fecha = new Date(fechaISO).getTime();
  const diff = ahora - fecha;
  const minutos = Math.floor(diff / 60000);
  const horas = Math.floor(diff / 3600000);
  const dias = Math.floor(diff / 86400000);

  if (minutos < 1) return "Ahora mismo";
  if (minutos < 60) return `Hace ${minutos}m`;
  if (horas < 24) return `Hace ${horas}h`;
  if (dias === 1) return "Ayer";
  if (dias < 7) return `Hace ${dias}d`;
  return new Date(fechaISO).toLocaleDateString("es-CO", {
    day: "numeric",
    month: "short",
  });
}

// Devuelve el color de la nota según su valor.
function colorNota(nota: number): string {
  if (nota >= 4.0) return "text-emerald-600 dark:text-emerald-400";
  if (nota >= 3.0) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

// Devuelve el color de fondo del badge de dificultad.
function badgeDificultad(dificultad: number): string {
  if (dificultad === 1)
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400";
  if (dificultad === 2)
    return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
}

function labelDificultad(dificultad: number): string {
  if (dificultad === 1) return "Básico";
  if (dificultad === 2) return "Intermedio";
  return "Avanzado";
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

export default function PaginaDashboardEstudiante() {
  const { usuario } = useAuth();
  const {
    cursos,
    avances,
    examenesPorCurso,
    stats,
    actividadReciente,
    cargando,
    error,
  } = useDashboardEstudiante();

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
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            {saludo}, {nombre}
          </h2>
          <p className="flex items-center gap-1.5 text-sm text-muted-foreground capitalize">
            <Calendar className="h-3.5 w-3.5" />
            {fecha}
          </p>
        </div>
        {stats.totalExamenes > 0 && (
          <p className="text-xs text-muted-foreground italic">
            {stats.notaPromedio >= 4.0
              ? "¡Excelente rendimiento, sigue así!"
              : stats.notaPromedio >= 3.0
                ? "Buen progreso, puedes mejorar aún más."
                : "Cada intento es una oportunidad de aprender."}
          </p>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 2 — Stats rápidas (4 cards)
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Cursos inscritos */}
        <CardStat
          titulo="Cursos inscritos"
          valor={stats.totalCursos}
          icono={BookOpen}
          variante="primary"
          subtitulo={stats.totalCursos === 1 ? "curso activo" : "cursos activos"}
        />

        {/* Exámenes rendidos */}
        <CardStat
          titulo="Exámenes rendidos"
          valor={stats.totalExamenes}
          icono={ClipboardCheck}
          subtitulo="intentos totales"
        />

        {/* Nota promedio */}
        <CardStat
          titulo="Nota promedio"
          valor={stats.totalExamenes > 0 ? stats.notaPromedio.toFixed(2) : "—"}
          icono={GraduationCap}
          variante="primary"
          subtitulo={stats.totalExamenes > 0 ? "escala 1.0 – 5.0" : "sin datos aún"}
        />

        {/* Mejor nota */}
        <CardStat
          titulo="Mejor nota"
          valor={stats.totalExamenes > 0 ? stats.mejorNota.toFixed(1) : "—"}
          icono={Trophy}
          subtitulo={stats.totalExamenes > 0 ? "tu mejor resultado" : "sin datos aún"}
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 3 — Mis Cursos
          ═══════════════════════════════════════════════════════════ */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Mis Cursos</h3>
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
              No estás inscrito en ningún curso
            </p>
            <Link to="/mis-cursos" className="mt-3">
              <Button size="sm">Inscribirme a un curso</Button>
            </Link>
          </div>
        )}

        {/* Carrusel de cursos con progreso */}
        {cursos.length > 0 && (
          <Carousel
            opts={{
              align: "start",
              slidesToScroll: 1,
            }}
            className="w-full"
          >
            <CarouselContent className="-ml-4">
              {cursos.map((curso) => {
                const avance = avances.get(curso.id);
                const examenes = examenesPorCurso.get(curso.id) ?? [];

                return (
                  <CarouselItem
                    key={curso.id}
                    className="pl-4 basis-full sm:basis-1/2 lg:basis-1/3"
                  >
                    <CardCursoEstudiante
                      id={curso.id}
                      nombre={curso.nombre}
                      descripcion={curso.descripcion}
                      docente={curso.docente}
                      examenesRendidos={avance?.total_examenes_presentados ?? 0}
                      totalExamenes={examenes.length}
                      notaPromedio={avance?.nota_promedio}
                    />
                  </CarouselItem>
                );
              })}
            </CarouselContent>
            <CarouselPrevious className="-left-4" />
            <CarouselNext className="-right-4" />
          </Carousel>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECCIÓN 4 + 5 — Actividad reciente + Exámenes disponibles
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Actividad reciente */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Actividad reciente</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {actividadReciente.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <ClipboardCheck className="h-8 w-8 text-muted-foreground/40" />
                <p className="mt-2 text-xs text-muted-foreground">
                  Aún no has rendido exámenes
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {actividadReciente.map((actividad, index) => {
                  const aprobo = actividad.nota >= 3.0;
                  return (
                    <Link
                      key={`${actividad.examenId}-${index}`}
                      to={`/analitica/curso/${actividad.cursoId}`}
                    >
                      <div className="flex items-center gap-3 rounded-lg p-2.5 transition-colors hover:bg-muted/50 group">
                        {/* Icono de resultado */}
                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                            aprobo
                              ? "bg-emerald-100 dark:bg-emerald-900/30"
                              : "bg-red-100 dark:bg-red-900/30"
                          }`}
                        >
                          {aprobo ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                          )}
                        </div>

                        {/* Detalle */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium line-clamp-1 group-hover:text-primary transition-colors">
                            Examen #{actividad.examenId}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {actividad.cursoNombre}
                          </p>
                        </div>

                        {/* Nota y fecha */}
                        <div className="text-right shrink-0">
                          <p
                            className={`text-sm font-bold ${colorNota(actividad.nota)}`}
                          >
                            {actividad.nota.toFixed(1)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {tiempoRelativo(actividad.completadoEn)}
                          </p>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Exámenes disponibles */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Exámenes disponibles</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {(() => {
              // Recopilar exámenes de todos los cursos.
              const examenesDisponibles: {
                examen: import("@/types/examen").Examen;
                cursoNombre: string;
              }[] = [];

              for (const curso of cursos) {
                const examenes = examenesPorCurso.get(curso.id) ?? [];
                for (const examen of examenes) {
                  examenesDisponibles.push({
                    examen,
                    cursoNombre: curso.nombre,
                  });
                }
              }

              if (examenesDisponibles.length === 0) {
                return (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <Target className="h-8 w-8 text-muted-foreground/40" />
                    <p className="mt-2 text-xs text-muted-foreground">
                      No hay exámenes disponibles
                    </p>
                  </div>
                );
              }

              return (
                <div className="space-y-2.5">
                  {examenesDisponibles
                    .slice(0, 6)
                    .map(({ examen, cursoNombre }) => (
                      <Link
                        key={examen.id}
                        to={`/mis-cursos/${examen.curso}/examenes/${examen.id}/rendir`}
                      >
                        <div className="flex items-center gap-3 rounded-lg p-2.5 transition-colors hover:bg-muted/50 group">
                          {/* Icono */}
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <ClipboardCheck className="h-4 w-4 text-primary" />
                          </div>

                          {/* Detalle */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium line-clamp-1 group-hover:text-primary transition-colors">
                              {examen.titulo}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <span>{cursoNombre}</span>
                              <span>·</span>
                              <span>{examen.tiempo} min</span>
                              <span>·</span>
                              <span>{examen.num_preguntas} preg.</span>
                            </div>
                          </div>

                          {/* Dificultad badge */}
                          <Badge
                            variant="outline"
                            className={`shrink-0 text-[10px] font-semibold ${badgeDificultad(examen.dificultad_inicial)}`}
                          >
                            {labelDificultad(examen.dificultad_inicial)}
                          </Badge>
                        </div>
                      </Link>
                    ))}

                  {examenesDisponibles.length > 6 && (
                    <Link to="/mis-cursos">
                      <p className="text-center text-xs text-muted-foreground hover:text-primary transition-colors pt-1">
                        Ver todos los exámenes ({examenesDisponibles.length})
                      </p>
                    </Link>
                  )}
                </div>
              );
            })()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
