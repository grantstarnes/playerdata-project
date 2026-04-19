"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useTransition } from "react";

import type { FilterOptions } from "@/lib/api";

export function FilterForm({ options }: { options: FilterOptions }) {
  const router = useRouter();
  const pathname = usePathname();
  const current = useSearchParams();
  const [pending, startTransition] = useTransition();

  function set(key: string, value: string | null) {
    const params = new URLSearchParams(current.toString());
    if (value === null || value === "") params.delete(key);
    else params.set(key, value);
    startTransition(() => router.push(`${pathname}?${params.toString()}`));
  }

  const dataSource = current.get("data_source") ?? "all";
  const gender = current.get("gender") ?? "all";
  const minMinutes = Number(current.get("min_minutes") ?? 70);

  const DATA_SOURCES = [
    { value: "all",       label: "Sample + Synthetic" },
    { value: "sample",    label: "Sample only" },
    { value: "synthetic", label: "Synthetic only" },
  ];
  const GENDERS = [{ value: "all", label: "All" }, ...options.genders.map((g) => ({ value: g, label: g[0].toUpperCase() + g.slice(1) }))];

  return (
    <div>
      <div className="pd-h3" style={{ marginBottom: 4 }}>Filters</div>
      <div style={{ color: "var(--fg-3)", fontSize: 12, marginBottom: 20 }}>
        Applies to all tabs
      </div>

      <Field label="Data source">
        <div className="flex flex-col gap-1.5">
          {DATA_SOURCES.map((d) => (
            <label
              key={d.value}
              className="flex items-center gap-2.5 cursor-pointer"
              style={{ fontSize: 13 }}
            >
              <input
                type="radio"
                checked={dataSource === d.value}
                onChange={() => set("data_source", d.value === "all" ? null : d.value)}
                style={{ accentColor: "var(--pd-green)" }}
              />
              {d.label}
            </label>
          ))}
        </div>
      </Field>

      <Field label="Gender">
        <div className="flex gap-1.5">
          {GENDERS.map((g) => (
            <Chip
              key={g.value}
              active={gender === g.value}
              onClick={() => set("gender", g.value === "all" ? null : g.value)}
            >
              {g.label}
            </Chip>
          ))}
        </div>
      </Field>

      <Field label={`Min active minutes — ${minMinutes}`}>
        <input
          type="range"
          min={0}
          max={120}
          step={5}
          value={minMinutes}
          onChange={(e) => set("min_minutes", e.target.value)}
          className="w-full"
          style={{ accentColor: "var(--pd-green)" }}
        />
        <div
          className="flex justify-between"
          style={{ color: "var(--fg-3)", fontSize: 11, marginTop: 2 }}
        >
          <span>0</span>
          <span>120</span>
        </div>
      </Field>

      <hr className="pd-divider" />

      <button
        className="pd-btn pd-btn--secondary pd-btn--sm"
        style={{ width: "100%" }}
        onClick={() => startTransition(() => router.push(pathname))}
      >
        Reset filters
      </button>

      <div style={{ fontSize: 11, color: "var(--fg-3)", lineHeight: 1.5, marginTop: 16 }}>
        DS pipeline default: <code className="pd-mono" style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "var(--pd-ink-50)", padding: "1px 6px", borderRadius: 6 }}>active_minutes ≥ 70</code>
      </div>

      {pending && (
        <div style={{ fontSize: 11, color: "var(--fg-3)", marginTop: 8 }}>
          Updating…
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div className="pd-label-caps" style={{ marginBottom: 8 }}>{label}</div>
      {children}
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
        padding: "6px 10px",
        fontSize: 12,
        fontWeight: 600,
        border: active ? "1px solid var(--pd-green)" : "1px solid var(--pd-ink-200)",
        background: active ? "var(--pd-green-50)" : "var(--pd-surface)",
        color: active ? "var(--pd-green-700)" : "var(--fg-2)",
        borderRadius: 999,
        cursor: "pointer",
        transition: "all 120ms",
      }}
    >
      {children}
    </button>
  );
}
