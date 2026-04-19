import { api } from "@/lib/api";
import { parseFilters, type RawSearchParams } from "@/lib/filters";
import { KpiCard } from "@/components/kpi-card";
import { TabFilters } from "@/components/filters/tab-filters";
import { BenchmarksAccordion } from "@/components/benchmarks-accordion";
import { SessionLoadByAge } from "@/components/charts/session-load-by-age";
import { WeightedScatter } from "@/components/charts/weighted-scatter";

export default async function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const filters = parseFilters(await searchParams);
  const [options, kpis, ageStats, loadByAge, scatter] = await Promise.all([
    api.filterOptions(),
    api.overviewKpis(filters),
    api.ageStats(filters),
    api.sessionLoadByAge(filters),
    api.weightedScatter(filters),
  ]);

  return (
    <div className="flex flex-col gap-5">
      <TabFilters options={options} />

      {/* KPIs */}
      <section className="grid grid-cols-1 md:grid-cols-4" style={{ gap: 16 }}>
        <KpiCard label="Sessions"           value={kpis.sessions.toLocaleString()} />
        <KpiCard label="Unique Athletes"    value={kpis.athletes.toLocaleString()} />
        <KpiCard label="Avg Session Load"   value={kpis.avg_session_load.toFixed(1)} />
        <KpiCard label="Avg Total Distance" value={kpis.avg_total_distance_m.toFixed(0)} unit="m" />
      </section>

      {/* Benchmarks — accordion of 4 tables + slide-in chart drawer */}
      <section className="flex flex-col gap-3">
        <h2 className="pd-h2">Benchmarks</h2>
        <BenchmarksAccordion
          metrics={ageStats.metrics}
          tables={ageStats.tables}
          boxRows={loadByAge}
        />
      </section>

      {/* Overview charts */}
      <section className="grid grid-cols-1 lg:grid-cols-2" style={{ gap: 16 }}>
        <SessionLoadByAge data={loadByAge} />
        <WeightedScatter
          data={scatter.map((p) => ({
            athlete_id: p.athlete_id,
            sport: p.sport,
            gender: p.gender,
            weighted_session_load: p.weighted_session_load,
            weighted_max_speed: p.weighted_max_speed,
            sessions: p.sessions,
          }))}
        />
      </section>
    </div>
  );
}
