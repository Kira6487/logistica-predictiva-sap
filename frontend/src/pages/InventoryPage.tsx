import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { inventoryApi } from "../api/inventoryApi";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import type { InventoryItem } from "../types/inventory";
import { formatNumber } from "../utils/format";

export function InventoryPage() {
  const { data, loading, error, retry } = useAsync(() => inventoryApi.current(true), []);
  const [search, setSearch] = useState("");
  const [warehouse, setWarehouse] = useState("");
  const [onlyPositive, setOnlyPositive] = useState(true);

  const warehouses = useMemo(
    () => Array.from(new Set((data || []).map((row) => row.warehouse_code))).sort(),
    [data],
  );
  const rows = useMemo(() => {
    const query = search.toLowerCase().trim();
    return (data || []).filter((row) => {
      if (warehouse && row.warehouse_code !== warehouse) return false;
      if (onlyPositive && row.physical_stock === 0 && row.on_order_stock === 0) return false;
      return !query || `${row.item_code} ${row.item_name}`.toLowerCase().includes(query);
    });
  }, [data, search, warehouse, onlyPositive]);

  if (loading) return <LoadingState label="Consultando inventario por almacén…" />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  const columns: Column<InventoryItem>[] = [
    { key: "item", header: "Artículo", width: "300px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "warehouse", header: "Almacén", render: (row) => <div className="product-cell"><strong>{row.warehouse_code}</strong><span>{row.warehouse_name}</span></div> },
    { key: "physical", header: "Físico", align: "right", render: (row) => formatNumber(row.physical_stock) },
    { key: "committed", header: "Comprometido", align: "right", render: (row) => formatNumber(row.committed_stock) },
    { key: "order", header: "En pedido", align: "right", render: (row) => formatNumber(row.on_order_stock) },
    { key: "available", header: "Disponible", align: "right", render: (row) => <strong>{formatNumber(row.available_stock)}</strong> },
    { key: "projected", header: "Proyectado", align: "right", render: (row) => formatNumber(row.projected_stock) },
  ];

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div><span className="eyebrow">Existencias SAP</span><h2>Inventario por almacén</h2><p>Stock físico, comprometido, en pedido y disponible.</p></div>
        <div className="result-count">{rows.length.toLocaleString("es-PE")} posiciones</div>
      </section>
      <section className="panel filter-panel">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar artículo" /></label>
        <label className="select-field"><span>Almacén</span><select value={warehouse} onChange={(e) => setWarehouse(e.target.value)}><option value="">Todos</option>{warehouses.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label className="check-field"><input type="checkbox" checked={onlyPositive} onChange={(e) => setOnlyPositive(e.target.checked)} />Solo con existencias o pedidos</label>
      </section>
      <DataTable rows={rows} columns={columns} rowKey={(row) => `${row.item_code}-${row.warehouse_code}`} pageSize={20} />
    </div>
  );
}
