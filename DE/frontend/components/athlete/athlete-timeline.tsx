"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = Record<string, number | null>;

export function AthleteTimeline({ data }: { data: Row[] }) {
  const rows = data.map((r, i) => ({ ...r, i: i + 1 }));
  return (
    <div style={{ height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey="i" stroke="var(--fg-3)" fontSize={11} />
          <YAxis yAxisId="left" stroke="var(--fg-3)" fontSize={11} />
          <YAxis yAxisId="right" orientation="right" stroke="var(--fg-3)" fontSize={11} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid var(--pd-ink-100)",
              borderRadius: 10,
              fontSize: 12,
              boxShadow: "var(--shadow-sm)",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            yAxisId="left"
            dataKey="session_load"
            name="Session Load"
            stroke="var(--chart-2)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="left"
            dataKey="total_distance_m"
            name="Total Distance (m)"
            stroke="var(--chart-3)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="right"
            dataKey="max_speed_kph"
            name="Max Speed (kph)"
            stroke="var(--chart-4)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
