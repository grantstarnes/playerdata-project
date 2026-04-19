import type { AthleteDetail } from "@/lib/api";
import { PercentileRadar } from "@/components/athlete/percentile-radar";
import { SessionHistoryBars } from "@/components/athlete/session-history-bars";

function prettifySport(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function initials(sport: string, id: number) {
  return (
    sport
      .split("_")
      .map((w) => w[0]?.toUpperCase() ?? "")
      .join("")
      .slice(0, 2) || String(id).slice(-2)
  );
}

function pctTier(p: number) {
  if (p >= 90) return `Top ${Math.max(1, 100 - Math.round(p))}%`;
  if (p >= 75) return `Top ${Math.round(100 - p)}%`;
  if (p >= 50) return "Above cohort mean";
  return `${Math.round(p)}th pctile`;
}

export function AthleteDrilldownPanel({
  detail,
}: {
  detail: AthleteDetail | null;
}) {
  if (!detail) {
    return (
      <div className="pd-card flex items-center justify-center" style={{ minHeight: 560 }}>
        <p style={{ color: "var(--fg-3)", fontSize: 13 }}>
          Select an athlete from the roster to see their drilldown.
        </p>
      </div>
    );
  }

  // Pull percentiles into 6-axis radar data (axes without data → null → placeholder dot)
  const p = detail.percentiles;
  const radar = [
    { axis: "Distance",     value: p.total_dist_perc_rank   ?? null },
    { axis: "Max Speed",    value: p.max_speed_perc_rank    ?? null },
    { axis: "Session Load", value: p.session_load_perc_rank ?? null },
    { axis: "Accel",        value: p.accel_perc_rank        ?? null },
    { axis: "Decel",        value: p.decel_perc_rank        ?? null },
    { axis: "Sprint",       value: p.sprint_perc_rank       ?? null },
  ];

  const s = detail.stats;
  const totalDistance = s.total_distance_m?.max ?? 0;
  const maxSpeed      = s.max_speed_kph?.max   ?? 0;
  const sessionLoad   = s.session_load?.avg    ?? 0;

  return (
    <div className="flex flex-col" style={{ gap: 16 }}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="pd-h1">Athlete Drilldown</h1>
          <p
            style={{
              color: "var(--fg-3)",
              fontSize: 13,
              marginTop: 4,
              fontFamily: "var(--font-mono)",
            }}
          >
            · ID {detail.athlete_id} · {prettifySport(detail.sport)} {detail.gender[0].toUpperCase()} · {detail.division.toUpperCase()} · Age {detail.age ?? "—"}
          </p>
        </div>
        <span className="pd-badge pd-badge--live" style={{ letterSpacing: "0.06em" }}>
          TRACKED
        </span>
      </div>

      {/* Main layout: radar left (full height), KPIs + session history on right */}
      <section
        className="grid"
        style={{ gap: 16, gridTemplateColumns: "320px 1fr", alignItems: "stretch" }}
      >
        {/* Radar card — spans both rows on the right */}
        <div className="pd-card" style={{ padding: 18 }}>
          <div className="flex items-center gap-3" style={{ marginBottom: 10 }}>
            <div
              className="flex items-center justify-center shrink-0"
              style={{
                width: 44,
                height: 44,
                borderRadius: "50%",
                background: "var(--pd-green)",
                color: "var(--pd-black)",
                fontFamily: "var(--font-display)",
                fontWeight: 800,
                fontSize: 16,
              }}
            >
              {initials(detail.sport, detail.athlete_id)}
            </div>
            <div>
              <div className="pd-h3" style={{ marginBottom: 0 }}>
                #{detail.athlete_id}
              </div>
              <div style={{ fontSize: 11, color: "var(--fg-3)", fontFamily: "var(--font-mono)" }}>
                #{detail.athlete_id} · POS
              </div>
            </div>
          </div>
          <div
            className="pd-label-caps"
            style={{ fontSize: 10, marginBottom: 4 }}
          >
            Percentile Radar · vs Age Cohort
          </div>
          <PercentileRadar values={radar} />

          <div className="flex flex-col" style={{ gap: 6, marginTop: 10 }}>
            {radar
              .filter((v) => v.value !== null)
              .map((v) => (
                <PercentileBar key={v.axis} label={v.axis} pct={v.value as number} />
              ))}
          </div>
        </div>

        {/* Right column: KPI row on top, Last 10 Sessions below */}
        <div className="flex flex-col" style={{ gap: 16, minWidth: 0 }}>
          <div
            className="grid"
            style={{ gap: 16, gridTemplateColumns: "1fr 1fr 1fr" }}
          >
            <DrillKpi
              label="Total Distance"
              value={totalDistance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              unit=" m"
              caption="Session · Session Date"
              pctBadge={p.total_dist_perc_rank}
            />
            <DrillKpi
              label="Max Speed"
              value={maxSpeed.toFixed(1)}
              unit=" km/h"
              caption="PB · Session Date"
              pctBadge={p.max_speed_perc_rank}
            />
            <DrillKpi
              label="Session Load"
              value={sessionLoad.toFixed(0)}
              caption="Avg across sessions"
              pctBadge={p.session_load_perc_rank}
            />
          </div>

          <div className="pd-card flex-1" style={{ padding: 20 }}>
            <h3 className="pd-h3">Last 10 Sessions</h3>
            <p style={{ color: "var(--fg-3)", fontSize: 12, marginBottom: 14 }}>
              Session load · total distance · max speed
            </p>
            <SessionHistoryBars sessions={detail.timeline} />
          </div>
        </div>
      </section>
    </div>
  );
}

function DrillKpi({
  label,
  value,
  unit,
  caption,
  pctBadge,
}: {
  label: string;
  value: string;
  unit?: string;
  caption: string;
  pctBadge?: number;
}) {
  return (
    <div className="pd-card" style={{ padding: 18 }}>
      <div className="pd-label-caps">{label}</div>
      <div className="pd-kpi" style={{ fontSize: 32, marginTop: 6 }}>
        {value}
        {unit && <span className="pd-kpi-unit">{unit}</span>}
      </div>
      <div style={{ fontSize: 12, color: "var(--fg-3)", marginTop: 4 }}>
        {caption}
      </div>
      {typeof pctBadge === "number" && (
        <span
          className="pd-badge pd-badge--success"
          style={{ marginTop: 8 }}
        >
          {pctTier(pctBadge)}
        </span>
      )}
    </div>
  );
}

function PercentileBar({ label, pct }: { label: string; pct: number }) {
  return (
    <div>
      <div
        className="flex items-baseline justify-between"
        style={{ fontSize: 11 }}
      >
        <span style={{ color: "var(--fg-2)", fontWeight: 500 }}>{label}</span>
        <span
          style={{
            fontWeight: 700,
            fontFamily: "var(--font-mono)",
            color: "var(--fg-1)",
          }}
        >
          P{Math.round(pct)}
        </span>
      </div>
      <div
        style={{
          marginTop: 3,
          height: 6,
          borderRadius: 999,
          background: "var(--pd-ink-100)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(100, Math.max(0, pct))}%`,
            height: "100%",
            background: "var(--pd-green)",
            transition: "width 200ms",
          }}
        />
      </div>
    </div>
  );
}
