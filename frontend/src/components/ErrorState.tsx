import { CircleAlert, RefreshCw } from "lucide-react";

export function ErrorState({
  message,
  onRetry,
  status,
}: {
  message: string;
  onRetry?: () => void;
  status?: number | null;
}) {
  const waking = status === 503;
  return (
    <div className="state-card state-error">
      <CircleAlert size={28} />
      <strong>{waking ? "La base demo se está reactivando" : "No se pudo cargar la información"}</strong>
      <p>{waking ? "Azure SQL serverless puede tardar unos segundos. Vuelva a intentar." : message}</p>
      {onRetry && (
        <button className="button button-secondary" onClick={onRetry}>
          <RefreshCw size={16} /> Reintentar
        </button>
      )}
    </div>
  );
}
