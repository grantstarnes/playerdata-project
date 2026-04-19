"use client";

import { useState } from "react";
import { AgeStatsTable } from "@/components/age-stats-table";
import { AgeTrend } from "@/components/charts/age-trend";
import { AgeBar } from "@/components/charts/age-bar";
import { SessionLoadByAge } from "@/components/charts/session-load-by-age";

type Row = {
  age: number;
  count: number;
  mean: number;
  sd: number;
  top10: number;
  bottom10: number;
};

type BoxRow = {
  age: number; n: number; min: number; q1: number; median: number;
  q3: number; max: number; mean: number;
};

type Props = {
  metrics: string[];
  tables: Record<string, Row[]>;
  boxRows: BoxRow[];
};

const LABEL: Record<string, string> = {
  total_distance_m: "Total Distance (m)",
  max_speed_kph:    "Max Speed (kph)",
  session_load:     "Session Load",
  sprint_events:    "Sprint Events",
};

export function BenchmarksAccordion({ metrics, tables, boxRows }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set(metrics.length > 0 ? [metrics[0]] : []),
  );
  const [activeChart, setActiveChart] = useState<string | null>(null);

  function toggle(m: string) {
    setExpanded((s) => {
      const next = new Set(s);
      if (next.has(m)) next.delete(m);
      else next.add(m);
      return next;
    });
  }

  return (
    <>
      <div className="flex flex-col" style={{ gap: 12 }}>
        {metrics.map((m) => {
          const rows = tables[m] ?? [];
          const isOpen = expanded.has(m);
          return (
            <div
              key={m}
              className="pd-card"
              style={{ padding: 0, overflow: "hidden" }}
            >
              {/* Header */}
              <div
                className="flex items-center"
                style={{
                  padding: "12px 16px",
                  borderBottom: isOpen ? "1px solid var(--pd-ink-100)" : "none",
                  gap: 12,
                }}
              >
                <button
                  onClick={() => toggle(m)}
                  aria-expanded={isOpen}
                  className="flex items-center flex-1"
                  style={{
                    background: "transparent",
                    border: 0,
                    cursor: "pointer",
                    textAlign: "left",
                    padding: 0,
                    gap: 10,
                  }}
                >
                  <Chevron open={isOpen} />
                  <h3 className="pd-h3" style={{ margin: 0 }}>{LABEL[m] ?? m}</h3>
                  <span
                    className="pd-badge"
                    style={{ marginLeft: 8, fontWeight: 500 }}
                  >
                    {rows.length} age{rows.length === 1 ? "" : "s"}
                  </span>
                </button>

                <button
                  onClick={() => setActiveChart(m)}
                  className="pd-btn pd-btn--secondary pd-btn--sm"
                  style={{ gap: 6 }}
                >
                  <ChartIcon />
                  View chart
                </button>
              </div>

              {/* Body */}
              {isOpen && <AgeStatsTable metric={m} rows={rows} bare />}
            </div>
          );
        })}
      </div>

      {/* Slide-in drawer */}
      <Drawer
        open={activeChart !== null}
        onClose={() => setActiveChart(null)}
        title={activeChart ? `${LABEL[activeChart] ?? activeChart} · Chart` : ""}
      >
        {activeChart === "total_distance_m" && (
          <AgeTrend data={tables.total_distance_m ?? []} title="Total Distance (m)" unit=" m" />
        )}
        {activeChart === "max_speed_kph" && (
          <AgeTrend data={tables.max_speed_kph ?? []} title="Max Speed (kph)" unit=" kph" />
        )}
        {activeChart === "session_load" && (
          <SessionLoadByAge data={boxRows} bare />
        )}
        {activeChart === "sprint_events" && (
          <AgeBar data={tables.sprint_events ?? []} title="Sprint Events" />
        )}
      </Drawer>
    </>
  );
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width={16} height={16} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
      style={{
        transform: open ? "rotate(90deg)" : "rotate(0deg)",
        transition: "transform 180ms",
        color: "var(--fg-3)",
      }}
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3v18h18" />
      <path d="m19 9-5 5-4-4-3 3" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18" /><path d="m6 6 12 12" />
    </svg>
  );
}

function Drawer({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(10,10,10,0.35)",
          backdropFilter: "blur(2px)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
          transition: "opacity 200ms",
          zIndex: 50,
        }}
      />
      {/* Panel */}
      <aside
        role="dialog"
        aria-hidden={!open}
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "min(820px, 92vw)",
          background: "#fff",
          boxShadow: "var(--shadow-lg, -16px 0 48px rgba(10,10,10,.15))",
          transform: open ? "translateX(0)" : "translateX(100%)",
          transition: "transform 280ms cubic-bezier(.16,1,.3,1)",
          zIndex: 51,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          className="flex items-center"
          style={{ padding: "16px 20px", borderBottom: "1px solid var(--pd-ink-100)", gap: 12 }}
        >
          <h2 className="pd-h3" style={{ margin: 0, flex: 1 }}>{title}</h2>
          <button
            onClick={onClose}
            className="pd-btn pd-btn--ghost pd-btn--sm"
            style={{ width: 32, height: 32, padding: 0, borderRadius: 8 }}
            aria-label="Close chart"
          >
            <XIcon />
          </button>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: "20px 24px", minHeight: 0 }}>
          {children}
        </div>
      </aside>
    </>
  );
}
