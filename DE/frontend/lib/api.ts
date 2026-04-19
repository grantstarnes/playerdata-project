/**
 * Typed client for the PlayerData FastAPI backend.
 *
 * Server components: uses Clerk's server-side auth() to fetch a session token.
 * Client components: import from lib/api-client.ts instead (uses useAuth()).
 */

import { auth } from "@clerk/nextjs/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type SessionFilters = {
  gender?: string;
  sports?: string[];
  divisions?: string[];
  age_min?: number;
  age_max?: number;
  min_minutes?: number;
  data_source?: "all" | "sample" | "synthetic";
};

function toQuery(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, String(x)));
    else sp.append(k, String(v));
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

async function bearer(): Promise<string> {
  const { getToken } = await auth();
  const token = await getToken();
  if (!token) throw new Error("Not signed in");
  return token;
}

async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const token = await bearer();
  const url = `${API_URL}${path}${params ? toQuery(params) : ""}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${body.slice(0, 120)}`);
  }
  return res.json() as Promise<T>;
}

async function apiPost<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const token = await bearer();
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`POST ${path} failed: ${res.status} ${body.slice(0, 120)}`);
  }
  return res.json() as Promise<TRes>;
}

// --- Types mirror the backend Pydantic models / JSON shapes ---

export type FilterOptions = {
  genders: string[];
  sports: string[];
  divisions: string[];
  age_min: number;
  age_max: number;
  total_sessions: number;
};

export type OverviewKpis = {
  sessions: number;
  athletes: number;
  avg_session_load: number;
  avg_total_distance_m: number;
  avg_max_speed_kph: number;
  avg_active_minutes: number;
};

export type BoxStat = {
  sport: string;
  n: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  mean: number;
};

export type VolumePoint = {
  active_minutes: number;
  session_load: number;
  total_distance_m: number;
  sport: string;
  athlete_id: number | null;
};

export type AthleteRow = {
  athlete_id: number;
  sport: string;
  gender: string;
  age: number | null;
  division: string;
  sessions: number;
};

export type AthleteDetail = AthleteRow & {
  session_count: number;
  stats: Record<string, { avg: number; max: number; min: number }>;
  percentiles: Record<string, number>;
  timeline: Array<Record<string, number | null>>;
};

export type ModelInfo = {
  id: string;
  label: string;
  tier: string;
  installed: boolean;
};

export type ChatResponse = {
  model: string;
  response: string;
  tool_calls: Array<{ name: string; args: Record<string, unknown>; result: unknown }>;
  fallback_reason?: string | null;
  note?: string | null;
};

// --- Endpoint wrappers ---

export const api = {
  health: () => apiGet<{ status: string; ollama: string }>("/health"),
  filterOptions: () => apiGet<FilterOptions>("/api/filters/options"),
  overviewKpis: (f: SessionFilters = {}) =>
    apiGet<OverviewKpis>("/api/overview/kpis", f as Record<string, unknown>),
  sessionLoadBySport: (f: SessionFilters = {}) =>
    apiGet<BoxStat[]>("/api/overview/session-load-by-sport", f as Record<string, unknown>),
  volumeVsIntensity: (f: SessionFilters = {}) =>
    apiGet<VolumePoint[]>("/api/overview/volume-vs-intensity", f as Record<string, unknown>),
  distanceBreakdown: (
    group_by: "athlete_sport" | "club_division" | "athlete_gender_marker" = "athlete_sport",
    f: SessionFilters = {},
  ) =>
    apiGet<Array<{
      bucket: string;
      avg_total_distance_m: number;
      avg_hi_distance_m: number;
      avg_sprint_distance_m: number;
    }>>("/api/overview/distance-breakdown", {
      group_by,
      ...f,
    } as Record<string, unknown>),
  listAthletes: (f: SessionFilters = {}, search?: string) =>
    apiGet<AthleteRow[]>("/api/athletes", { ...f, search } as Record<string, unknown>),
  athleteDetail: (id: number, f: SessionFilters = {}) =>
    apiGet<AthleteDetail>(`/api/athletes/${id}`, f as Record<string, unknown>),
  athleteCohort: (id: number, f: SessionFilters = {}) =>
    apiGet<{
      athlete_id: number;
      age: number;
      peers: Array<{
        athlete_id: number;
        accel: number;
        decel: number;
        max_speed: number;
        distance: number;
        sessions: number;
      }>;
    }>(`/api/athletes/${id}/cohort`, f as Record<string, unknown>),
  ageStats: (f: SessionFilters = {}) =>
    apiGet<{
      metrics: string[];
      tables: Record<string, Array<{
        age: number; count: number; mean: number; sd: number; top10: number; bottom10: number;
      }>>;
    }>("/api/overview/age-stats", f as Record<string, unknown>),
  sessionLoadByAge: (f: SessionFilters = {}) =>
    apiGet<Array<{ age: number; n: number; min: number; q1: number; median: number; q3: number; max: number; mean: number }>>(
      "/api/overview/session-load-by-age",
      f as Record<string, unknown>,
    ),
  weightedScatter: (f: SessionFilters = {}) =>
    apiGet<Array<{
      athlete_id: number; sport: string; gender: string; division: string; age: number | null;
      weighted_session_load: number; weighted_max_speed: number; sessions: number;
    }>>("/api/overview/weighted-scatter", f as Record<string, unknown>),
  benchmarkBreakdown: (
    by: "athlete_sport" | "club_division" | "athlete_gender_marker" | "athlete_relative_age",
    f: SessionFilters = {},
  ) =>
    apiGet<Array<{
      bucket: string; n: number;
      avg_load: number; q1_load: number; median_load: number; q3_load: number;
      avg_distance_m: number; avg_max_speed_kph: number;
      avg_accel_events: number; avg_decel_events: number;
    }>>("/api/benchmarks/breakdown", { by, ...f } as Record<string, unknown>),
  chatModels: () => apiGet<{ default: string; models: ModelInfo[] }>("/api/chat/models"),
  chatSession: () => apiGet<{ athlete_ctx: number | null; user_id: string }>("/api/chat/session"),
  chat: (
    message: string,
    model: string,
    athlete_ctx: number | null | undefined,
    history: Array<{ role: string; content: string }>,
  ) =>
    apiPost<
      { message: string; model: string; athlete_ctx?: number | null; history: Array<{ role: string; content: string }> },
      ChatResponse
    >("/api/chat", { message, model, athlete_ctx, history }),
};
