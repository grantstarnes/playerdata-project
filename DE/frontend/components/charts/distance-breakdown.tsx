"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Label,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/chart-card";

function prettifyBucket(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

type Row = {
  bucket: string;
  avg_total_distance_m: number;
  avg_hi_distance_m: number;
  avg_sprint_distance_m: number;
};

export function DistanceBreakdown({ data }: { data: Row[] }) {
  const rows = data.map((d) => ({ ...d, bucket: prettifyBucket(d.bucket) }));
  return (
    <ChartCard
      title="Distance Breakdown"
      subtitle="Mean total / high-intensity / sprint distance per sport"
    >
      <div style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 28, right: 24, bottom: 36, left: 12 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" vertical={false} />
            <XAxis dataKey="bucket" stroke="var(--fg-3)" fontSize={11}>
              <Label
                value="Sport"
                position="insideBottom"
                offset={-22}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis stroke="var(--fg-3)" fontSize={11} width={60}>
              <Label
                value="Distance (m)"
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </YAxis>
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid var(--pd-ink-100)",
                borderRadius: 10,
                fontSize: 12,
                boxShadow: "var(--shadow-sm)",
              }}
              formatter={(v: number) => v.toFixed(0) + " m"}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, top: -4 }}
              iconType="circle"
            />
            <Bar dataKey="avg_total_distance_m" name="Total"          fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="avg_hi_distance_m"    name="High-intensity" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="avg_sprint_distance_m" name="Sprint"        fill="var(--chart-4)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
