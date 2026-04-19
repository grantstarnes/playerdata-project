"use client";

import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Label,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = {
  age: number;
  count: number;
  mean: number;
  sd: number;
  top10: number;
  bottom10: number;
};

export function AgeBar({ data, title }: { data: Row[]; title: string }) {
  if (data.length === 0) {
    return (
      <p style={{ color: "var(--fg-3)", fontSize: 13 }}>
        Not enough data for this metric at current filters.
      </p>
    );
  }
  return (
    <div>
      <h3 className="pd-h3" style={{ marginBottom: 4 }}>{title} by Age Group</h3>
      <p style={{ color: "var(--fg-3)", fontSize: 12, marginBottom: 14 }}>
        Mean per age (bar), with top 10 (p90) marker
      </p>
      <div style={{ height: 480 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 28, right: 24, bottom: 42, left: 12 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" vertical={false} />
            <XAxis dataKey="age" stroke="var(--fg-3)" fontSize={11}>
              <Label
                value="Athlete relative age"
                position="insideBottom"
                offset={-28}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis stroke="var(--fg-3)" fontSize={11} width={60}>
              <Label
                value={title}
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
              formatter={(v) => Number(v).toFixed(2)}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, top: -4 }}
            />
            <Bar dataKey="mean" name="Mean" fill="var(--pd-green)" radius={[4, 4, 0, 0]} isAnimationActive={false}>
              {data.map((_, i) => <Cell key={i} />)}
            </Bar>
            <Line
              type="monotone"
              dataKey="top10"
              name="Top 10 (p90)"
              stroke="var(--chart-3)"
              strokeWidth={2}
              dot={{ r: 3 }}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
