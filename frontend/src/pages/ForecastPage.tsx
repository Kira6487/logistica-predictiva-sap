import { useEffect, useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { forecastApi } from "../api/forecastApi";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { KpiCard } from "../components/KpiCard";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import type { ForecastCandidate, ForecastItemDetail } from "../types/forecast";
import { formatNumber, formatPercent } from "../utils/format";
import { Activity, BrainCircuit, ChartSpline, Target } from "lucide-react";

export function ForecastPage() {
  const summaryState = useAsync(
    async () => {
      const [summary, candidates, results] = await Promise.all([
        forecastApi.summary(),
        forecastApi.candidates(),
        forecastApi.results(),
      ]);
      return { summary, candidates, results };
    },
    [],
  );
  const [selected, setSelected] = useState("");

  useEffect(() => {
    if (!selected && summaryState.data?.candidates.length) {
      const forecastedItems = new Set(
        summaryState.data.results.map((row) => row.item_code),
      );
      const preferred = [...summaryState.data.candidates]
        .filter((candidate) => forecastedItems.has(candidate.item_code))
        .sort((a, b) =>
          (b.last_sale_period || "").localeCompare(a.last_sale_period || ""),
        )[0];
      setSelected(preferred?.item_code || summaryState.data.candidates[0].item_code);
    }
  }, [summaryState.data, selected]);

  const detailState = useAsync<ForecastItemDetail | null>(
    () => (selected ? forecastApi.item(selected) : Promise.resolve(null)),
    [selected],
  );

  if (summaryState.loading) return <LoadingState label="Cargando modelos y forecast…" />;
  if (summaryState.error || !summaryState.data) {
    return <ErrorState message={summaryState.error || "Sin datos."} onRetry={summaryState.retry} />;
  }

  const chartData = buildChartData(detailState.data);
  const columns: Column<ForecastCandidate>[] = [
    { key: "item", header: "Artículo", width: "280px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "segment", header: "Segmento", render: (row) => row.abc_xyz_class },
    { key: "model", header: "Mejor modelo", render: (row) => row.best_model || "—" },
    { key: "wape", header: "WAPE", align: "right", render: (row) => formatPercent(row.best_wape) },
    { key: "mae", header: "MAE", align: "right", render: (row) => formatNumber(row.best_mae) },
    { key: "confidence", header: "Confianza", render: (row) => <ConfidenceBadge value={row.forecast_confidence || "NOT_RECOMMENDED"} /> },
  ];

  const { summary } = summaryState.data;
  return (
    <div className="page-stack">
      <section className="page-intro">
        <div><span className="eyebrow">Demanda futura</span><h2>Forecast por producto</h2><p>Comparación temporal de modelos y proyección de tres meses.</p></div>
      </section>
      <section className="kpi-grid kpi-grid-four">
        <KpiCard label="Artículos modelados" value={summary.modeled_items} icon={BrainCircuit} />
        <KpiCard label="WAPE promedio" value={summary.average_wape} icon={Target} tone="amber" />
        <KpiCard label="MAE promedio" value={summary.average_mae} icon={Activity} tone="violet" />
        <KpiCard label="Confianza media" value={summary.medium_confidence} icon={ChartSpline} tone="green" />
      </section>
      <section className="panel forecast-focus">
        <header className="panel-header">
          <div>
            <h3>{detailState.data?.item.item_name || "Seleccione un artículo"}</h3>
            <p>
              {detailState.data?.best_model?.best_model || "—"} ·{" "}
              {detailState.data?.best_model && (
                <ConfidenceBadge value={detailState.data.best_model.forecast_confidence} />
              )}
            </p>
          </div>
          <select value={selected} onChange={(e) => setSelected(e.target.value)} className="product-select">
            {summaryState.data.candidates.map((candidate) => (
              <option key={candidate.item_code} value={candidate.item_code}>
                {candidate.item_code} · {candidate.item_name}
              </option>
            ))}
          </select>
        </header>
        {detailState.loading && <LoadingState />}
        {detailState.error && <ErrorState message={detailState.error} onRetry={detailState.retry} />}
        {detailState.data && (
          <ResponsiveContainer width="100%" height={360}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Area dataKey="upper" stroke="none" fill="#dbeafe" fillOpacity={0.6} />
              <Line type="monotone" dataKey="actual" name="Demanda real" stroke="#334155" strokeWidth={2} dot={false} connectNulls />
              <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#0f6cbd" strokeWidth={3} strokeDasharray="6 4" connectNulls />
            </ComposedChart>
          </ResponsiveContainer>
        )}
        <p className="notice notice-amber">
          El WAPE promedio es alto. Use la proyección como apoyo y mantenga revisión humana.
        </p>
      </section>
      <section className="panel">
        <header className="panel-header"><div><h3>Artículos modelados</h3><p>Seleccione una fila para actualizar el gráfico.</p></div></header>
        <DataTable rows={summaryState.data.candidates} columns={columns} rowKey={(row) => row.item_code} pageSize={10} onRowClick={(row) => setSelected(row.item_code)} />
      </section>
    </div>
  );
}

function buildChartData(detail: ForecastItemDetail | null) {
  if (!detail) return [];
  const map = new Map<string, { period: string; actual?: number; forecast?: number; upper?: number }>();
  [...detail.historical, ...detail.test].forEach((point) => {
    map.set(point.period, { period: point.period, actual: point.net_quantity });
  });
  detail.future_forecast.forEach((point) => {
    map.set(point.forecast_period, {
      period: point.forecast_period,
      forecast: point.forecast_quantity,
      upper: point.upper_bound,
    });
  });
  return Array.from(map.values()).slice(-24);
}
