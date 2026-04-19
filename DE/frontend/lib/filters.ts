import type { SessionFilters } from "./api";

export type RawSearchParams = Record<string, string | string[] | undefined>;

function asNumber(v: string | string[] | undefined): number | undefined {
  const s = Array.isArray(v) ? v[0] : v;
  if (!s) return undefined;
  const n = Number(s);
  return Number.isFinite(n) ? n : undefined;
}

function asString(v: string | string[] | undefined): string | undefined {
  const s = Array.isArray(v) ? v[0] : v;
  return s || undefined;
}

function asArray(v: string | string[] | undefined): string[] | undefined {
  if (!v) return undefined;
  if (Array.isArray(v)) return v;
  return v.split(",").filter(Boolean);
}

export function parseFilters(params: RawSearchParams): SessionFilters {
  const ds = asString(params.data_source);
  return {
    gender: asString(params.gender),
    sports: asArray(params.sports),
    divisions: asArray(params.divisions),
    age_min: asNumber(params.age_min),
    age_max: asNumber(params.age_max),
    min_minutes: asNumber(params.min_minutes) ?? 70,
    data_source:
      ds === "sample" || ds === "synthetic" || ds === "all" ? ds : "all",
  };
}
