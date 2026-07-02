const confidenceLabels: Record<string, string> = {
  HIGH: "Predicción confiable",
  MEDIUM: "Predicción usable",
  LOW: "Predicción con cautela",
  NOT_RECOMMENDED: "No usar para decidir",
};

const confidenceHints: Record<string, string> = {
  HIGH: "Alta",
  MEDIUM: "Media",
  LOW: "Baja",
  NOT_RECOMMENDED: "Sin recomendación",
};

export function ConfidencePercentBadge({ value }: { value?: string | null }) {
  const safeValue = value || "NOT_RECOMMENDED";
  return (
    <span className={`confidence-percent confidence-${safeValue.toLowerCase()}`}>
      <strong>{confidenceHints[safeValue] || "Revisar"}</strong>
      <span>{confidenceLabels[safeValue] || "Predicción con cautela"}</span>
    </span>
  );
}
