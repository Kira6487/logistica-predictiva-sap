import { Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { replenishmentApi } from "../api/replenishmentApi";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PriorityBadge } from "../components/PriorityBadge";
import { ProductDetailDrawer } from "../components/ProductDetailDrawer";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { ReplenishmentItem } from "../types/replenishment";
import { formatCoverage, formatNumber } from "../utils/format";

export function ReplenishmentPage() {
  const { data, loading, error, retry } = useAsync(replenishmentApi.suggestions, []);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [priority, setPriority] = useState("");
  const [confidence, setConfidence] = useState("");
  const [onlyPurchases, setOnlyPurchases] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const rows = useMemo(() => {
    const query = search.toLowerCase().trim();
    return (data || []).filter((item) => {
      if (query && !`${item.item_code} ${item.item_name}`.toLowerCase().includes(query)) return false;
      if (status && item.stock_status !== status) return false;
      if (recommendation && item.recommendation_type !== recommendation) return false;
      if (priority && item.priority_level !== priority) return false;
      if (confidence && item.forecast_confidence !== confidence) return false;
      if (onlyPurchases && item.suggested_purchase_quantity <= 0) return false;
      return true;
    });
  }, [data, search, status, recommendation, priority, confidence, onlyPurchases]);

  if (loading) return <LoadingState label="Calculando tabla de reposición…" />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  const columns: Column<ReplenishmentItem>[] = [
    { key: "item", header: "Producto", width: "260px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "stock", header: "Disponible", align: "right", render: (row) => formatNumber(row.available_stock) },
    { key: "order", header: "En pedido", align: "right", render: (row) => formatNumber(row.on_order_stock) },
    { key: "forecast", header: "Forecast", align: "right", render: (row) => formatNumber(row.projected_demand_horizon) },
    { key: "coverage", header: "Cobertura", render: (row) => formatCoverage(row.coverage_days) },
    { key: "safety", header: "Seguridad", align: "right", render: (row) => formatNumber(row.safety_stock) },
    { key: "purchase", header: "Compra", align: "right", render: (row) => <strong>{formatNumber(row.suggested_purchase_quantity)}</strong> },
    { key: "status", header: "Estado", render: (row) => <StatusBadge value={row.stock_status} /> },
    { key: "recommendation", header: "Recomendación", render: (row) => <StatusBadge value={row.recommendation_type} /> },
    { key: "confidence", header: "Confianza", render: (row) => <ConfidenceBadge value={row.forecast_confidence} /> },
    { key: "priority", header: "Prioridad", render: (row) => <PriorityBadge value={row.priority_level} /> },
  ];

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div>
          <span className="eyebrow">Compras y logística</span>
          <h2>Reposición sugerida</h2>
          <p>Ordenada por prioridad, cobertura y riesgo operativo.</p>
        </div>
        <div className="result-count">{rows.length.toLocaleString("es-PE")} resultados</div>
      </section>
      <section className="panel filter-panel">
        <label className="search-field">
          <Search size={17} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar código o producto" />
        </label>
        <Filter value={status} onChange={setStatus} label="Estado" options={["CRITICAL", "NO_STOCK_WITH_DEMAND", "REVIEW", "HEALTHY", "OVERSTOCK", "NO_DEMAND", "NOT_RECOMMENDED"]} />
        <Filter value={recommendation} onChange={setRecommendation} label="Recomendación" options={["PURCHASE_SUGGESTED", "REFERENTIAL_PURCHASE", "MONITOR", "NO_PURCHASE", "MANUAL_REVIEW", "EXCLUDED"]} />
        <Filter value={priority} onChange={setPriority} label="Prioridad" options={["HIGH", "MEDIUM", "LOW"]} />
        <Filter value={confidence} onChange={setConfidence} label="Confianza" options={["MEDIUM", "LOW", "NOT_RECOMMENDED"]} />
        <label className="check-field">
          <input type="checkbox" checked={onlyPurchases} onChange={(e) => setOnlyPurchases(e.target.checked)} />
          Solo compras
        </label>
      </section>
      <p className="notice notice-amber">
        <SlidersHorizontal size={17} /> Las compras de confianza baja son referenciales y requieren aprobación humana.
      </p>
      <DataTable rows={rows} columns={columns} rowKey={(row) => row.item_code} onRowClick={(row) => setSelected(row.item_code)} />
      <ProductDetailDrawer itemCode={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function Filter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Todos</option>
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}
