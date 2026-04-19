"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Split layout for the Athletes tab. Measures the right column's height via
 * ResizeObserver and pins the left column to match — so the scrollable roster
 * ends exactly at the bottom of the right-side content (drilldown + scatter).
 */
export function AthletesSplit({
  left,
  right,
}: {
  left: React.ReactNode;
  right: React.ReactNode;
}) {
  const rightRef = useRef<HTMLDivElement>(null);
  const [h, setH] = useState<number | null>(null);

  useEffect(() => {
    const el = rightRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        // contentRect height doesn't include padding/border consistently;
        // use getBoundingClientRect for a more accurate total.
        setH(e.target.getBoundingClientRect().height);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <section
      className="grid"
      style={{
        gridTemplateColumns: "300px 1fr",
        gap: 16,
        alignItems: "start",
      }}
    >
      <div
        style={{
          height: h ? `${h}px` : "auto",
          minHeight: 560,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {left}
      </div>
      <div ref={rightRef} className="flex flex-col" style={{ gap: 16, minWidth: 0 }}>
        {right}
      </div>
    </section>
  );
}
