"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useEffect, useRef, useTransition } from "react";

import type { FilterOptions } from "@/lib/api";

const MIN_MIN_CHOICES = [60, 70, 80, 90, 100];
const DIVISIONS = ["di", "dii", "diii"];

// Keys that represent "filters" (persisted across sessions + carried between
// tabs). Excludes tab-specific keys like `id` or future per-tab state.
const FILTER_KEYS = new Set([
  "gender", "sports", "divisions",
  "age_min", "age_max",
  "min_minutes", "data_source",
]);
const STORAGE_KEY = "pd-filters";

function prettifySport(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function TabFilters({ options }: { options: FilterOptions }) {
  const router = useRouter();
  const pathname = usePathname();
  const current = useSearchParams();
  const [pending, startTransition] = useTransition();

  // ---- Persistence: save current filter params whenever they change,
  //      restore from localStorage on first mount if URL has no filters.
  const hydrated = useRef(false);
  useEffect(() => {
    if (hydrated.current) return;
    hydrated.current = true;

    const hasAnyFilter = Array.from(current.keys()).some((k) => FILTER_KEYS.has(k));
    if (!hasAnyFilter) {
      try {
        const saved = window.localStorage.getItem(STORAGE_KEY);
        if (saved) {
          startTransition(() => router.replace(`${pathname}?${saved}`, { scroll: false }));
        }
      } catch { /* localStorage may be blocked */ }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // Build a filter-only snapshot and save to localStorage.
    const snap = new URLSearchParams();
    current.forEach((v, k) => {
      if (FILTER_KEYS.has(k)) snap.append(k, v);
    });
    try {
      if (snap.toString()) window.localStorage.setItem(STORAGE_KEY, snap.toString());
      else window.localStorage.removeItem(STORAGE_KEY);
    } catch { /* ignore */ }
  }, [current]);

  function set(key: string, value: string | string[] | null) {
    const params = new URLSearchParams(current.toString());
    params.delete(key);
    if (Array.isArray(value)) value.forEach((v) => params.append(key, v));
    else if (value !== null && value !== "") params.set(key, value);
    startTransition(() => router.push(`${pathname}?${params.toString()}`, { scroll: false }));
  }

  function resetAll() {
    try { window.localStorage.removeItem(STORAGE_KEY); } catch {}
    const params = new URLSearchParams(current.toString());
    FILTER_KEYS.forEach((k) => params.delete(k));
    startTransition(() => router.push(`${pathname}?${params.toString()}`, { scroll: false }));
  }

  const dataSource = current.get("data_source") ?? "all";
  const gender = current.get("gender") ?? "all";
  const minMinutes = Number(current.get("min_minutes") ?? 70);
  const sports = current.getAll("sports");
  const divisions = current.getAll("divisions");

  return (
    <div
      className="pd-card"
      style={{ padding: "14px 18px", display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}
    >
      <FilterGroup label="Gender">
        <Chip active={gender === "all"} onClick={() => set("gender", null)}>All</Chip>
        {options.genders.map((g) => (
          <Chip key={g} active={gender === g} onClick={() => set("gender", g)}>
            {g[0].toUpperCase() + g.slice(1)}
          </Chip>
        ))}
      </FilterGroup>

      <FilterGroup label="Min active min">
        {MIN_MIN_CHOICES.map((m) => (
          <Chip
            key={m}
            active={minMinutes === m}
            onClick={() => set("min_minutes", String(m))}
          >
            {m}
          </Chip>
        ))}
      </FilterGroup>

      <div style={{ flex: 1 }} />

      <FilterGroup label="Data source">
        <select
          value={dataSource}
          onChange={(e) => set("data_source", e.target.value === "all" ? null : e.target.value)}
          className="pd-input"
          style={{ height: 30, padding: "0 8px", fontSize: 12, width: "auto" }}
        >
          <option value="all">Sample + Synthetic</option>
          <option value="sample">Sample only</option>
          <option value="synthetic">Synthetic only</option>
        </select>
      </FilterGroup>

      <FilterGroup label="Division">
        {DIVISIONS.filter((d) => options.divisions.includes(d) || options.divisions.some((x) => x.startsWith(d))).map((d) => {
          const matching = options.divisions.filter((x) => x === d || x.startsWith(d + "-"));
          const isAllOn = matching.every((m) => divisions.includes(m));
          return (
            <Chip
              key={d}
              active={isAllOn}
              onClick={() => {
                const next = isAllOn
                  ? divisions.filter((x) => !matching.includes(x))
                  : [...new Set([...divisions, ...matching])];
                set("divisions", next.length ? next : null);
              }}
            >
              {d.toUpperCase()}
            </Chip>
          );
        })}
      </FilterGroup>

      <FilterGroup label="Sport">
        <SportMultiSelect
          options={options.sports}
          selected={sports}
          onChange={(next) => set("sports", next.length ? next : null)}
        />
      </FilterGroup>

      <button
        onClick={resetAll}
        className="pd-btn pd-btn--ghost pd-btn--sm"
        style={{ height: 28 }}
      >
        Reset
      </button>

      {pending && <div style={{ fontSize: 11, color: "var(--fg-3)" }}>Updating…</div>}
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <span className="pd-label-caps" style={{ whiteSpace: "nowrap" }}>{label}</span>
      <div className="flex gap-1 flex-wrap">{children}</div>
    </div>
  );
}

function Chip({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "5px 10px",
        fontSize: 12,
        fontWeight: 600,
        border: active ? "1px solid var(--pd-green)" : "1px solid var(--pd-ink-200)",
        background: active ? "var(--pd-green-50)" : "var(--pd-surface)",
        color: active ? "var(--pd-green-700)" : "var(--fg-2)",
        borderRadius: 999,
        cursor: "pointer",
        transition: "all 120ms",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

/** Multi-select dropdown of sports with checkboxes. Scales better than a row of chips. */
function SportMultiSelect({
  options,
  selected,
  onChange,
}: {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
}) {
  function prettify(s: string) {
    return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  function toggle(s: string) {
    const next = selected.includes(s) ? selected.filter((x) => x !== s) : [...selected, s];
    onChange(next);
  }
  const summary =
    selected.length === 0
      ? "All sports"
      : selected.length === 1
        ? prettify(selected[0])
        : `${selected.length} selected`;

  return (
    <details style={{ position: "relative" }} className="sport-dropdown">
      <summary
        style={{
          listStyle: "none",
          cursor: "pointer",
          padding: "5px 10px",
          fontSize: 12,
          fontWeight: 600,
          border: selected.length ? "1px solid var(--pd-green)" : "1px solid var(--pd-ink-200)",
          background: selected.length ? "var(--pd-green-50)" : "var(--pd-surface)",
          color: selected.length ? "var(--pd-green-700)" : "var(--fg-2)",
          borderRadius: 999,
          whiteSpace: "nowrap",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        {summary}
        <svg width={10} height={10} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      <div
        style={{
          position: "absolute",
          top: "calc(100% + 4px)",
          left: 0,
          zIndex: 20,
          minWidth: 200,
          maxHeight: 280,
          overflow: "auto",
          background: "#fff",
          border: "1px solid var(--pd-ink-100)",
          borderRadius: 10,
          boxShadow: "var(--shadow-md, 0 8px 24px rgba(10,10,10,.08))",
          padding: 8,
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {options.map((s) => (
          <label
            key={s}
            className="flex items-center"
            style={{
              gap: 8,
              padding: "6px 8px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            <input
              type="checkbox"
              checked={selected.includes(s)}
              onChange={() => toggle(s)}
              style={{ accentColor: "var(--pd-green)" }}
            />
            {prettify(s)}
          </label>
        ))}
      </div>
    </details>
  );
}
