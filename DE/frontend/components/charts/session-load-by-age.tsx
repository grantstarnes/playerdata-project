"use client";

import { ChartCard } from "@/components/chart-card";

type Row = {
  age: number;
  n: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  mean: number;
};

export function SessionLoadByAge({ data, bare = false }: { data: Row[]; bare?: boolean }) {
  if (data.length === 0) {
    const msg = <p style={{ color: "var(--fg-3)", fontSize: 13 }}>No age groups meet the filter threshold (need ≥5 sessions per age).</p>;
    return bare ? msg : (
      <ChartCard title="Session Load by Relative Age" subtitle="Box plot">{msg}</ChartCard>
    );
  }

  const W = 620, H = 400;
  const P = { t: 30, r: 16, b: 70, l: 52 };
  const innerH = H - P.t - P.b;
  const innerW = W - P.l - P.r;

  const yMin = 0;
  const yMax = Math.max(...data.map((d) => d.max)) * 1.05;
  const y = (v: number) => P.t + innerH * (1 - (v - yMin) / (yMax - yMin));

  const bw = innerW / data.length;

  const yTicks = (() => {
    const step = Math.ceil(yMax / 5 / 100) * 100;
    const out: number[] = [];
    for (let v = 0; v <= yMax; v += step) out.push(v);
    return out;
  })();

  const svg = (
    <div style={{ height: 400 }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        {/* Y-axis gridlines + labels */}
        {yTicks.map((t) => (
          <g key={t}>
            <line
              x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)}
              stroke="var(--chart-grid)"
            />
            <text
              x={P.l - 8} y={y(t) + 4}
              fontSize={10} fill="var(--fg-3)" textAnchor="end"
            >
              {t}
            </text>
          </g>
        ))}

        {/* Boxes */}
        {data.map((d, i) => {
          const cx = P.l + bw * i + bw / 2;
          const w = Math.min(32, bw * 0.55);
          const color = "var(--pd-green)";
          return (
            <g key={d.age}>
              {/* whisker vertical */}
              <line x1={cx} x2={cx} y1={y(d.max)} y2={y(d.min)} stroke={color} strokeOpacity={0.5} />
              {/* whisker caps */}
              <line x1={cx - 6} x2={cx + 6} y1={y(d.max)} y2={y(d.max)} stroke={color} />
              <line x1={cx - 6} x2={cx + 6} y1={y(d.min)} y2={y(d.min)} stroke={color} />
              {/* box */}
              <rect
                x={cx - w / 2}
                y={y(d.q3)}
                width={w}
                height={y(d.q1) - y(d.q3)}
                fill={color}
                fillOpacity={0.18}
                stroke={color}
                rx={3}
              />
              {/* median */}
              <line x1={cx - w / 2} x2={cx + w / 2} y1={y(d.median)} y2={y(d.median)} stroke={color} strokeWidth={2} />
              {/* age tick */}
              <text
                x={cx}
                y={H - P.b + 14}
                fontSize={11}
                fill="var(--fg-2)"
                textAnchor="middle"
              >
                {d.age}
              </text>
              <text
                x={cx}
                y={H - P.b + 26}
                fontSize={10}
                fill="var(--fg-3)"
                textAnchor="middle"
              >
                n={d.n}
              </text>
            </g>
          );
        })}

        {/* X-axis label */}
        <text
          x={P.l + innerW / 2}
          y={H - 8}
          fontSize={12}
          fill="var(--fg-2)"
          textAnchor="middle"
        >
          Athlete relative age
        </text>

        {/* Y-axis label */}
        <text
          transform={`rotate(-90 14 ${P.t + innerH / 2})`}
          x={14} y={P.t + innerH / 2}
          fontSize={12}
          fill="var(--fg-2)"
          textAnchor="middle"
        >
          Session load
        </text>

        {/* Legend top-right */}
        <g transform={`translate(${W - P.r - 180}, ${P.t - 2})`}>
          <rect x={0} y={-12} width={180} height={22} fill="#fff" stroke="var(--pd-ink-100)" rx={6} />
          <rect x={8} y={-6} width={14} height={10} fill="var(--pd-green)" fillOpacity={0.3} stroke="var(--pd-green)" rx={2} />
          <line x1={12} x2={20} y1={-1} y2={-1} stroke="var(--pd-green)" strokeWidth={2} />
          <text x={28} y={2} fontSize={11} fill="var(--fg-2)">Q1–Q3 · median · whiskers</text>
        </g>
      </svg>
    </div>
  );

  if (bare) {
    return (
      <div>
        <h3 className="pd-h3" style={{ marginBottom: 4 }}>Session Load by Relative Age</h3>
        <p style={{ color: "var(--fg-3)", fontSize: 12, marginBottom: 14 }}>Box plot — Q1/median/Q3 + whiskers per age</p>
        {svg}
      </div>
    );
  }

  return (
    <ChartCard
      title="Session Load by Relative Age"
      subtitle="Box plot — Q1/median/Q3 + whiskers per age"
    >
      {svg}
    </ChartCard>
  );
}
