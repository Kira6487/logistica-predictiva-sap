import { useState } from "react";
import { replenishmentApi } from "../api/replenishmentApi";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { ProductDetailDrawer } from "../components/ProductDetailDrawer";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { ReplenishmentItem } from "../types/replenishment";
import { formatCoverage, formatNumber } from "../utils/format";

export function OverstockPage() {
  const { data, loading, error, retry } = useAsync(replenishmentApi.overstock, []);
  const [selected, setSelected] = useState<string | null>(null);
  if (loading) return <LoadingState label="Analizando exceso de cobertura…" />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  const columns: Column<ReplenishmentItem>[] = [
    { key: "item", header: "Producto", width: "320px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "stock", header: "Stock disponible", align: "right", render: (row) => formatNumber(row.available_stock) },
    { key: "forecast", header: "Demanda proyectada", align: "right", render: (row) => formatNumber(row.projected_demand_horizon) },
    { key: "coverage", header: "Cobertura", render: (row) => formatCoverage(row.coverage_days) },
    { key: "status", header: "Estado", render: (row) => <StatusBadge value={row.stock_status} /> },
    { key: "recommendation", header: "Recomendación", render: (row) => <StatusBadge value={row.recommendation_type} /> },
  ];
  return (
    <div className="page-stack">
      <section className="page-intro">
        <div><span className="eyebrow">Capital e inventario</span><h2>Posible sobrestock</h2><p>Productos con cobertura superior a 180 días.</p></div>
        <div className="result-count">{data?.length || 0} productos</div>
      </section>
      <DataTable rows={data || []} columns={columns} rowKey={(row) => row.item_code} onRowClick={(row) => setSelected(row.item_code)} />
      <ProductDetailDrawer itemCode={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
