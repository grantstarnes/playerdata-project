"use client";

import {
  CartesianGrid,
  Label,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
  Legend,
} from "recharts";

import { ChartCard } from "@/components/chart-card";

type Point = {
  athlete_id: number;
  sport: string;
  gender: string;
  weighted_session_load: number;
  weighted_max_speed: number;
  sessions: number;
};

const SPORT_COLORS: Record<string, string> = {
  association_football: "var(--chart-1)",
  american_football:    "var(--chart-2)",
  basketball:           "var(--chart-4)",
  lacrosse:             "var(--chart-5)",
};

function prettify(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function WeightedScatter({ data }: { data: Point[] }) {
  const sports = [...new Set(data.map((d) => d.sport))];
  const series = sports.map((s) => ({
    sport: s,
    color: SPORT_COLORS[s] ?? "var(--chart-6)",
    points: data.filter((d) => d.sport === s),
  }));

  return (
    <ChartCard
      title="Weighted Session Load vs Weighted Max Speed"
      subtitle="Per-athlete averages weighted by active minutes · bubble size = session count"
    >
      <div style={{ height: 400 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 28, right: 24, bottom: 44, left: 12 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" />
            <XAxis
              type="number"
              dataKey="weighted_session_load"
              name="Weighted Session Load"
              stroke="var(--fg-3)"
              fontSize={11}
              tickFormatter={(v) => Number(v).toLocaleString()}
            >
              <Label
                value="Weighted Session Load"
                position="insideBottom"
                offset={-30}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis
              type="number"
              dataKey="weighted_max_speed"
              name="Weighted Max Speed"
              stroke="var(--fg-3)"
              fontSize={11}
              width={60}
            >
              <Label
                value="Weighted Max Speed (kph)"
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </YAxis>
            <ZAxis type="number" dataKey="sessions" range={[25, 180]} name="Sessions" />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid var(--pd-ink-100)",
                borderRadius: 10,
                fontSize: 12,
                boxShadow: "var(--shadow-sm)",
              }}
              formatter={(v, name) => {
                if (name === "Sessions") return [String(v ?? ""), "Sessions"];
                return [typeof v === "number" ? v.toFixed(1) : String(v ?? ""), String(name)];
              }}
              labelFormatter={() => ""}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, top: -4 }}
              iconType="circle"
            />
            {series.map((s) => (
              <Scatter
                key={s.sport}
                name={prettify(s.sport)}
                data={s.points}
                fill={s.color}
                fillOpacity={0.6}
                stroke={s.color}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
