export function LoadingState({ label = "Cargando datos reales…" }: { label?: string }) {
  return (
    <div className="state-card">
      <span className="spinner" />
      <p>{label}</p>
    </div>
  );
}
