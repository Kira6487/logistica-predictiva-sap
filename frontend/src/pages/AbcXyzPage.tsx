import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { analyticsApi } from "../api/analyticsApi";
import { DataTable, type Column } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";
import type { AnalyticsItem } from "../types/analytics";
import { formatNumber } from "../utils/format";

const COLORS = ["#0f6cbd", "#8764b8", "#64748b", "#f2c811", "#d83b01"];

export function AbcXyzPage() {
  const { data, loading, error, retry } = useAsync(async () => {
    const [summary, abc, xyz, combined] = await Promise.all([
      analyticsApi.summary(),
      analyticsApi.abc(),
      analyticsApi.xyz(),
      analyticsApi.combined(),
    ]);
    return { summary, abc, xyz, combined };
  }, []);

  const qualityRows = useMemo(
    () => (data?.combined || []).filter((row) => row.recommended_for_forecast).slice(0, 100),
    [data],
  );

  if (loading) return <LoadingState label="Clasificando catálogo ABC/XYZ…" />;
  if (error || !data) return <ErrorState message={error || "Sin datos."} onRetry={retry} />;

  const abcData = [
    { name: "A", value: data.summary.items_a },
    { name: "B", value: data.summary.items_b },
    { name: "C", value: data.summary.items_c },
  ];
  const xyzData = [
    { name: "X", value: data.summary.items_x },
    { name: "Y", value: data.summary.items_y },
    { name: "Z", value: data.summary.items_z },
    { name: "Intermitente", value: data.summary.intermittent_items },
    { name: "Historia insuficiente", value: data.summary.insufficient_history_items },
  ];
  const columns: Column<AnalyticsItem>[] = [
    { key: "item", header: "Artículo", width: "300px", render: (row) => <div className="product-cell"><strong>{row.item_name}</strong><span>{row.item_code}</span></div> },
    { key: "abcxyz", header: "ABC / XYZ", render: (row) => <span className="segment-pill">{row.abc_xyz_class}</span> },
    { key: "quality", header: "Calidad", render: (row) => row.data_quality_status },
    { key: "quantity", header: "Demanda neta", align: "right", render: (row) => formatNumber(row.net_quantity_total) },
    { key: "cv", header: "Variabilidad", align: "right", render: (row) => formatNumber(row.coefficient_of_variation) },
  ];

  return (
    <div className="page-stack">
      <section className="page-intro">
        <div><span className="eyebrow">Segmentación del catálogo</span><h2>ABC / XYZ y calidad de datos</h2><p>No todos los productos son igualmente importantes ni pronosticables.</p></div>
        <div className="result-count">{data.summary.forecast_recommended_items} candidatos</div>
      </section>
      <section className="chart-grid">
        <article className="panel chart-card">
          <header className="panel-header"><div><h3>Importancia ABC</h3><p>Participación acumulada de cantidad neta.</p></div></header>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={abcData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={105}>
                {abcData.map((_, index) => <Cell key={index} fill={COLORS[index]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </article>
        <article className="panel chart-card">
          <header className="panel-header"><div><h3>Estabilidad XYZ</h3><p>La mayoría requiere más historia.</p></div></header>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={xyzData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8764b8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>
      </section>
      <section className="insight-grid">
        <article className="insight-card"><strong>{data.summary.forecast_recommended_items}</strong><span>Recomendados para forecast</span></article>
        <article className="insight-card"><strong>{data.summary.forecast_not_recommended_items}</strong><span>No recomendados todavía</span></article>
        <article className="insight-card"><strong>{data.summary.amount_anomaly_items}</strong><span>Con anomalía monetaria</span></article>
        <article className="insight-card"><strong>{data.summary.negative_demand_items}</strong><span>Demanda negativa</span></article>
      </section>
      <section className="panel">
        <header className="panel-header"><div><h3>Muestra de candidatos</h3><p>Los primeros productos aptos para análisis predictivo.</p></div></header>
        <DataTable rows={qualityRows} columns={columns} rowKey={(row) => row.item_code} pageSize={10} />
      </section>
    </div>
  );
}
