import { X } from "lucide-react";
import { replenishmentApi } from "../api/replenishmentApi";
import { useAsync } from "../hooks/useAsync";
import { formatCoverage, formatNumber } from "../utils/format";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { PriorityBadge } from "./PriorityBadge";
import { StatusBadge } from "./StatusBadge";

export function ProductDetailDrawer({
  itemCode,
  onClose,
}: {
  itemCode: string | null;
  onClose: () => void;
}) {
  const { data, loading, error, retry } = useAsync(
    () =>
      itemCode
        ? replenishmentApi.item(itemCode)
        : Promise.reject(new Error("Artículo no seleccionado.")),
    [itemCode],
  );

  if (!itemCode) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()}>
        <header className="drawer-header">
          <div>
            <span className="eyebrow">Detalle operativo</span>
            <h2>{data?.replenishment.item_name || itemCode}</h2>
            <p>{itemCode}</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Cerrar">
            <X size={20} />
          </button>
        </header>
        <div className="drawer-body">
          {loading && <LoadingState />}
          {error && <ErrorState message={error} onRetry={retry} />}
          {data && (
            <>
              <div className="badge-row">
                <StatusBadge value={data.replenishment.stock_status} />
                <PriorityBadge value={data.replenishment.priority_level} />
                <ConfidenceBadge value={data.replenishment.forecast_confidence} />
              </div>
              <div className="detail-grid">
                <Detail label="Stock disponible" value={formatNumber(data.replenishment.available_stock)} />
                <Detail label="Ingresos esperados" value={formatNumber(data.replenishment.on_order_stock)} />
                <Detail label="Consumo proyectado 3 meses" value={formatNumber(data.replenishment.projected_demand_horizon)} />
                <Detail label="Cobertura" value={formatCoverage(data.replenishment.coverage_days)} />
                <Detail label="Stock de seguridad" value={formatNumber(data.replenishment.safety_stock)} />
                <Detail label="Cantidad sugerida" value={formatNumber(data.replenishment.suggested_purchase_quantity)} />
              </div>
              <section className="drawer-callout">
                <strong>Acción recomendada</strong>
                <StatusBadge value={data.replenishment.recommendation_type} />
                <p>{data.replenishment.recommendation_reason}</p>
              </section>
              <section>
                <h3>Proyección mensual</h3>
                <div className="forecast-mini-list">
                  {data.forecast.map((point) => (
                    <div key={point.forecast_period}>
                      <span>{point.forecast_period}</span>
                      <strong>{formatNumber(point.forecast_quantity)}</strong>
                    </div>
                  ))}
                </div>
              </section>
              <p className="notice notice-amber">
                Las recomendaciones son informativas. No se crean órdenes de compra
                ni documentos en SAP.
              </p>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
