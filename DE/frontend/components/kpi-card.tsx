export function KpiCard({
  label,
  value,
  unit,
  delta,
  deltaDir = "flat",
}: {
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  deltaDir?: "up" | "down" | "flat";
}) {
  const deltaColor =
    deltaDir === "up"   ? "var(--pd-green-700)" :
    deltaDir === "down" ? "#9B1C24" :
                          "var(--fg-3)";
  const arrow = deltaDir === "up" ? "↑" : deltaDir === "down" ? "↓" : "";
  return (
    <div className="pd-card" style={{ padding: 18 }}>
      <div className="pd-label-caps">{label}</div>
      <div className="pd-kpi" style={{ marginTop: 6, fontSize: 36 }}>
        {value}
        {unit && <span className="pd-kpi-unit">{unit}</span>}
      </div>
      {delta ? (
        <div style={{ marginTop: 6, fontSize: 12, fontWeight: 600, color: deltaColor }}>
          {arrow} {delta}
        </div>
      ) : (
        <div style={{ marginTop: 6, fontSize: 12, color: "var(--fg-3)" }}>&nbsp;</div>
      )}
    </div>
  );
}
