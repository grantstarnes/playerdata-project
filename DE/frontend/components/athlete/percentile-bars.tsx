"use client";

type PctMap = Record<string, number>;

const LABELS: Record<string, string> = {
  total_dist_perc_rank:   "Total Distance",
  max_speed_perc_rank:    "Max Speed",
  session_load_perc_rank: "Session Load",
};

function tier(p: number) {
  if (p >= 90) return { label: "Elite (top 10%)", color: "var(--pd-green-700)" };
  if (p >= 75) return { label: "Top quartile",    color: "var(--pd-green-600)" };
  if (p >= 50) return { label: "Above average",   color: "var(--pd-green)" };
  if (p >= 25) return { label: "Below average",   color: "var(--chart-5)" };
  return { label: "Bottom quartile", color: "var(--pd-error)" };
}

export function PercentileBars({ data }: { data: PctMap }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return (
      <p style={{ fontSize: 13, color: "var(--fg-3)" }}>
        Not enough peers in age group to compute ranks.
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-4" style={{ margin: 0, padding: 0, listStyle: "none" }}>
      {entries.map(([k, v]) => {
        const t = tier(v);
        return (
          <li key={k}>
            <div className="flex items-baseline justify-between" style={{ fontSize: 12 }}>
              <span style={{ fontWeight: 600, color: "var(--fg-1)" }}>{LABELS[k] ?? k}</span>
              <span style={{ color: t.color, fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>
                {v.toFixed(1)} · {t.label}
              </span>
            </div>
            <div
              style={{
                marginTop: 6,
                position: "relative",
                height: 8,
                borderRadius: 999,
                background: "var(--pd-ink-100)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, v))}%`,
                  height: "100%",
                  background: t.color,
                  transition: "width 200ms",
                }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
