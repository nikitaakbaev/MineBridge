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
import { readCssVariable } from "../../lib/theme";

type SeriesKey = keyof MetricsSample;

type AreaSpec = {
  key: SeriesKey;
  label: string;
  color: string;
};

const axisColor = "#7f8994";
const gridColor = "rgba(231, 236, 241, 0.10)";

function tooltipStyle() {
  return {
    background: "#111418",
    border: `1px solid ${readCssVariable("--border-strong", "rgba(231, 236, 241, 0.18)")}`,
    borderRadius: 8,
    color: readCssVariable("--text", "#edf1f5")
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
          <Tooltip contentStyle={tooltipStyle()} labelStyle={{ color: axisColor }} />
          {series.map((spec) => (
            <Line
              key={spec.key}
              type="monotone"
              dataKey={spec.key}
              name={spec.label}
              stroke={spec.color}
              strokeWidth={2}
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

export function Gauge({ value, max = 100, label, unit = "%", color = "var(--accent)" }: GaugeProps) {
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
          <RadialBar dataKey="value" cornerRadius={8} background={{ fill: "rgba(231,236,241,0.10)" }} />
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

export function Sparkline({ data, dataKey, color = "var(--accent)" }: SparklineProps) {
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
