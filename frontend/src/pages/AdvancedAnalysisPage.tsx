import { BarChart3, Boxes, DatabaseZap, LineChart, ShieldCheck } from "lucide-react";
import { analyticsApi } from "../api/analyticsApi";
import { forecastApi } from "../api/forecastApi";
import { inventoryApi } from "../api/inventoryApi";
import { BusinessExplanationCard } from "../components/BusinessExplanationCard";
import { ErrorState } from "../components/ErrorState";
import { KpiCard } from "../components/KpiCard";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import { formatNumber, formatPercent } from "../utils/format";

export function AdvancedAnalysisPage() {
  const { data, loading, error, retry } = useAsync(async () => {
    const [forecast, inventory, analytics] = await Promise.all([
      forecastApi.summary(),
      inventoryApi.current(true),
      analyticsApi.summary(),
    ]);
    return { forecast, inventory, analytics };
  }, []);

  if (loading) return <LoadingState label="Preparando análisis avanzado..." />;
  if (error || !data) return <ErrorState message={error || "Sin datos."} onRetry={retry} />;

  const stockPositions = data.inventory.length;

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div>
          <span className="eyebrow">Detalle técnico explicado</span>
          <h2>Análisis avanzado</h2>
          <p>
            Espacio para usuarios logísticos que necesitan revisar proyección,
            inventario, segmentación técnica y calidad de datos.
          </p>
        </div>
      </section>

      <section className="kpi-grid kpi-grid-four">
        <KpiCard label="Artículos modelados" value={data.forecast.modeled_items} icon={LineChart} />
        <KpiCard label="Posiciones de inventario" value={stockPositions} icon={Boxes} tone="blue" />
        <KpiCard label="Artículos analizados" value={data.analytics.total_items_analyzed} icon={BarChart3} tone="green" />
        <KpiCard label="Calidad por revisar" value={data.analytics.insufficient_history_items} icon={ShieldCheck} tone="amber" />
      </section>

      <section className="advanced-topic-grid">
        <BusinessExplanationCard
          title="Proyección de consumo"
          description={`Horizonte actual: ${formatNumber(data.forecast.forecast_horizon)} meses. Diferencia promedio de la proyección: ${formatNumber(data.forecast.average_mae)} unidades.`}
        >
          <p className="technical-note">
            WAPE se usa aquí solo como métrica técnica de error porcentual:
            {` ${formatPercent(data.forecast.average_wape)}.`}
          </p>
        </BusinessExplanationCard>
        <BusinessExplanationCard
          title="Inventario por almacén"
          description="Consulta de stock físico, salidas comprometidas, ingresos esperados y stock disponible por almacén."
        />
        <BusinessExplanationCard
          title="Segmentación técnica"
          description={`ABC/XYZ agrupa artículos por relevancia y variabilidad. Artículos A: ${formatNumber(data.analytics.items_a)}, artículos Z: ${formatNumber(data.analytics.items_z)}.`}
        />
        <BusinessExplanationCard
          title="Calidad de datos"
          description={`Artículos con historial insuficiente: ${formatNumber(data.analytics.insufficient_history_items)}. Artículos con demanda negativa: ${formatNumber(data.analytics.negative_demand_items)}.`}
        />
        <BusinessExplanationCard
          title="Detalle histórico"
          description={`Periodo disponible: ${data.analytics.date_from} a ${data.analytics.date_to}. Meses evaluados: ${formatNumber(data.analytics.total_months_available)}.`}
        />
        <BusinessExplanationCard
          title="Lectura SAP"
          description="Los datos se consultan en modo lectura. Esta fase no crea, modifica ni elimina documentos SAP."
        >
          <p className="technical-note"><DatabaseZap size={15} /> Las tablas internas se mantienen fuera de las vistas principales.</p>
        </BusinessExplanationCard>
      </section>
    </div>
  );
}
