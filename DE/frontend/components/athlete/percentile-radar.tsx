/**
 * Hexagonal percentile radar — 6 axes (Distance, Max Speed, Session Load,
 * Accel, Decel, Sprint). Values are 0–100 percentiles; axes without data
 * fall back to 50 (visually centered) with a dashed outline.
 */
export function PercentileRadar({
  values,
}: {
  values: Array<{ axis: string; value: number | null }>;
}) {
  const W = 280;
  const H = 220;
  const cx = W / 2;
  const cy = H / 2 + 4;
  const R = 80;

  const n = values.length;
  const pt = (i: number, r: number) => {
    const a = -Math.PI / 2 + i * ((2 * Math.PI) / n);
    return [cx + Math.cos(a) * r, cy + Math.sin(a) * r] as [number, number];
  };

  const polyPts = values
    .map((v, i) => pt(i, (R * (v.value ?? 50)) / 100).join(","))
    .join(" ");

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
      {/* concentric hexagonal grid */}
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon
          key={f}
          points={values.map((_, i) => pt(i, R * f).join(",")).join(" ")}
          fill="none"
          stroke="var(--chart-grid)"
          strokeDasharray={f === 1 ? "" : "2 2"}
        />
      ))}

      {/* axis labels */}
      {values.map((v, i) => {
        const [tx, ty] = pt(i, R + 16);
        return (
          <text
            key={v.axis}
            x={tx}
            y={ty + 4}
            fontSize={11}
            fill="var(--fg-2)"
            textAnchor="middle"
          >
            {v.axis}
          </text>
        );
      })}

      {/* filled polygon */}
      <polygon
        points={polyPts}
        fill="var(--pd-green)"
        fillOpacity={0.22}
        stroke="var(--pd-green)"
        strokeWidth={2}
      />

      {/* dots per axis */}
      {values.map((v, i) => {
        const hasData = v.value !== null;
        const [px, py] = pt(i, (R * (v.value ?? 50)) / 100);
        return (
          <circle
            key={v.axis}
            cx={px}
            cy={py}
            r={4}
            fill={hasData ? "var(--pd-green)" : "var(--pd-ink-300)"}
          />
        );
      })}
    </svg>
  );
}
