"use client";

import {
  Area,
  CartesianGrid,
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

export function AgeTrend({
  data,
  title,
  unit = "",
}: {
  data: Row[];
  title: string;
  unit?: string;
}) {
  if (data.length === 0) {
    return (
      <p style={{ color: "var(--fg-3)", fontSize: 13 }}>
        Not enough data for this metric at current filters.
      </p>
    );
  }

  // Prep data: compute mean ±1 SD band bounds + keep top10 / bottom10 for the dashed lines.
  // The band is drawn as a stacked Area trick — `_sd_lo` is invisible, `_sd_hi` is the
  // filled slice on top of it, width = 2 × SD.
  const rows = data.map((d) => ({
    age:      d.age,
    mean:     d.mean,
    top10:    d.top10,
    bottom10: d.bottom10,
    _sd_lo:   d.mean - d.sd,
    _sd_hi:   2 * d.sd,
  }));

  const numberFmt = (v: number) =>
    v.toLocaleString(undefined, { maximumFractionDigits: 2 });

  return (
    <div>
      <h3 className="pd-h3" style={{ marginBottom: 4 }}>{title} by Age Group</h3>
      <p style={{ color: "var(--fg-3)", fontSize: 12, marginBottom: 14 }}>
        Mean ±1 SD with 10/90 percentile markers
      </p>
      <div style={{ height: 480 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 28, right: 24, bottom: 42, left: 12 }}>
            <CartesianGrid strokeDasharray="0" stroke="var(--chart-grid)" vertical={false} />
            <XAxis dataKey="age" stroke="var(--fg-3)" fontSize={11}>
              <Label
                value="Athlete relative age"
                position="insideBottom"
                offset={-28}
                style={{ textAnchor: "middle", fontSize: 12, fill: "var(--fg-2)" }}
              />
            </XAxis>
            <YAxis
              stroke="var(--fg-3)"
              fontSize={11}
              tickFormatter={(v) => Number(v).toLocaleString()}
              width={68}
            >
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
              formatter={(v, name) => {
                if (name === "_sd_lo" || name === "_sd_hi") {
                  return null as unknown as [string, string];
                }
                return [numberFmt(Number(v)) + unit, String(name)];
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, top: -4 }}
              // @ts-expect-error Recharts 3 removed `payload` from Legend's typed Props but still honors it at runtime for static legends
              payload={[
                { value: "Mean (±1 SD)", type: "line", color: "var(--pd-green)" },
                { value: "90th pctile",  type: "line", color: "var(--chart-3)" },
                { value: "10th pctile",  type: "line", color: "var(--chart-4)" },
              ]}
            />

            {/* SD band — stacked Area trick */}
            <Area
              type="monotone"
              dataKey="_sd_lo"
              stackId="sdband"
              stroke="transparent"
              fill="transparent"
              isAnimationActive={false}
              legendType="none"
            />
            <Area
              type="monotone"
              dataKey="_sd_hi"
              stackId="sdband"
              stroke="transparent"
              fill="var(--pd-green)"
              fillOpacity={0.18}
              isAnimationActive={false}
              legendType="none"
            />

            {/* p90 — dashed magenta */}
            <Line
              type="monotone"
              dataKey="top10"
              name="90th pctile"
              stroke="var(--chart-3)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />

            {/* p10 — dashed purple */}
            <Line
              type="monotone"
              dataKey="bottom10"
              name="10th pctile"
              stroke="var(--chart-4)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
              legendType="none"
            />

            {/* Mean — solid green line + dots */}
            <Line
              type="monotone"
              dataKey="mean"
              name="Mean"
              stroke="var(--pd-green)"
              strokeWidth={2.5}
              dot={{ r: 3.5, fill: "var(--pd-green)" }}
              isAnimationActive={false}
              legendType="none"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
