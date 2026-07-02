import type { LucideIcon } from "lucide-react";

type ActionTone = "blue" | "green" | "amber" | "red" | "slate";

interface ExecutiveActionCardProps {
  title: string;
  value?: number | string | null;
  description: string;
  tone?: ActionTone;
  icon: LucideIcon;
}

export function ExecutiveActionCard({
  title,
  value,
  description,
  tone = "blue",
  icon: Icon,
}: ExecutiveActionCardProps) {
  return (
    <article className={`executive-action-card action-${tone}`}>
      <div className="action-icon">
        <Icon size={22} />
      </div>
      <div>
        <span>{title}</span>
        <strong>{value ?? "Sin datos"}</strong>
        <p>{description}</p>
      </div>
    </article>
  );
}
