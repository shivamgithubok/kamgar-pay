import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ChartPoint = {
  label: string;
  value: number;
  secondaryValue?: number;
};

type LineChartProps = {
  title: string;
  description: string;
  points: ChartPoint[];
  valueLabel?: string;
  secondaryLabel?: string;
  height?: number;
  valueFormatter?: (val: number) => string;
};

export function LineChart({
  title,
  description,
  points,
  valueLabel = "Value",
  secondaryLabel,
  valueFormatter = (v) => String(v),
}: LineChartProps) {
  const maxVal = Math.max(...points.flatMap((p) => [p.value, p.secondaryValue ?? 0]), 1);

  // Generate SVG path points
  const width = 600;
  const height = 180;
  const padding = 20;
  const usableWidth = width - padding * 2;
  const usableHeight = height - padding * 2;

  const getX = (index: number) => {
    if (points.length <= 1) return width / 2;
    return padding + (index / (points.length - 1)) * usableWidth;
  };

  const getY = (val: number) => {
    return height - padding - (val / maxVal) * usableHeight;
  };

  const pathD = points.length > 0
    ? points.map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(p.value)}`).join(" ")
    : "";

  const secondaryPathD = secondaryLabel && points.length > 0
    ? points.map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(p.secondaryValue ?? 0)}`).join(" ")
    : "";

  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardHeader>
        <CardTitle className="text-base font-bold">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <div className="flex h-44 items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
            No trend data available.
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-4 text-xs font-semibold text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-labour-ink" />
                {valueLabel}
              </span>
              {secondaryLabel ? (
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-labour-amber" />
                  {secondaryLabel}
                </span>
              ) : null}
            </div>

            <div className="relative">
              <svg viewBox={`0 0 ${width} ${height}`} className="w-full overflow-visible">
                {/* Grid lines */}
                <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="currentColor" className="text-border" strokeDasharray="3 3" />
                <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="currentColor" className="text-border" strokeDasharray="3 3" />
                <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="currentColor" className="text-border" />

                {/* Secondary line if applicable */}
                {secondaryPathD ? (
                  <path d={secondaryPathD} fill="none" stroke="rgb(245, 158, 11)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                ) : null}

                {/* Main trend line */}
                <path d={pathD} fill="none" stroke="rgb(15, 23, 42)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

                {/* Data Points */}
                {points.map((p, i) => (
                  <g key={p.label} className="group cursor-pointer">
                    <circle cx={getX(i)} cy={getY(p.value)} r="4.5" className="fill-labour-paper stroke-labour-ink stroke-[2.5]" />
                    <title>{`${p.label}: ${valueFormatter(p.value)}`}</title>
                  </g>
                ))}
              </svg>
            </div>

            <div className="flex justify-between gap-1 text-[11px] font-semibold text-muted-foreground pt-1">
              {points.map((p) => (
                <span key={p.label} className="truncate text-center">
                  {p.label}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

type DonutChartProps = {
  title: string;
  description: string;
  points: ChartPoint[];
  colors?: string[];
  totalFormatter?: (val: number) => string;
};

const DEFAULT_DONUT_COLORS = [
  "#0F172A", // Dark ink
  "#F59E0B", // Amber
  "#10B981", // Emerald/Mint
  "#6366F1", // Indigo
  "#EC4899", // Pink
  "#8B5CF6", // Purple
  "#3B82F6", // Blue
  "#64748B", // Slate
];

export function DonutChart({
  title,
  description,
  points,
  colors = DEFAULT_DONUT_COLORS,
  totalFormatter = (v) => v.toLocaleString(),
}: DonutChartProps) {
  const total = points.reduce((sum, p) => sum + p.value, 0);
  let cumulativePercent = 0;

  const gradient = points
    .map((p, i) => {
      const start = total ? (cumulativePercent / total) * 100 : 0;
      cumulativePercent += p.value;
      const end = total ? (cumulativePercent / total) * 100 : 0;
      return `${colors[i % colors.length]} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardHeader>
        <CardTitle className="text-base font-bold">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {points.length === 0 || total === 0 ? (
          <div className="flex h-44 items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
            No category distribution available.
          </div>
        ) : (
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-around py-2">
            <div
              className="relative flex h-36 w-36 shrink-0 items-center justify-center rounded-full shadow-inner"
              style={{ background: `conic-gradient(${gradient})` }}
            >
              <div className="flex h-24 w-24 flex-col items-center justify-center rounded-full bg-card p-2 text-center shadow-md">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Total</span>
                <span className="text-xs font-black text-foreground">{totalFormatter(total)}</span>
              </div>
            </div>

            <div className="w-full space-y-2.5">
              {points.map((p, i) => {
                const percentage = total > 0 ? ((p.value / total) * 100).toFixed(1) : "0";
                return (
                  <div key={p.label} className="flex items-center justify-between gap-3 text-xs font-semibold">
                    <div className="flex items-center gap-2 min-w-0 truncate">
                      <span
                        className="h-3 w-3 shrink-0 rounded-full shadow-sm"
                        style={{ backgroundColor: colors[i % colors.length] }}
                      />
                      <span className="truncate text-foreground">{p.label}</span>
                    </div>
                    <div className="flex items-center gap-2 whitespace-nowrap text-muted-foreground">
                      <span className="text-foreground">{totalFormatter(p.value)}</span>
                      <span className="rounded-md bg-secondary/80 px-1.5 py-0.5 text-[10px] text-secondary-foreground font-bold">
                        {percentage}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
