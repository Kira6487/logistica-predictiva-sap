export function ConfidenceBadge({ value }: { value: string }) {
  const label =
    value === "HIGH"
      ? "Alta"
      : value === "MEDIUM"
        ? "Media"
        : value === "LOW"
          ? "Baja"
          : "No recomendada";
  return (
    <span className={`confidence confidence-${value.toLowerCase()}`}>{label}</span>
  );
}
