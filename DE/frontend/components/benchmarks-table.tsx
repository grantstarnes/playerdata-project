type Row = {
  bucket: string;
  n: number;
  avg_load: number;
  median_load: number;
  avg_distance_m: number;
  avg_max_speed_kph: number;
};

function prettify(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function BenchmarksTable({
  title,
  subtitle,
  rows,
  bucketLabel,
  prettifyBucket = true,
}: {
  title: string;
  subtitle?: string;
  rows: Row[];
  bucketLabel: string;
  prettifyBucket?: boolean;
}) {
  return (
    <div className="pd-card" style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--pd-ink-100)" }}>
        <h3 className="pd-h3">{title}</h3>
        {subtitle && <div style={{ color: "var(--fg-3)", fontSize: 12, marginTop: 2 }}>{subtitle}</div>}
      </div>
      <table className="w-full" style={{ fontSize: 12.5, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "var(--pd-ink-50)" }}>
            {[bucketLabel, "N", "Avg Load", "Median Load", "Avg Dist (m)", "Avg Max Speed (kph)"].map((h, i) => (
              <th
                key={h}
                className="pd-label-caps"
                style={{
                  textAlign: i === 0 ? "left" : "right",
                  padding: "8px 16px",
                  borderBottom: "1px solid var(--pd-ink-100)",
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.bucket} style={{ borderBottom: "1px solid var(--pd-ink-100)" }}>
              <td style={{ padding: "8px 16px", fontWeight: 600, color: "var(--fg-1)" }}>
                {prettifyBucket ? prettify(r.bucket) : r.bucket}
              </td>
              <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                {r.n.toLocaleString()}
              </td>
              <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                {r.avg_load.toFixed(1)}
              </td>
              <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                {r.median_load.toFixed(1)}
              </td>
              <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                {r.avg_distance_m.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </td>
              <td style={{ padding: "8px 16px", textAlign: "right", fontVariantNumeric: "tabular-nums", color: "var(--fg-2)" }}>
                {r.avg_max_speed_kph.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
