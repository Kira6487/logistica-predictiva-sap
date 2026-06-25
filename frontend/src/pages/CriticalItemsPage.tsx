import { replenishmentApi } from "../api/replenishmentApi";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PriorityBadge } from "../components/PriorityBadge";
import { ProductDetailDrawer } from "../components/ProductDetailDrawer";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { useState } from "react";
import type { ReplenishmentItem } from "../types/replenishment";
import { formatCoverage, formatNumber } from "../utils/format";

export function CriticalItemsPage() {
  const { data, loading, error, retry } = useAsync(replenishmentApi.critical, []);
  const [selected, setSelected] = useState<string | null>(null);
  if (loading) return <LoadingState label="Identificando productos críticos…" />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  const columns: Column<ReplenishmentItem>[] = [
    { key: "item", header: "Producto", width: "300px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "status", header: "Condición", render: (row) => <StatusBadge value={row.stock_status} /> },
    { key: "priority", header: "Prioridad", render: (row) => <PriorityBadge value={row.priority_level} /> },
    { key: "stock", header: "Disponible", align: "right", render: (row) => formatNumber(row.available_stock) },
    { key: "coverage", header: "Cobertura", render: (row) => formatCoverage(row.coverage_days) },
    { key: "purchase", header: "Compra sugerida", align: "right", render: (row) => <strong>{formatNumber(row.suggested_purchase_quantity)}</strong> },
    { key: "reason", header: "Motivo", width: "340px", render: (row) => row.recommendation_reason },
  ];

  return (
    <div className="page-stack">
      <section className="page-intro critical-intro">
        <div><span className="eyebrow">Atención inmediata</span><h2>Productos críticos</h2><p>Sin stock o con menos de 30 días de cobertura.</p></div>
        <strong>{data?.length || 0}</strong>
      </section>
      <DataTable rows={data || []} columns={columns} rowKey={(row) => row.item_code} onRowClick={(row) => setSelected(row.item_code)} />
      <ProductDetailDrawer itemCode={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
