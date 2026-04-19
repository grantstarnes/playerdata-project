type Row = {
  age: number;
  count: number;
  mean: number;
  sd: number;
  top10: number;
  bottom10: number;
};

const METRIC_META: Record<string, { title: string; unit: string; integer?: boolean }> = {
  total_distance_m:  { title: "Total Distance",  unit: "(m)" },
  max_speed_kph:     { title: "Max Speed",       unit: "(kph)" },
  session_load:      { title: "Session Load",    unit: "" },
  sprint_events:     { title: "Sprint Events",   unit: "", integer: true },
};

function fmt(v: number, integer = false): string {
  if (integer && Number.isInteger(v)) return v.toLocaleString();
  if (Number.isInteger(v)) return v.toLocaleString();
  return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function AgeStatsTable({
  metric,
  rows,
  bare = false,
}: {
  metric: string;
  rows: Row[];
  /** When bare, skip the outer card + title — used inside accordion items. */
  bare?: boolean;
}) {
  const meta = METRIC_META[metric] ?? { title: metric, unit: "" };
  const label = `${meta.title}${meta.unit ? " " + meta.unit : ""}`;

  const table = (
    <div style={{ overflowX: "auto" }}>
      <table className="w-full" style={{ fontSize: 12.5, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "var(--pd-ink-50)" }}>
            {[
              "Athlete Relative Age",
              "Count",
              `Average ${label}`,
              `Standard Deviation ${label}`,
              `Top 10 ${label}`,
              `Bottom 10 ${label}`,
            ].map((h, i) => (
              <th
                key={h}
                className="pd-label-caps"
                style={{
                  textAlign: i === 0 ? "left" : "right",
                  padding: "10px 16px",
                  borderBottom: "1px solid var(--pd-ink-100)",
                  whiteSpace: "nowrap",
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={6}
                style={{ padding: "16px", textAlign: "center", color: "var(--fg-3)", fontSize: 13 }}
              >
                No age groups meet the filter (need ≥5 sessions per age).
              </td>
            </tr>
          ) : (
            rows.map((r) => (
              <tr key={r.age} style={{ borderBottom: "1px solid var(--pd-ink-100)" }}>
                <td style={{ padding: "8px 16px", fontWeight: 600, color: "var(--fg-1)", fontVariantNumeric: "tabular-nums" }}>
                  {r.age}
                </td>
                <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                  {r.count.toLocaleString()}
                </td>
                <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                  {fmt(r.mean, meta.integer)}
                </td>
                <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                  {fmt(r.sd, meta.integer)}
                </td>
                <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                  {fmt(r.top10, meta.integer)}
                </td>
                <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                  {fmt(r.bottom10, meta.integer)}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );

  if (bare) return table;

  return (
    <div className="pd-card" style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--pd-ink-100)" }}>
        <h3 className="pd-h3">{meta.title}</h3>
      </div>
      {table}
    </div>
  );
}
