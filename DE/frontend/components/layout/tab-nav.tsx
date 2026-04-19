"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const TABS = [
  { href: "/dashboard/overview", label: "Overview",  iconPath: "M3 13h4l2-5 3 10 2-6 2 3h5" },
  { href: "/dashboard/athletes", label: "Athletes",  iconPath: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" },
];

function TabIcon({ d }: { d: string }) {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

// Filter keys that should carry over when switching tabs. Athlete-specific
// keys like `id` are omitted so clicking Athletes from Overview doesn't
// attempt to load a tab-specific context.
const PERSIST_KEYS = new Set(["gender", "sports", "divisions", "age_min", "age_max", "min_minutes", "data_source"]);

export function TabNav() {
  const pathname = usePathname();
  const params = useSearchParams();

  const persisted = new URLSearchParams();
  params.forEach((v, k) => {
    if (PERSIST_KEYS.has(k)) persisted.append(k, v);
  });
  const qs = persisted.toString();
  return (
    <nav
      className="bg-white"
      style={{ borderBottom: "1px solid var(--pd-ink-100)" }}
    >
      <div className="mx-auto flex gap-1" style={{ maxWidth: 1400, padding: "0 32px" }}>
        {TABS.map((t) => {
          const active = pathname === t.href || pathname.startsWith(t.href + "/");
          return (
            <Link
              key={t.href}
              href={qs ? `${t.href}?${qs}` : t.href}
              className="inline-flex items-center gap-2 transition-colors"
              style={{
                padding: "14px 14px 12px",
                fontFamily: "var(--font-body)",
                fontWeight: 600,
                fontSize: 14,
                color: active ? "var(--fg-1)" : "var(--fg-3)",
                borderBottom: active ? "2px solid var(--pd-green)" : "2px solid transparent",
                marginBottom: -1,
              }}
            >
              <TabIcon d={t.iconPath} />
              {t.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
