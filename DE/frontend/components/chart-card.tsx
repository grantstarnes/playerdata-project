export function ChartCard({
  title,
  subtitle,
  right,
  children,
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="pd-card" style={{ padding: 20 }}>
      <div
        className="flex items-start justify-between"
        style={{ marginBottom: 14 }}
      >
        <div>
          <h3 className="pd-h3">{title}</h3>
          {subtitle && (
            <div style={{ color: "var(--fg-3)", fontSize: 12, marginTop: 2 }}>
              {subtitle}
            </div>
          )}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}
