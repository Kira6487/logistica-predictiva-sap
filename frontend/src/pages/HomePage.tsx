import {
  AlertTriangle,
  ClipboardCheck,
  FileSearch,
  PackageCheck,
  PackagePlus,
  ShieldAlert,
} from "lucide-react";
import { dashboardApi } from "../api/dashboardApi";
import { BusinessExplanationCard } from "../components/BusinessExplanationCard";
import { ErrorState } from "../components/ErrorState";
import { ExecutiveActionCard } from "../components/ExecutiveActionCard";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import { formatNumber } from "../utils/format";

export function HomePage() {
  const { data, loading, error, retry } = useAsync(async () => {
    const [replenishment, health] = await Promise.all([
      dashboardApi.replenishment(),
      dashboardApi.health(),
    ]);
    return { replenishment, health };
  }, []);

  if (loading) return <LoadingState label="Preparando resumen ejecutivo..." />;
  if (error || !data) return <ErrorState message={error || "Sin datos."} onRetry={retry} />;

  const summary = data.replenishment;
  const noBuyCount = summary.overstock_items + summary.no_demand_items + summary.not_recommended_items;

  return (
    <div className="page-stack">
      <section className="hero-panel executive-hero">
        <div>
          <span className="eyebrow">Resumen ejecutivo</span>
          <h2>¿Qué debe hacer hoy?</h2>
          <p>
            Diagnóstico logístico basado en consumo histórico, salidas proyectadas
            y partidas abiertas de SAP Business One.
          </p>
        </div>
        <div className="hero-status">
          <span className="connection-dot" />
          API operativa: {data.health.status}
        </div>
      </section>

      <section className="executive-action-grid">
        <ExecutiveActionCard
          title="Abastecer ahora"
          value={`${formatNumber(summary.active_purchase_suggestions)} artículos`}
          description="Artículos con cantidad sugerida y predicción usable."
          tone="green"
          icon={PackagePlus}
        />
        <ExecutiveActionCard
          title="Revisar antes de abastecer"
          value={`${formatNumber(summary.referential_purchases + summary.review_items)} artículos`}
          description="Casos que requieren validación logística antes de comprar."
          tone="amber"
          icon={FileSearch}
        />
        <ExecutiveActionCard
          title="Atender riesgo critico"
          value={`${formatNumber(summary.critical_items)} artículos`}
          description="Riesgo de quiebre o cobertura insuficiente."
          tone="red"
          icon={ShieldAlert}
        />
        <ExecutiveActionCard
          title="No comprar"
          value={`${formatNumber(noBuyCount)} artículos`}
          description="Sin acción sugerida, sin demanda o con exceso de stock."
          tone="slate"
          icon={PackageCheck}
        />
      </section>

      <section className="business-grid">
        <BusinessExplanationCard
          title="Plan recomendado para el horizonte operativo"
          description={`Se evaluaron ${formatNumber(summary.total_items_evaluated)} artículos para un horizonte de ${summary.horizon_months} meses.`}
        >
          <div className="plan-list">
            <p><ClipboardCheck size={16} /> Priorizar abastecimiento con predicción usable.</p>
            <p><AlertTriangle size={16} /> Validar manualmente los casos de cautela.</p>
            <p><PackageCheck size={16} /> Evitar compras en articulos sin accion o con exceso.</p>
          </div>
        </BusinessExplanationCard>
        <BusinessExplanationCard
          title="Origen general del diagnóstico SAP"
          items={[
            "Consumo histórico registrado en SAP",
            "Órdenes de compra abiertas",
            "Órdenes de venta abiertas",
            "Órdenes de fabricación abiertas",
            "Inventario actual por almacén",
          ]}
        />
      </section>
    </div>
  );
}
