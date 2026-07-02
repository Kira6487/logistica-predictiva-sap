import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { replenishmentApi } from "../api/replenishmentApi";
import { AdvancedFiltersPanel } from "../components/AdvancedFiltersPanel";
import { ConfidencePercentBadge } from "../components/ConfidencePercentBadge";
import { DataTable, type Column } from "../components/DataTable";
import { DecisionBadge } from "../components/DecisionBadge";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PriorityBadge } from "../components/PriorityBadge";
import { ProductDetailDrawer } from "../components/ProductDetailDrawer";
import { useAsync } from "../hooks/useAsync";
import type { ReplenishmentItem } from "../types/replenishment";
import { formatCoverage, formatNumber } from "../utils/format";

const actionOptions = [
  { value: "", label: "Todas" },
  { value: "PURCHASE_SUGGESTED", label: "Abastecer" },
  { value: "REFERENTIAL_PURCHASE", label: "Revisar" },
  { value: "MANUAL_REVIEW", label: "Revisar manualmente" },
  { value: "NO_PURCHASE", label: "No comprar" },
  { value: "MONITOR", label: "Monitorear" },
  { value: "EXCLUDED", label: "Sin acción" },
];

const priorityOptions = [
  { value: "", label: "Todas" },
  { value: "HIGH", label: "Alta" },
  { value: "MEDIUM", label: "Media" },
  { value: "LOW", label: "Baja" },
];

const confidenceOptions = [
  { value: "", label: "Todas" },
  { value: "MEDIUM", label: "Predicción usable" },
  { value: "LOW", label: "Predicción con cautela" },
  { value: "NOT_RECOMMENDED", label: "No usar para decidir" },
];

export function RecommendationsPage() {
  const { data, loading, error, retry } = useAsync(replenishmentApi.suggestions, []);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [priority, setPriority] = useState("");
  const [confidence, setConfidence] = useState("");
  const [warehouse, setWarehouse] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const warehouses = useMemo(
    () => Array.from(new Set((data || []).map((item) => item.warehouse_code))).sort(),
    [data],
  );

  const rows = useMemo(() => {
    const query = search.toLowerCase().trim();
    return (data || []).filter((item) => {
      if (query && !`${item.item_code} ${item.item_name}`.toLowerCase().includes(query)) return false;
      if (action && item.recommendation_type !== action) return false;
      if (priority && item.priority_level !== priority) return false;
      if (confidence && item.forecast_confidence !== confidence) return false;
      if (warehouse && item.warehouse_code !== warehouse) return false;
      return true;
    });
  }, [data, search, action, priority, confidence, warehouse]);

  if (loading) return <LoadingState label="Preparando recomendaciones..." />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  const columns: Column<ReplenishmentItem>[] = [
    { key: "item", header: "Artículo", width: "260px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "warehouse", header: "Almacén", render: (row) => row.warehouse_name || row.warehouse_code },
    { key: "available", header: "Stock disponible", align: "right", render: (row) => formatNumber(row.available_stock) },
    { key: "incoming", header: "Ingresos esperados", align: "right", render: (row) => formatNumber(row.on_order_stock) },
    { key: "committed", header: "Salidas comprometidas", align: "right", render: (row) => formatNumber(row.committed_stock) },
    { key: "projected", header: "Consumo proyectado", align: "right", render: (row) => formatNumber(row.projected_demand_horizon) },
    { key: "coverage", header: "Cobertura", render: (row) => formatCoverage(row.coverage_days) },
    { key: "purchase", header: "Cantidad sugerida", align: "right", render: (row) => <strong>{formatNumber(row.suggested_purchase_quantity)}</strong> },
    { key: "action", header: "Acción", render: (row) => <DecisionBadge value={row.recommendation_type} /> },
    { key: "confidence", header: "Confianza", render: (row) => <ConfidencePercentBadge value={row.forecast_confidence} /> },
    { key: "priority", header: "Prioridad", render: (row) => <PriorityBadge value={row.priority_level} /> },
  ];

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div>
          <span className="eyebrow">Acciones logísticas</span>
          <h2>Recomendaciones</h2>
          <p>Prioriza artículos para abastecer, revisar, monitorear o no comprar.</p>
        </div>
        <div className="result-count">{rows.length.toLocaleString("es-PE")} resultados</div>
      </section>

      <AdvancedFiltersPanel resultCount={rows.length}>
        <label className="search-field">
          <Search size={17} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar artículo" />
        </label>
        <SelectFilter label="Acción" value={action} onChange={setAction} options={actionOptions} />
        <SelectFilter label="Prioridad" value={priority} onChange={setPriority} options={priorityOptions} />
        <SelectFilter label="Confianza" value={confidence} onChange={setConfidence} options={confidenceOptions} />
        <label className="select-field">
          <span>Almacén</span>
          <select value={warehouse} onChange={(event) => setWarehouse(event.target.value)}>
            <option value="">Todos</option>
            {warehouses.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
      </AdvancedFiltersPanel>

      <DataTable rows={rows} columns={columns} rowKey={(row) => `${row.item_code}-${row.warehouse_code}`} onRowClick={(row) => setSelected(row.item_code)} />
      <ProductDetailDrawer itemCode={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function SelectFilter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value || "all"} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}
