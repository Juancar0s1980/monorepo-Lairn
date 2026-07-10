// Tab de analítica para el docente.
//
// Muestra rendimiento por estudiante (tabla con Sheet de detalle),
// rendimiento por examen (cards), análisis por dificultad y conceptos
// débiles/fuertes del curso.

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Loader2,
  Users,
  Mail,
  TrendingUp,
  BarChart3,
  Target,
  Zap,
} from "lucide-react";
import { colorNota, colorAprobados, coloresIntentos } from "../utilidades";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  Label,
} from "recharts";
import type {
  ResumenCursoDocente,
  PatronesCurso,
  EstudianteResumen,
} from "@/types/analitica";

// Selecciona un color púrpura consistente para una card según un id.
function colorParaCard(id: number) {
  return coloresIntentos[Math.abs(id) % coloresIntentos.length];
}

interface TabAnaliticaDocenteProps {
  resumen: ResumenCursoDocente | null;
  patrones: PatronesCurso | null;
  cargandoPatrones: boolean;
  cargandoResumen: boolean;
}

export function TabAnaliticaDocente({
  resumen,
  patrones,
  cargandoPatrones,
  cargandoResumen,
}: TabAnaliticaDocenteProps) {
  const [estudianteDetalle, setEstudianteDetalle] =
    useState<EstudianteResumen | null>(null);

  // Filtra conceptos por umbrales para evitar inconsistencias si el backend cambia el criterio.
  const conceptosDebiles = useMemo(() => {
    return (patrones?.conceptos_mas_debiles ?? [])
      .filter((c) => c.porcentaje_acierto <= 49)
      .slice(0, 5);
  }, [patrones]);

  const conceptosFuertes = useMemo(() => {
    return (patrones?.conceptos_mas_fuertes ?? [])
      .filter((c) => c.porcentaje_acierto >= 50)
      .slice(0, 5);
  }, [patrones]);

  // Datos para gráfico: dificultad vs acierto (promedio de curso).
  const datosDificultad = useMemo(() => {
    const lista = patrones?.analisis_por_dificultad ?? [];
    const porNivel = new Map(lista.map((d) => [d.dificultad, d]));
    return [1, 2, 3].map((nivel) => {
      const dif = porNivel.get(nivel);
      return {
        dificultad:
          dif?.nombre ??
          (nivel === 1 ? "Básico" : nivel === 2 ? "Intermedio" : "Avanzado"),
        aciertos: dif?.porcentaje_acierto ?? 0,
      };
    });
  }, [patrones]);

  const configDificultad = {
    aciertos: { label: "Acierto (%)", color: "var(--purple-2)" },
  } satisfies ChartConfig;

  return (
    <div className="space-y-6">
      {/* Estado de carga */}
      {cargandoPatrones && cargandoResumen && (
        <div className="flex h-[40vh] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Resumen del curso */}
      {!cargandoResumen && resumen && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Resumen del curso</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Fila compacta de métricas: consistente con el estilo de cards del resto del sistema. */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  <span>
                    Inscritos:{" "}
                    <span className="font-semibold text-foreground">
                      {resumen.total_inscritos}
                    </span>
                  </span>
                </div>
                <div className="hidden sm:block h-3 w-px bg-border" />
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>
                    Promedio:{" "}
                    <span
                      className={`font-semibold ${colorNota(resumen.nota_promedio_curso)}`}
                    >
                      {resumen.nota_promedio_curso.toFixed(1)}
                    </span>
                  </span>
                </div>
                <div className="hidden sm:block h-3 w-px bg-border" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Estado vacío de analítica */}
      {!cargandoPatrones &&
        (!patrones || !patrones.examenes || patrones.examenes.length === 0) && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-12 text-center">
            <BarChart3 className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              Aún no hay datos de rendimiento
            </p>
            <p className="text-xs text-muted-foreground">
              Los datos aparecerán cuando los estudiantes rindan exámenes
            </p>
          </div>
        )}

      {/* Secciones de analítica por examen */}
      {!cargandoPatrones &&
        patrones &&
        patrones.examenes &&
        patrones.examenes.length > 0 && (
          <>
            {/* Sección 2: Rendimiento por Examen */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Rendimiento por Examen
              </h3>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {patrones.examenes.map((examen) => (
                  <Card key={examen.examen_id} className="overflow-hidden">
                    <CardHeader
                      className="pb-3"
                      style={{
                        background: `linear-gradient(135deg, ${colorParaCard(examen.examen_id)}22, ${colorParaCard(examen.examen_id)}08)`,
                      }}
                    >
                      <CardTitle className="text-sm line-clamp-1">
                        {examen.titulo}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 pt-5">
                      {/* Fila compacta de métricas con separadores (mismo patrón que CardIntento). */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Users className="h-3.5 w-3.5" />
                          <span>
                            {examen.total_presentaciones} presentaciones
                          </span>
                        </div>
                        <div className="hidden sm:block h-3 w-px bg-border" />
                        <div className="flex items-center gap-1.5">
                          <span>Promedio:</span>
                          <span
                            className={`font-semibold ${colorNota(examen.nota_promedio)}`}
                          >
                            {examen.nota_promedio.toFixed(1)}
                          </span>
                        </div>
                        <div className="hidden sm:block h-3 w-px bg-border" />
                        <Badge
                          variant="outline"
                          className="text-xs bg-primary/10 text-primary border-primary/20"
                        >
                          Aprobados: {examen.porcentaje_aprobados}%
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
            {/* Sección 3: Dificultad + Conceptos (misma fila en desktop) */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Dificultad y conceptos
              </h3>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {/* Conceptos más fuertes */}
                <Card className="overflow-hidden">
                  <CardHeader
                    className="pb-3"
                    style={{
                      background: `linear-gradient(135deg, var(--purple-3)22, var(--purple-3)08)`,
                    }}
                  >
                    <CardTitle className="flex items-center justify-between text-sm">
                      <span className="inline-flex items-center gap-2">
                        <Zap className="h-4 w-4 text-primary" />
                        Conceptos más fuertes
                      </span>
                      <span className="text-xs font-normal text-muted-foreground">
                        Top 5
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-5">
                    {conceptosFuertes.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">
                        No hay conceptos con más del 50% de acierto
                      </p>
                    ) : (
                      conceptosFuertes.map((c) => (
                        <div key={c.concepto} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-foreground truncate max-w-[70%]">
                              {c.concepto.length > 30
                                ? c.concepto.slice(0, 30) + "…"
                                : c.concepto}
                            </span>
                            <span className="font-medium text-primary">
                              {c.porcentaje_acierto}%
                            </span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary transition-all"
                              style={{ width: `${c.porcentaje_acierto}%` }}
                            />
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
                {/* Conceptos más débiles */}
                <Card className="overflow-hidden">
                  <CardHeader
                    className="pb-3"
                    style={{
                      background: `linear-gradient(135deg, var(--purple-5)22, var(--purple-5)08)`,
                    }}
                  >
                    <CardTitle className="flex items-center justify-between text-sm">
                      <span className="inline-flex items-center gap-2">
                        <Target className="h-4 w-4 text-destructive" />
                        Conceptos más débiles
                      </span>
                      <span className="text-xs font-normal text-muted-foreground">
                        Top 5
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-5">
                    {conceptosDebiles.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">
                        No hay conceptos con 49% o menos de acierto
                      </p>
                    ) : (
                      conceptosDebiles.map((c) => (
                        <div key={c.concepto} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-foreground truncate max-w-[70%]">
                              {c.concepto.length > 30
                                ? c.concepto.slice(0, 30) + "…"
                                : c.concepto}
                            </span>
                            <span className="font-medium text-destructive">
                              {c.porcentaje_acierto}%
                            </span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-destructive transition-all"
                              style={{ width: `${c.porcentaje_acierto}%` }}
                            />
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>

                {/* Dificultad vs acierto */}
                <Card className="overflow-hidden">
                  <CardHeader
                    className="pb-3"
                    style={{
                      background: `linear-gradient(135deg, var(--purple-2)22, var(--purple-2)08)`,
                    }}
                  >
                    <CardTitle className="text-sm">
                      Dificultad vs acierto
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-5">
                    <ChartContainer
                      config={configDificultad}
                      className="h-[220px] w-full"
                    >
                      <BarChart data={datosDificultad}>
                        <CartesianGrid
                          stroke="var(--border)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="dificultad"
                          tick={{
                            fontSize: 11,
                            fill: "var(--muted-foreground)",
                          }}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={{
                            fontSize: 11,
                            fill: "var(--muted-foreground)",
                          }}
                        />
                        <ReferenceLine
                          y={60}
                          stroke="var(--muted-foreground)"
                          strokeDasharray="4 4"
                          strokeOpacity={0.4}
                        >
                          <Label
                            value="Aprobado"
                            position="insideTopRight"
                            fontSize={10}
                            fill="var(--muted-foreground)"
                          />
                        </ReferenceLine>
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Bar
                          dataKey="aciertos"
                          fill="var(--color-aciertos)"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ChartContainer>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Sección 1: Rendimiento por Estudiante */}
            {!cargandoResumen && resumen && resumen.estudiantes.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  Rendimiento por Estudiante
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Estudiante</TableHead>
                      <TableHead className="hidden sm:table-cell">
                        Email
                      </TableHead>
                      <TableHead className="text-center">Exámenes</TableHead>
                      <TableHead className="text-center">Promedio</TableHead>
                      <TableHead className="text-center hidden md:table-cell">
                        Aprobados
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resumen.estudiantes.map((est) => (
                      <TableRow
                        key={est.estudiante_id}
                        className="cursor-pointer"
                        onClick={() => setEstudianteDetalle(est)}
                      >
                        <TableCell>
                          <p className="font-medium">{est.nombre}</p>
                          <p className="text-xs text-muted-foreground sm:hidden flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {est.email}
                          </p>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell text-muted-foreground">
                          <div className="flex items-center gap-1.5">
                            <Mail className="h-3.5 w-3.5" />
                            {est.email}
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="text-sm font-medium">
                            {est.examenes_presentados}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span
                            className={`text-sm font-bold ${colorNota(est.nota_promedio)}`}
                          >
                            {est.nota_promedio.toFixed(1)}
                          </span>
                        </TableCell>
                        <TableCell className="text-center hidden md:table-cell">
                          <Badge
                            variant="outline"
                            className={`text-xs ${colorAprobados(
                              est.examenes_presentados > 0
                                ? Math.round(
                                    (est.aprobados / est.examenes_presentados) *
                                      100,
                                  )
                                : 0,
                            )}`}
                          >
                            {est.aprobados}/{est.examenes_presentados}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </>
        )}

      {/* Sheet de detalle del estudiante */}
      <Sheet
        open={!!estudianteDetalle}
        onOpenChange={(open) => !open && setEstudianteDetalle(null)}
      >
        <SheetContent side="right">
          {estudianteDetalle && (
            <>
              <SheetHeader>
                <SheetTitle>{estudianteDetalle.nombre}</SheetTitle>
                <SheetDescription>{estudianteDetalle.email}</SheetDescription>
              </SheetHeader>

              <div className="flex-1 overflow-y-auto space-y-4 px-4">
                {/* Stats del estudiante */}
                <div className="grid grid-cols-3 gap-3">
                  <Card size="sm">
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-muted-foreground">Exámenes</p>
                      <p className="text-lg font-bold">
                        {estudianteDetalle.examenes_presentados}
                      </p>
                    </CardContent>
                  </Card>
                  <Card size="sm">
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-muted-foreground">Promedio</p>
                      <p
                        className={`text-lg font-bold ${colorNota(estudianteDetalle.nota_promedio)}`}
                      >
                        {estudianteDetalle.nota_promedio.toFixed(1)}
                      </p>
                    </CardContent>
                  </Card>
                  <Card size="sm">
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-muted-foreground">Aprobados</p>
                      <p className="text-lg font-bold">
                        {estudianteDetalle.aprobados}/
                        {estudianteDetalle.examenes_presentados}
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Barra de aprobados */}
                {estudianteDetalle.examenes_presentados > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">
                        Tasa de aprobación
                      </span>
                      <span className="font-medium">
                        {Math.round(
                          (estudianteDetalle.aprobados /
                            estudianteDetalle.examenes_presentados) *
                            100,
                        )}
                        %
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          Math.round(
                            (estudianteDetalle.aprobados /
                              estudianteDetalle.examenes_presentados) *
                              100,
                          ) >= 80
                            ? "bg-emerald-500"
                            : Math.round(
                                  (estudianteDetalle.aprobados /
                                    estudianteDetalle.examenes_presentados) *
                                    100,
                                ) >= 60
                              ? "bg-amber-500"
                              : "bg-red-500"
                        }`}
                        style={{
                          width: `${Math.round(
                            (estudianteDetalle.aprobados /
                              estudianteDetalle.examenes_presentados) *
                              100,
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Conceptos débiles */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground">
                    Conceptos débiles
                  </h4>
                  {estudianteDetalle.conceptos_debiles.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {estudianteDetalle.conceptos_debiles.map(
                        (concepto, i) => (
                          <Badge
                            key={i}
                            variant="outline"
                            className="text-xs bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800"
                          >
                            {concepto}
                          </Badge>
                        ),
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Sin conceptos débiles registrados
                    </p>
                  )}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
