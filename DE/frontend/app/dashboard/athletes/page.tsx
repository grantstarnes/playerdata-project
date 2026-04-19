import { api } from "@/lib/api";
import { parseFilters, type RawSearchParams } from "@/lib/filters";
import { TabFilters } from "@/components/filters/tab-filters";
import { AthleteListPanel } from "@/components/athlete/athlete-list-panel";
import { AthleteDrilldownPanel } from "@/components/athlete/athlete-drilldown-panel";
import { CohortScatter } from "@/components/athlete/cohort-scatter";
import { AthletesSplit } from "@/components/athlete/athletes-split";

export default async function AthletesPage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const params = await searchParams;
  const filters = parseFilters(params);
  const selectedIdParam = typeof params.id === "string" ? Number(params.id) : NaN;

  const [options, athletes] = await Promise.all([
    api.filterOptions(),
    api.listAthletes(filters),
  ]);

  const activeId = Number.isFinite(selectedIdParam)
    ? selectedIdParam
    : athletes[0]?.athlete_id ?? null;

  const [detail, cohort] = activeId !== null
    ? await Promise.all([
        api.athleteDetail(activeId, filters).catch(() => null),
        api.athleteCohort(activeId, filters).catch(() => null),
      ])
    : [null, null];

  return (
    <div className="flex flex-col gap-5">
      <TabFilters options={options} />

      <AthletesSplit
        left={<AthleteListPanel athletes={athletes} activeId={activeId} />}
        right={
          <>
            <AthleteDrilldownPanel detail={detail} />
            {cohort && detail && (
              <CohortScatter
                peers={cohort.peers}
                activeAthleteId={cohort.athlete_id}
                age={cohort.age}
              />
            )}
          </>
        }
      />
    </div>
  );
}
