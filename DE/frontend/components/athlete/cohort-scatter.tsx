"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Label,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Peer = {
  athlete_id: number;
  accel: number;
  decel: number;
  max_speed: number;
  distance: number;
  sessions: number;
};

const METRICS = [
  { id: "distance",  label: "Distance (m)" },
  { id: "max_speed", label: "Max Speed (kph)" },
  { id: "accel",     label: "Accel events" },
  { id: "decel",     label: "Decel events" },
] as const;

type MetricId = (typeof METRICS)[number]["id"];

export function CohortScatter({
  peers,
  activeAthleteId,
  age,
}: {
  peers: Peer[];
  activeAthleteId: number;
  age: number;
}) {
  const [x, setX] = useState<MetricId>("max_speed");
  const [y, setY] = useState<MetricId>("distance");

  const active = peers.filter((p) => p.athlete_id === activeAthleteId);
  const others = peers.filter((p) => p.athlete_id !== activeAthleteId);

  const xLabel = METRICS.find((m) => m.id === x)?.label ?? x;
  const yLabel = METRICS.find((m) => m.id === y)?.label ?? y;

  const fmt = (v: number) =>
    v.toLocaleString(undefined, { maximumFractionDigits: 2 });

  return (
    <div className="pd-card" style={{ padding: 20 }}>
      <div className="flex items-start justify-between" style={{ gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
        <div>
          <h3 className="pd-h3">Cohort Scatter · Age {age}</h3>
          <p style={{ color: "var(--fg-3)", fontSize: 12, marginTop: 2 }}>
            {peers.length} athletes in the same age group · selected athlete highlighted
          </p>
        </div>

        <div className="flex flex-col" style={{ gap: 6 }}>
          <AxisSelect label="X" current={x} onChange={setX} except={y} />
          <AxisSelect label="Y" current={y} onChange={setY} except={x} />
        </div>
      </div>

      <div style={{ height: 360 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 16, right: 24, bottom: 44, left: 12 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" />
            <XAxis
              type="number"
              dataKey={x}
              stroke="var(--fg-3)"
              fontSize={11}
              tickFormatter={(v) => Number(v).toLocaleString()}
            >
              <Label
                value={xLabel}
                position="insideBottom"
                offset={-30}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis
              type="number"
              dataKey={y}
              stroke="var(--fg-3)"
              fontSize={11}
              width={60}
              tickFormatter={(v) => Number(v).toLocaleString()}
            >
              <Label
                value={yLabel}
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </YAxis>
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid var(--pd-ink-100)",
                borderRadius: 10,
                fontSize: 12,
                boxShadow: "var(--shadow-sm)",
              }}
              formatter={(v, name) => [fmt(Number(v)), String(name)]}
              labelFormatter={() => ""}
            />
            <Scatter
              name="Cohort"
              data={others}
              fill="var(--pd-ink-300)"
              fillOpacity={0.55}
            />
            <Scatter
              name="Selected"
              data={active}
              fill="var(--pd-green)"
              stroke="var(--pd-green-700)"
              strokeWidth={2}
              r={10}
              shape="circle"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AxisSelect({
  label,
  current,
  onChange,
  except,
}: {
  label: string;
  current: MetricId;
  onChange: (m: MetricId) => void;
  except: MetricId;
}) {
  return (
    <div className="flex items-center" style={{ gap: 6 }}>
      <span className="pd-label-caps" style={{ width: 14 }}>{label}</span>
      <div className="flex" style={{ gap: 4, flexWrap: "wrap" }}>
        {METRICS.map((m) => {
          const disabled = m.id === except;
          const active = m.id === current;
          return (
            <button
              key={m.id}
              onClick={() => onChange(m.id)}
              disabled={disabled}
              style={{
                padding: "3px 8px",
                fontSize: 11,
                fontWeight: 600,
                border: active ? "1px solid var(--pd-green)" : "1px solid var(--pd-ink-200)",
                background: active ? "var(--pd-green-50)" : "var(--pd-surface)",
                color: disabled ? "var(--fg-4)" : active ? "var(--pd-green-700)" : "var(--fg-2)",
                borderRadius: 999,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.5 : 1,
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
