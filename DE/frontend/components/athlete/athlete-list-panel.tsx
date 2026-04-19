"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import type { AthleteRow } from "@/lib/api";

function initials(sport: string, id: number) {
  return (
    sport
      .split("_")
      .map((w) => w[0]?.toUpperCase() ?? "")
      .join("")
      .slice(0, 2) || String(id).slice(-2)
  );
}

function prettifySport(s: string) {
  return s.replace(/_/g, ". ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function AthleteListPanel({
  athletes,
  activeId,
}: {
  athletes: AthleteRow[];
  activeId: number | null;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [, startTransition] = useTransition();

  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return athletes;
    return athletes.filter(
      (a) =>
        String(a.athlete_id).includes(needle) ||
        (a.sport ?? "").toLowerCase().includes(needle) ||
        (a.division ?? "").toLowerCase().includes(needle),
    );
  }, [q, athletes]);

  function select(id: number) {
    const next = new URLSearchParams(params.toString());
    next.set("id", String(id));
    startTransition(() => router.push(`${pathname}?${next.toString()}`, { scroll: false }));
  }

  return (
    <div className="pd-card flex flex-col" style={{ padding: 12, gap: 10, height: "100%", minHeight: 560 }}>
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2"
          style={{ color: "var(--fg-3)" }}
          width={14} height={14} viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth={1.75}
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search roster..."
          className="pd-input"
          style={{ paddingLeft: 34, height: 36, fontSize: 13 }}
        />
      </div>

      <div
        className="flex flex-col overflow-y-auto"
        style={{ gap: 2, flex: 1, minHeight: 0 }}
      >
        {filtered.length === 0 && (
          <p style={{ fontSize: 12, color: "var(--fg-3)", padding: "12px 10px" }}>
            No athletes match.
          </p>
        )}
        {filtered.map((a) => {
          const on = a.athlete_id === activeId;
          return (
            <button
              key={a.athlete_id}
              onClick={() => select(a.athlete_id)}
              className="flex items-center text-left"
              style={{
                gap: 10,
                padding: "10px 10px",
                background: on ? "var(--pd-green-50)" : "transparent",
                border: on ? "1px solid var(--pd-green)" : "1px solid transparent",
                borderRadius: 10,
                cursor: "pointer",
                transition: "all 120ms",
              }}
            >
              <span
                className="flex items-center justify-center shrink-0"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: on ? "var(--pd-green)" : "var(--pd-ink-50)",
                  color: on ? "var(--pd-black)" : "var(--fg-2)",
                  fontWeight: 700,
                  fontSize: 11,
                }}
              >
                {initials(a.sport, a.athlete_id)}
              </span>
              <span className="flex-1 min-w-0">
                <span
                  className="block"
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: "var(--fg-1)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  #{a.athlete_id}
                </span>
                <span
                  className="block"
                  style={{
                    fontSize: 11,
                    color: "var(--fg-3)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {prettifySport(a.sport)} · {a.division.toUpperCase()}
                </span>
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: "var(--fg-3)",
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {a.sessions}
              </span>
            </button>
          );
        })}
      </div>
      <div
        className="pt-2"
        style={{ fontSize: 11, color: "var(--fg-3)", borderTop: "1px solid var(--pd-ink-100)" }}
      >
        {filtered.length.toLocaleString()} of {athletes.length.toLocaleString()} shown
      </div>
    </div>
  );
}
