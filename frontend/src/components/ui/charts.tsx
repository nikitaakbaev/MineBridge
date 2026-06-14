import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { MetricsSample } from "../../lib/types";

type SeriesKey = keyof MetricsSample;

type AreaSpec = {
  key: SeriesKey;
  label: string;
  color: string;
};

const axisColor = "#64748b";
const gridColor = "rgba(148, 163, 184, 0.12)";

function tooltipStyle() {
  return {
    background: "rgba(8, 17, 31, 0.94)",
    border: "1px solid rgba(96, 165, 250, 0.35)",
    borderRadius: 12,
    color: "#e8eef8"
  } as const;
}

type MetricAreaProps = {
  data: MetricsSample[];
  series: AreaSpec[];
  height?: number;
  unit?: string;
  domainMax?: number;
};

export function MetricArea({ data, series, height = 220, unit, domainMax }: MetricAreaProps) {
  return (
    <div className="chart" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <defs>
            {series.map((spec) => (
              <linearGradient key={spec.key} id={`grad-${spec.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={spec.color} stopOpacity={0.5} />
                <stop offset="100%" stopColor={spec.color} stopOpacity={0.02} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke={gridColor} vertical={false} />
          <XAxis dataKey="time" stroke={axisColor} fontSize={11} tickLine={false} minTickGap={40} />
          <YAxis
            stroke={axisColor}
            fontSize={11}
            tickLine={false}
            width={46}
            domain={domainMax ? [0, domainMax] : [0, "auto"]}
            unit={unit}
          />
          <Tooltip contentStyle={tooltipStyle()} labelStyle={{ color: "#94a3b8" }} />
          {series.map((spec) => (
            <Area
              key={spec.key}
              type="monotone"
              dataKey={spec.key}
              name={spec.label}
              stroke={spec.color}
              strokeWidth={2}
              fill={`url(#grad-${spec.key})`}
              isAnimationActive={false}
              dot={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

type GaugeProps = {
  value: number;
  max?: number;
  label: string;
  unit?: string;
  color?: string;
};

export function Gauge({ value, max = 100, label, unit = "%", color = "#60a5fa" }: GaugeProps) {
  const clamped = Math.max(0, Math.min(value, max));
  const data = [{ name: label, value: clamped, fill: color }];
  return (
    <div className="gauge">
      <ResponsiveContainer width="100%" height={150}>
        <RadialBarChart
          innerRadius="68%"
          outerRadius="100%"
          data={data}
          startAngle={220}
          endAngle={-40}
        >
          <PolarAngleAxis type="number" domain={[0, max]} tick={false} />
          <RadialBar dataKey="value" cornerRadius={12} background={{ fill: "rgba(148,163,184,0.12)" }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="gauge-readout">
        <strong>
          {Math.round(value)}
          <small>{unit}</small>
        </strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

type SparklineProps = {
  data: MetricsSample[];
  dataKey: SeriesKey;
  color?: string;
};

export function Sparkline({ data, dataKey, color = "#60a5fa" }: SparklineProps) {
  return (
    <ResponsiveContainer width="100%" height={44}>
      <LineChart data={data} margin={{ top: 4, right: 2, bottom: 0, left: 2 }}>
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
