import type { ReactNode } from "react";

import type { MetricsSample } from "../../lib/types";
import { Sparkline } from "./charts";

type StatTileProps = {
  icon: ReactNode;
  label: string;
  value: string;
  hint?: string;
  accent?: string;
  data?: MetricsSample[];
  dataKey?: keyof MetricsSample;
};

export function StatTile({ icon, label, value, hint, accent = "#60a5fa", data, dataKey }: StatTileProps) {
  return (
    <div className="stat-tile">
      <div className="stat-tile-head">
        <span className="stat-icon" style={{ color: accent }}>
          {icon}
        </span>
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value">{value}</div>
      {hint && <div className="stat-hint">{hint}</div>}
      {data && dataKey && data.length > 1 && (
        <div className="stat-spark">
          <Sparkline data={data} dataKey={dataKey} color={accent} />
        </div>
      )}
    </div>
  );
}
