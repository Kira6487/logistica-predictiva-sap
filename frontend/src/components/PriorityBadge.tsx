export function PriorityBadge({ value }: { value: string }) {
  const label = value === "HIGH" ? "Alta" : value === "MEDIUM" ? "Media" : "Baja";
  return <span className={`priority priority-${value.toLowerCase()}`}>{label}</span>;
}
