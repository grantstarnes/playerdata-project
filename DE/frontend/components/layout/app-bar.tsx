import { UserButton } from "@clerk/nextjs";

export function AppBar() {
  return (
    <header
      className="sticky top-0 z-20 bg-white"
      style={{ borderBottom: "1px solid var(--pd-ink-100)" }}
    >
      <div
        className="mx-auto flex items-center gap-6"
        style={{ height: 64, maxWidth: 1400, padding: "0 32px" }}
      >
        <img src="/brand/logo-wordmark.svg" alt="PlayerData" style={{ height: 28 }} />

        <div className="relative flex-1 max-w-[420px]">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "var(--fg-3)" }}
            width={16} height={16} viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth={1.75}
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            placeholder="Search athletes, sessions, teams..."
            className="pd-input"
            style={{
              height: 36,
              paddingLeft: 36,
              background: "var(--pd-ink-50)",
              borderColor: "transparent",
            }}
          />
        </div>

        <div className="ml-auto flex items-center gap-3">
          <span className="pd-badge pd-badge--live">LIVE · Gemma 4</span>
          <div className="pl-3" style={{ borderLeft: "1px solid var(--pd-ink-100)" }}>
            <UserButton />
          </div>
        </div>
      </div>
    </header>
  );
}
