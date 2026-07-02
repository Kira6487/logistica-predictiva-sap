const labels: Record<string, string> = {
  PURCHASE_SUGGESTED: "Abastecer",
  REFERENTIAL_PURCHASE: "Revisar",
  MANUAL_REVIEW: "Revisar",
  NO_PURCHASE: "No comprar",
  MONITOR: "Monitorear",
  EXCLUDED: "Sin acción",
  CRITICAL: "Atender crítico",
  NO_STOCK_WITH_DEMAND: "Atender crítico",
  REVIEW: "Revisar",
  HEALTHY: "Monitorear",
  OVERSTOCK: "No comprar",
  NO_DEMAND: "No comprar",
  NOT_RECOMMENDED: "Sin acción",
};

const tones: Record<string, string> = {
  PURCHASE_SUGGESTED: "green",
  REFERENTIAL_PURCHASE: "amber",
  MANUAL_REVIEW: "amber",
  NO_PURCHASE: "slate",
  MONITOR: "blue",
  EXCLUDED: "slate",
  CRITICAL: "red",
  NO_STOCK_WITH_DEMAND: "red",
  REVIEW: "amber",
  HEALTHY: "blue",
  OVERSTOCK: "slate",
  NO_DEMAND: "slate",
  NOT_RECOMMENDED: "slate",
};

export function DecisionBadge({ value }: { value?: string | null }) {
  const safeValue = value || "NOT_RECOMMENDED";
  return (
    <span className={`decision-badge decision-${tones[safeValue] || "slate"}`}>
      {labels[safeValue] || "Revisar"}
    </span>
  );
}
