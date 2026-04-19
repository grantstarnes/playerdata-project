"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Label,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { BoxStat } from "@/lib/api";
import { ChartCard } from "@/components/chart-card";

function prettifySport(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function SessionLoadBySport({ data }: { data: BoxStat[] }) {
  const rows = data.map((d) => ({ ...d, sport: prettifySport(d.sport) }));

  return (
    <ChartCard
      title="Session Load by Sport"
      subtitle="Median session load across filtered sessions"
    >
      <div style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 32 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" horizontal={false} />
            <XAxis type="number" stroke="var(--fg-3)" fontSize={11}>
              <Label
                value="Median session load"
                position="insideBottom"
                offset={-18}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis type="category" dataKey="sport" stroke="var(--fg-3)" fontSize={12} width={150} />
            <Tooltip
              cursor={{ fill: "rgba(56,216,48,0.08)" }}
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid var(--pd-ink-100)",
                borderRadius: 10,
                fontSize: 12,
                boxShadow: "var(--shadow-sm)",
              }}
              formatter={(v) => Number(v).toFixed(1)}
            />
            <Bar dataKey="median" name="Median" fill="var(--pd-green)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
