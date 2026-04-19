import { api } from "@/lib/api";
import { FilterForm } from "@/components/filters/filter-form";

export async function Sidebar() {
  const options = await api.filterOptions();
  return (
    <aside
      className="shrink-0 bg-white"
      style={{
        width: 280,
        borderRight: "1px solid var(--pd-ink-100)",
        minHeight: "calc(100vh - 64px - 49px)",
        padding: "20px 20px 40px",
      }}
    >
      <FilterForm options={options} />
      <hr className="pd-divider" style={{ marginTop: 20 }} />
      <div style={{ fontSize: 11, color: "var(--fg-3)" }}>
        {options.total_sessions.toLocaleString()} sessions · {options.sports.length} sports
      </div>
    </aside>
  );
}
