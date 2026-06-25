import type { LucideIcon } from "lucide-react";
import { formatNumber } from "../utils/format";

interface KpiCardProps {
  label: string;
  value: number;
  icon: LucideIcon;
  tone?: "blue" | "red" | "amber" | "green" | "violet" | "slate";
  note?: string;
}

export function KpiCard({
  label,
  value,
  icon: Icon,
  tone = "blue",
  note,
}: KpiCardProps) {
  return (
    <article className={`kpi-card kpi-${tone}`}>
      <div className="kpi-icon">
        <Icon size={20} />
      </div>
      <div>
        <p className="kpi-label">{label}</p>
        <strong className="kpi-value">{formatNumber(value)}</strong>
        {note && <p className="kpi-note">{note}</p>}
      </div>
    </article>
  );
}
