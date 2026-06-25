const labels: Record<string, string> = {
  CRITICAL: "Crítico",
  NO_STOCK_WITH_DEMAND: "Sin stock",
  REVIEW: "Revisión",
  HEALTHY: "Saludable",
  OVERSTOCK: "Sobrestock",
  NO_DEMAND: "Sin demanda",
  NOT_RECOMMENDED: "No recomendado",
  PURCHASE_SUGGESTED: "Compra sugerida",
  REFERENTIAL_PURCHASE: "Compra referencial",
  MANUAL_REVIEW: "Revisión manual",
  NO_PURCHASE: "No comprar",
  MONITOR: "Monitorear",
  EXCLUDED: "Excluido",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`badge badge-${value.toLowerCase().replaceAll("_", "-")}`}>
      {labels[value] || value}
    </span>
  );
}
