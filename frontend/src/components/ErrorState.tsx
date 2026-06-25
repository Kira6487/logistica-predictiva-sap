import { CircleAlert, RefreshCw } from "lucide-react";

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="state-card state-error">
      <CircleAlert size={28} />
      <strong>No se pudo cargar la información</strong>
      <p>{message}</p>
      {onRetry && (
        <button className="button button-secondary" onClick={onRetry}>
          <RefreshCw size={16} /> Reintentar
        </button>
      )}
    </div>
  );
}
