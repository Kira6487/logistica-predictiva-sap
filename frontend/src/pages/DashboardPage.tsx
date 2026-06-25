import {
  AlertTriangle,
  ClipboardCheck,
  PackageCheck,
  PackagePlus,
  ScanSearch,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Warehouse,
} from "lucide-react";
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
import { dashboardApi } from "../api/dashboardApi";
import { ErrorState } from "../components/ErrorState";
import { KpiCard } from "../components/KpiCard";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";

const COLORS = ["#0f6cbd", "#d83b01", "#f2c811", "#107c10", "#8764b8", "#64748b"];

export function DashboardPage() {
  const { data, loading, error, retry } = useAsync(async () => {
    const [replenishment, forecast, analytics, health] = await Promise.all([
      dashboardApi.replenishment(),
      dashboardApi.forecast(),
      dashboardApi.analytics(),
      dashboardApi.health(),
    ]);
    return { replenishment, forecast, analytics, health };
  }, []);

  if (loading) return <LoadingState label="Preparando tablero ejecutivo…" />;
  if (error || !data) return <ErrorState message={error || "Sin datos."} onRetry={retry} />;

  const { replenishment: r } = data;
  const statusData = [
    { name: "Críticos", value: r.critical_items },
    { name: "Revisión", value: r.review_items },
    { name: "Saludables", value: r.healthy_items },
    { name: "Sobrestock", value: r.overstock_items },
    { name: "Sin demanda", value: r.no_demand_items },
  ];
  const priorityData = [
    { name: "Alta", value: r.high_priority_items },
    { name: "Media", value: r.medium_priority_items },
    { name: "Baja", value: r.low_priority_items },
  ];
  const confidenceData = [
    { name: "Media", value: r.medium_confidence_items },
    { name: "Baja", value: r.low_confidence_items },
  ];
  const purchaseData = [
    { name: "Activa", value: r.active_purchase_suggestions },
    { name: "Referencial", value: r.referential_purchases },
  ];

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <span className="eyebrow">Resumen ejecutivo</span>
          <h2>Decisiones de inventario, en una sola vista</h2>
          <p>
            Prioriza riesgos de quiebre, compras conservadoras y exceso de stock
            usando datos reales de SAP Business One.
          </p>
        </div>
        <div className="hero-status">
          <span className="connection-dot" />
          API operativa · {data.health.status.toUpperCase()}
        </div>
      </section>

      <section className="kpi-grid">
        <KpiCard label="Artículos evaluados" value={r.total_items_evaluated} icon={Warehouse} />
        <KpiCard label="Con compra sugerida" value={r.items_with_purchase} icon={PackagePlus} tone="blue" />
        <KpiCard label="Compra activa" value={r.active_purchase_suggestions} icon={ClipboardCheck} tone="green" note="Confianza media" />
        <KpiCard label="Compra referencial" value={r.referential_purchases} icon={ScanSearch} tone="amber" note="Requiere revisión" />
        <KpiCard label="Productos críticos" value={r.critical_items} icon={ShieldAlert} tone="red" />
        <KpiCard label="Posible sobrestock" value={r.overstock_items} icon={PackageCheck} tone="violet" />
        <KpiCard label="Confianza media" value={r.medium_confidence_items} icon={Sparkles} tone="green" />
        <KpiCard label="Confianza baja" value={r.low_confidence_items} icon={AlertTriangle} tone="amber" />
        <KpiCard label="Revisión manual" value={r.manual_review_items} icon={TrendingUp} tone="slate" />
      </section>

      <section className="chart-grid">
        <ChartCard title="Estados operativos" subtitle="Artículos modelados por condición">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={statusData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {statusData.map((_, index) => <Cell key={index} fill={COLORS[index]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Prioridad operativa" subtitle="Orden sugerido de atención">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={priorityData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={100} paddingAngle={3}>
                {priorityData.map((_, index) => <Cell key={index} fill={COLORS[index + 1]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Tipo de compra" subtitle="Activa frente a referencial">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={purchaseData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={90} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f6cbd" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Confianza del forecast" subtitle="Sin artículos de confianza alta">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={confidenceData} dataKey="value" nameKey="name" outerRadius={90}>
                <Cell fill="#107c10" />
                <Cell fill="#f2c811" />
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <section className="notice-grid">
        <p className="notice notice-amber">Las compras de baja confianza son referenciales.</p>
        <p className="notice notice-blue">No se automatizan órdenes de compra.</p>
        <p className="notice notice-slate">Los valores monetarios están pendientes de validación.</p>
      </section>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <article className="panel chart-card">
      <header className="panel-header">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
      </header>
      {children}
    </article>
  );
}
