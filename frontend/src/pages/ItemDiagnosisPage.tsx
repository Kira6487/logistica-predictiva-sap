import { useEffect, useMemo, useState } from "react";
import { replenishmentApi } from "../api/replenishmentApi";
import { BusinessExplanationCard } from "../components/BusinessExplanationCard";
import { ConfidencePercentBadge } from "../components/ConfidencePercentBadge";
import { DecisionBadge } from "../components/DecisionBadge";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import { formatNumber } from "../utils/format";

export function ItemDiagnosisPage() {
  const suggestions = useAsync(replenishmentApi.suggestions, []);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    if (!selected && suggestions.data?.length) {
      const preferred = suggestions.data.find((item) => item.suggested_purchase_quantity > 0);
      setSelected(preferred?.item_code || suggestions.data[0].item_code);
    }
  }, [selected, suggestions.data]);

  const selectedItem = useMemo(
    () => suggestions.data?.find((item) => item.item_code === selected),
    [selected, suggestions.data],
  );

  const detail = useAsync(
    () => (selected ? replenishmentApi.item(selected) : Promise.resolve(null)),
    [selected],
  );

  if (suggestions.loading) return <LoadingState label="Preparando diagnóstico por artículo..." />;
  if (suggestions.error || !suggestions.data) {
    return <ErrorState message={suggestions.error || "Sin datos."} onRetry={suggestions.retry} />;
  }

  const item = detail.data?.replenishment || selectedItem;

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div>
          <span className="eyebrow">Consulta detallada</span>
          <h2>Diagnóstico por artículo</h2>
          <p>Revise el origen de la cantidad sugerida sin exponer nombres técnicos de SAP.</p>
        </div>
        <select value={selected} onChange={(event) => setSelected(event.target.value)} className="product-select">
          {suggestions.data.map((candidate) => (
            <option key={candidate.item_code} value={candidate.item_code}>
              {candidate.item_code} - {candidate.item_name}
            </option>
          ))}
        </select>
      </section>

      {detail.loading && <LoadingState label="Consultando detalle..." />}
      {detail.error && <ErrorState message={detail.error} onRetry={detail.retry} />}

      {item && (
        <>
          <section className="diagnosis-header panel">
            <div>
              <span className="eyebrow">Artículo seleccionado</span>
              <h3>{item.item_name}</h3>
              <p>{item.item_code} - {item.warehouse_name || item.warehouse_code}</p>
            </div>
            <div className="badge-row">
              <DecisionBadge value={item.recommendation_type} />
              <ConfidencePercentBadge value={item.forecast_confidence} />
            </div>
          </section>

          <section className="diagnosis-grid">
            <Metric title="Stock disponible" value={item.available_stock} />
            <Metric title="Ingresos esperados" value={item.on_order_stock} />
            <Metric title="Salidas comprometidas" value={item.committed_stock} />
            <Metric title="Consumo proyectado" value={item.projected_demand_horizon} />
            <Metric title="Cantidad sugerida" value={item.suggested_purchase_quantity} highlight />
            <Metric title="Stock de seguridad" value={item.safety_stock} />
          </section>

          <section className="business-grid">
            <BusinessExplanationCard
              title="Lectura funcional"
              description={item.recommendation_reason || "Sin explicación disponible para este artículo."}
            />
            <BusinessExplanationCard
              title="Documentos SAP relacionados"
              description="Estructura preparada para mostrar documentos abiertos en fases siguientes."
            >
              <div className="related-docs">
                <details>
                  <summary>Ingresos esperados</summary>
                  <p>Órdenes de compra abiertas pendientes de incorporar.</p>
                </details>
                <details>
                  <summary>Salidas comprometidas</summary>
                  <p>Órdenes de venta abiertas pendientes de incorporar.</p>
                </details>
                <details>
                  <summary>Producción pendiente o consumo de componentes</summary>
                  <p>Órdenes de fabricación abiertas pendientes de incorporar.</p>
                </details>
              </div>
            </BusinessExplanationCard>
          </section>
        </>
      )}
    </div>
  );
}

function Metric({
  title,
  value,
  highlight = false,
}: {
  title: string;
  value?: number | null;
  highlight?: boolean;
}) {
  return (
    <article className={`metric-tile ${highlight ? "metric-highlight" : ""}`}>
      <span>{title}</span>
      <strong>{formatNumber(value)}</strong>
    </article>
  );
}
