type SparklineProps = {
  values: number[];
  color?: string;
  height?: number;
  domainMin?: number;
  domainMax?: number;
};

/**
 * Lightweight inline-SVG sparkline.
 *
 * Avoids pulling recharts/d3 into the home screen. Picks min/max from data
 * unless ``domainMin`` / ``domainMax`` are provided. Empty / single-point
 * series degrade to a flat baseline.
 */
export function Sparkline({
  values,
  color = "#60a5fa",
  height = 36,
  domainMin,
  domainMax
}: SparklineProps) {
  const series = values.length === 0 ? [0, 0] : values;
  const width = Math.max(60, series.length * 4);

  const min = domainMin ?? Math.min(...series);
  const max = domainMax ?? Math.max(...series);
  const span = Math.max(max - min, 1);

  const stepX = series.length > 1 ? width / (series.length - 1) : 0;
  const points = series
    .map((value, idx) => {
      const x = idx * stepX;
      const y = height - ((value - min) / span) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const fillPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      role="presentation"
      aria-hidden="true"
    >
      <polygon points={fillPoints} fill={color} fillOpacity="0.16" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}
