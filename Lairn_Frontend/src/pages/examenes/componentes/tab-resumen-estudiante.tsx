// Tab de resumen global del curso para el estudiante.
//
// Muestra el dominio de conceptos del estudiante usando el endpoint mi-conocimiento.
// Incluye cards de conceptos destacados, gráfico de dona por nivel,
// barras de top conceptos y tabla completa.

import { useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  AlertTriangle,
  Zap,
  CheckCircle2,
  TrendingUp,
  Award,
  Calendar,
} from "lucide-react";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { PieChart, Pie, Cell } from "recharts";
import type { MiConocimiento } from "@/types/analitica";
import type { StatsCurso } from "@/hooks/use-examenes-curso";

// Formatea una fecha ISO a formato legible.
function formatearFecha(fecha: string | null): string {
  if (!fecha) return "—";
  return new Date(fecha).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// Devuelve el color de la nota según su valor.
function colorNota(nota: number): string {
  if (nota >= 4.0) return "text-emerald-600 dark:text-emerald-400";
  if (nota >= 3.0) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

// Colores para los niveles de dominio.
// Usamos la paleta de purpuras del tema para mantener consistencia visual en toda la app.
const COLORES_NIVEL: Record<number, string> = {
  1: "var(--purple-5)",
  2: "var(--purple-3)",
  3: "var(--purple-1)",
};

const LABELS_NIVEL: Record<number, string> = {
  1: "Débil",
  2: "En desarrollo",
  3: "Dominado",
};

export function TabResumenEstudiante({
  conocimiento,
  stats,
}: {
  conocimiento: MiConocimiento;
  stats: StatsCurso;
}) {
  const { resumen_global } = conocimiento;
  const conceptos = resumen_global.conceptos;

  // Conteo por nivel.
  const conteoPorNivel = useMemo(() => {
    const conteo = { 1: 0, 2: 0, 3: 0 };
    for (const c of conceptos) {
      conteo[c.nivel as keyof typeof conteo]++;
    }
    return conteo;
  }, [conceptos]);

  // Datos para gráfico de dona.
  const datosDona = useMemo(
    () =>
      [
        { nivel: "Débil", cantidad: conteoPorNivel[1], fill: COLORES_NIVEL[1] },
        {
          nivel: "En desarrollo",
          cantidad: conteoPorNivel[2],
          fill: COLORES_NIVEL[2],
        },
        {
          nivel: "Dominado",
          cantidad: conteoPorNivel[3],
          fill: COLORES_NIVEL[3],
        },
      ].filter((d) => d.cantidad > 0),
    [conteoPorNivel],
  );

  const donaConfig = {
    cantidad: { label: "Conceptos" },
  } satisfies ChartConfig;

  // Top 5 conceptos por % de acierto (solo mayores a 50%).
  const topConceptos = useMemo(
    () =>
      [...conceptos]
        .filter((c) => c.porcentaje_acierto > 50)
        .sort((a, b) => b.porcentaje_acierto - a.porcentaje_acierto)
        .slice(0, 5),
    [conceptos],
  );

  // Bottom 5 conceptos por % de acierto (solo menores o iguales a 49%).
  const bottomConceptos = useMemo(
    () =>
      [...conceptos]
        .filter((c) => c.porcentaje_acierto <= 49)
        .sort((a, b) => a.porcentaje_acierto - b.porcentaje_acierto)
        .slice(0, 5),
    [conceptos],
  );

  // Nota: el backend entrega los nombres del concepto más débil/fuerte,
  // pero en esta vista no se usan directamente (se derivan top/bottom 5).

  return (
    <div className="space-y-6">
      {/* Resumen del curso */}
      {stats.totalExamenes > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Resumen del curso</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Fila compacta de métricas: consistente con el estilo de cards del resto del sistema. */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>
                    Promedio:{" "}
                    <span
                      className={`font-semibold ${colorNota(stats.notaPromedio)}`}
                    >
                      {stats.examenesRendidos > 0
                        ? stats.notaPromedio.toFixed(2)
                        : "—"}
                    </span>
                  </span>
                </div>
                <div className="hidden sm:block h-3 w-px bg-border" />
                <div className="flex items-center gap-1.5">
                  <Award className="h-3.5 w-3.5" />
                  <span>
                    Mejor nota:{" "}
                    <span
                      className={`font-semibold ${colorNota(stats.mejorNota)}`}
                    >
                      {stats.examenesRendidos > 0
                        ? stats.mejorNota.toFixed(2)
                        : "—"}
                    </span>
                  </span>
                </div>
                <div className="hidden sm:block h-3 w-px bg-border" />
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                  <span>
                    Dominados:{" "}
                    <span className="font-semibold text-primary">
                      {conteoPorNivel[3]}
                    </span>
                    <span className="text-muted-foreground">
                      /{conceptos.length}
                    </span>
                  </span>
                </div>
                <div className="hidden sm:block h-3 w-px bg-border" />
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>
                    Último examen:{" "}
                    <span className="font-semibold text-foreground">
                      {formatearFecha(stats.ultimoExamenEn)}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gráficos */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Conceptos fuertes y débiles */}
        <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2">
          {/* Fuertes */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                Conceptos más fuertes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topConceptos.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">
                  No hay conceptos con más del 50% de acierto
                </p>
              ) : (
                topConceptos.map((c) => (
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

          {/* Débiles */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                Conceptos más débiles
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {bottomConceptos.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">
                  No hay conceptos con 49% o menos de acierto
                </p>
              ) : (
                bottomConceptos.map((c) => (
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
        </div>
        {/* Dona: distribución por nivel */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución por nivel</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-center">
              <ChartContainer
                config={donaConfig}
                className="h-[250px] w-full max-w-[300px]"
              >
                <PieChart>
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Pie
                    data={datosDona}
                    dataKey="cantidad"
                    nameKey="nivel"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    strokeWidth={2}
                    stroke="hsl(var(--background))"
                  >
                    {datosDona.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ChartContainer>
            </div>

            {/* Leyenda manual */}
            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs">
              {datosDona.map((entry) => (
                <div key={entry.nivel} className="flex items-center gap-1.5">
                  <div
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: entry.fill }}
                  />
                  <span className="text-muted-foreground">
                    {entry.nivel} ({entry.cantidad})
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabla de todos los conceptos */}
      <Card>
        <CardHeader>
          <CardTitle>Todos los conceptos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[400px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-background z-10">
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-3 font-medium">Concepto</th>
                  <th className="pb-2 pr-3 font-medium text-center">
                    Intentos
                  </th>
                  <th className="pb-2 pr-3 font-medium text-center">
                    Correctas
                  </th>
                  <th className="pb-2 pr-3 font-medium text-center">
                    % Acierto
                  </th>
                  <th className="pb-2 font-medium text-center">Nivel</th>
                </tr>
              </thead>
              <tbody>
                {conceptos.map((c, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2.5 pr-3">
                      <span className="line-clamp-1">{c.concepto}</span>
                    </td>
                    <td className="py-2.5 pr-3 text-center text-muted-foreground">
                      {c.intentos}
                    </td>
                    <td className="py-2.5 pr-3 text-center text-muted-foreground">
                      {c.correctas}
                    </td>
                    <td className="py-2.5 pr-3 text-center font-mono font-medium">
                      {c.porcentaje_acierto}%
                    </td>
                    <td className="py-2.5 text-center">
                      <span
                        className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
                        style={{
                          backgroundColor: `color-mix(in oklch, ${COLORES_NIVEL[c.nivel]} 18%, transparent)`,
                          color: `color-mix(in oklch, ${COLORES_NIVEL[c.nivel]} 92%, hsl(var(--foreground)))`,
                        }}
                      >
                        {LABELS_NIVEL[c.nivel]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
