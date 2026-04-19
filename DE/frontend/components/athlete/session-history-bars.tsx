/**
 * Last N Sessions chart — 3 stacked rows of bars (Session Load / Total
 * Distance / Max Speed). Pure SVG, fixed dimensions, responsive width via
 * viewBox. Styled to match the mockup.
 */
type Session = {
  session_load?: number | null;
  total_distance_m?: number | null;
  max_speed_kph?: number | null;
};

export function SessionHistoryBars({ sessions }: { sessions: Session[] }) {
  if (sessions.length === 0) {
    return (
      <p style={{ color: "var(--fg-3)", fontSize: 13 }}>
        No sessions recorded for this athlete at current filters.
      </p>
    );
  }
  // Take last 10
  const last = sessions.slice(-10);
  const loads    = last.map((s) => Number(s.session_load     ?? 0));
  const dists    = last.map((s) => Number(s.total_distance_m ?? 0));
  const speeds   = last.map((s) => Number(s.max_speed_kph    ?? 0));

  const row = (
    title: string,
    vals: number[],
    color: string,
    unit: string,
    fmt: (v: number) => string,
  ) => {
    const max = Math.max(1, ...vals) * 1.05;
    const W = 720, H = 100;
    const P = { t: 20, r: 16, b: 18, l: 12 };
    const bw = (W - P.l - P.r) / Math.max(vals.length, 10);

    return (
      <svg
        width="100%"
        viewBox={`0 0 ${W} ${H}`}
        style={{ display: "block" }}
        preserveAspectRatio="xMidYMid meet"
      >
        <text x={P.l} y={12} fontSize={12} fontWeight={600} fill="var(--fg-1)">
          {title}
        </text>
        <text
          x={W - P.r}
          y={12}
          fontSize={11}
          fill="var(--fg-3)"
          textAnchor="end"
        >
          max {fmt(Math.max(0, ...vals))}{unit}
        </text>
        {vals.map((v, i) => {
          const h = ((H - P.t - P.b) * v) / max;
          const barW = Math.min(22, bw * 0.38);
          return (
            <g key={i}>
              <rect
                x={P.l + bw * i + (bw - barW) / 2}
                y={H - P.b - h}
                width={barW}
                height={h}
                fill={color}
                rx={3}
              />
              <text
                x={P.l + bw * i + bw / 2}
                y={H - 4}
                fontSize={10}
                fill="var(--fg-3)"
                textAnchor="middle"
              >
                S{i + 1}
              </text>
            </g>
          );
        })}
      </svg>
    );
  };

  const fmtInt = (v: number) => Math.round(v).toLocaleString();
  const fmtOne = (v: number) => v.toFixed(1);

  return (
    <div className="flex flex-col" style={{ gap: 6 }}>
      {row("Session Load",      loads,  "var(--chart-2)", "",      fmtInt)}
      {row("Total Distance (m)", dists,  "var(--chart-1)", "",      fmtInt)}
      {row("Max Speed (km/h)",   speeds, "var(--chart-4)", "",      fmtOne)}
    </div>
  );
}
