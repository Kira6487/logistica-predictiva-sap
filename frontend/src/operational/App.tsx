import { useEffect, useMemo, useState } from "react";
import {
  getCachedItemDiagnosis,
  loadActionsPage,
  loadInitialAppData,
  loadItemDiagnosis,
  loadPurchaseCandidatesPage,
  loadRecommendationsPage,
  loadTransferCandidatesPage,
} from "./appDataStore";
import {
  ActionIcon,
  ConfidenceBadge,
  EmptyState,
  ErrorState,
  FilterBar,
  KpiCard,
  LoadingState,
  PriorityBadge,
  RecommendationTable,
  RecommendationTypeBadge,
  RiskBadge,
  ResizableTable,
  type ResizableTableColumn,
  SectionHeader,
  StatusBadge,
  WarningBox,
  formatLabel,
  formatNumber,
  pageIcons,
} from "./components";
import { useAppData } from "./useAppData";
import type { AppDataState, CachedResource } from "./appDataStore";
import type {
  CoverageRiskSummary,
  ItemDiagnosis,
  ProjectedKardexLine,
  RelatedDocument,
  RecommendationActions,
  RecommendationFilters,
  RecommendationRecord,
  RecommendationsSummary,
  PaginatedActionsResponse,
  PaginatedResponse,
  StockSummary,
  WarehouseRecommendationSummary,
} from "./types";

type PageKey = "inicio" | "recomendaciones" | "compras" | "traslados" | "validaciones" | "diagnostico" | "analisis";

const navItems: Array<{ key: PageKey; label: string }> = [
  { key: "inicio", label: "Inicio" },
  { key: "recomendaciones", label: "Recomendaciones" },
  { key: "compras", label: "Compras sugeridas" },
  { key: "traslados", label: "Traslados sugeridos" },
  { key: "validaciones", label: "Validaciones" },
  { key: "diagnostico", label: "Diagnostico por articulo" },
  { key: "analisis", label: "Analisis avanzado" },
];

function ResourceNotice<T>({ resource, label }: { resource: CachedResource<T>; label: string }) {
  if (resource.status === "loading" && !resource.data) return <LoadingState label={`Cargando ${label}...`} />;
  if (resource.error) return <ErrorState message={`${label}: ${resource.error}`} />;
  return null;
}

function PaginationControls({
  total,
  limit,
  offset,
  hasNext,
  hasPrevious,
  onChange,
}: {
  total: number;
  limit: number;
  offset: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onChange: (next: { limit: number; offset: number }) => void;
}) {
  const currentPage = Math.floor(offset / limit) + 1;
  return (
    <div className="pagination-bar">
      <span>Página {formatNumber(currentPage)} · {formatNumber(total)} resultados</span>
      <label>
        <span>Por página</span>
        <select value={limit} onChange={(event) => onChange({ limit: Number(event.target.value), offset: 0 })}>
          {[20, 50, 100].map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <button className="secondary-button compact-button" type="button" disabled={!hasPrevious} onClick={() => onChange({ limit, offset: Math.max(0, offset - limit) })}>Anterior</button>
      <button className="secondary-button compact-button" type="button" disabled={!hasNext} onClick={() => onChange({ limit, offset: offset + limit })}>Siguiente</button>
    </div>
  );
}

function DistributionList({ title, values }: { title: string; values: Record<string, number> }) {
  const entries = Object.entries(values || {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return <EmptyState message={`Sin datos para ${title}.`} />;
  const max = Math.max(...entries.map(([, value]) => value), 1);
  return (
    <section className="distribution">
      <h3>{title}</h3>
      {entries.map(([key, value]) => (
        <div className="distribution-row" key={key}>
          <span>{formatLabel(key)}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
          </div>
          <strong>{formatNumber(value)}</strong>
        </div>
      ))}
    </section>
  );
}

function DashboardPage({
  summary,
  lastUpdated,
  onNavigate,
}: {
  summary: CachedResource<RecommendationsSummary>;
  lastUpdated: string | null;
  onNavigate: (page: PageKey) => void;
}) {
  const data = summary.data;
  if (summary.status === "loading" && !data) return <LoadingState />;
  if (!data) return summary.error ? <ErrorState message={summary.error} /> : <EmptyState />;

  const updatedText = lastUpdated ? new Date(lastUpdated).toLocaleString("es-PE") : "Sin actualización";
  const confidenceValues = {
    alta: data.cantidad_por_confianza.alta || 0,
    media: data.cantidad_por_confianza.media || 0,
    baja: data.cantidad_por_confianza.baja || 0,
    sin_confianza: data.cantidad_por_confianza.sin_confianza || data.total_datos_insuficientes || 0,
  };
  const statusValues = {
    accion_recomendada: data.total_accion_recomendada,
    requiere_validacion: data.total_requiere_validacion,
    solo_monitoreo: data.total_solo_monitoreo,
    no_accion: data.total_sin_accion,
    datos_insuficientes: data.total_datos_insuficientes,
  };
  const urgentCount = data.cantidad_por_prioridad.urgente || 0;
  const monitorCount = data.total_solo_monitoreo + data.total_sin_accion;

  return (
    <div className="page-stack executive-home">
      <header className="executive-header">
        <div className="section-title">
          {pageIcons.home}
          <div>
            <h2>Resumen ejecutivo de inventario</h2>
            <p>Vista gerencial de acciones prioritarias, riesgo de quiebre y estado del plan de abastecimiento.</p>
          </div>
        </div>
        <div className="executive-updated">
          <span>Última actualización</span>
          <strong>{updatedText}</strong>
        </div>
      </header>
      <ResourceNotice resource={summary} label="resumen de recomendaciones" />
      <WarningBox>Las recomendaciones son referenciales y requieren validación humana antes de operar en SAP.</WarningBox>

      <section className="executive-panel">
        <div className="executive-panel-heading">
          <div>
            <h3>¿Qué debe hacer hoy?</h3>
            <p>{formatNumber(data.total_recomendaciones_evaluadas)} artículos evaluados en el último diagnóstico disponible.</p>
          </div>
        </div>
        <div className="executive-action-grid">
          <ExecutiveActionCard title="Abastecer ahora" value={data.compras_sugeridas} detail="Artículos con inventario insuficiente frente a la demanda proyectada." buttonLabel="Ver plan" tone="buy" onClick={() => onNavigate("recomendaciones")} />
          <ExecutiveActionCard title="Revisar antes de abastecer" value={data.total_requiere_validacion} detail="Casos que requieren validar datos, compromisos o criterios operativos." buttonLabel="Revisar casos" tone="review" onClick={() => onNavigate("validaciones")} />
          <ExecutiveActionCard title="Atender riesgo crítico" value={urgentCount} detail="Prioridades urgentes con mayor exposición a quiebre o impacto operativo." buttonLabel="Ver artículos" tone="critical" onClick={() => onNavigate("recomendaciones")} />
          <ExecutiveActionCard title="No comprar / monitorear" value={monitorCount} detail="Artículos con cobertura suficiente, baja rotación o seguimiento sin acción inmediata." buttonLabel="Ver artículos" tone="monitor" onClick={() => onNavigate("recomendaciones")} />
        </div>
      </section>

      <div className="executive-two-column">
        <section className="executive-panel">
          <div className="executive-panel-heading">
            <div>
              <h3>Confianza general</h3>
              <p>La confianza indica qué tan sólido es el diagnóstico según historial, consumo y calidad de datos.</p>
            </div>
          </div>
          <div className="confidence-grid">
            <KpiCard title="Confianza alta" value={confidenceValues.alta} tone="success" />
            <KpiCard title="Confianza media" value={confidenceValues.media} tone="blue" />
            <KpiCard title="Confianza baja" value={confidenceValues.baja} tone="amber" />
            <KpiCard title="Datos insuficientes" value={confidenceValues.sin_confianza} tone="muted" />
          </div>
        </section>

        <section className="executive-panel">
          <div className="executive-panel-heading">
            <div>
              <h3>Acciones prioritarias</h3>
              <p>Lista corta para orientar la revisión diaria sin cargar tablas extensas.</p>
            </div>
          </div>
          <div className="executive-task-list">
            <ExecutiveTask title="Abastecer artículos críticos" value={data.compras_sugeridas} buttonLabel="Ir a Plan de abastecimiento" onClick={() => onNavigate("recomendaciones")} />
            <ExecutiveTask title="Revisar artículos con datos insuficientes" value={data.total_datos_insuficientes} buttonLabel="Ir a Validaciones" onClick={() => onNavigate("validaciones")} />
            <ExecutiveTask title="Validar casos con riesgo operativo alto" value={urgentCount} buttonLabel="Ir a Diagnóstico por artículo" onClick={() => onNavigate("diagnostico")} />
            <ExecutiveTask title="Revisar maestro de artículos" value={data.revisiones_maestro_sugeridas} buttonLabel="Ir a Validaciones" onClick={() => onNavigate("validaciones")} />
            <ExecutiveTask title="Monitorear artículos con bajo riesgo" value={monitorCount} buttonLabel="Ir a Plan de abastecimiento" onClick={() => onNavigate("recomendaciones")} />
          </div>
        </section>
      </div>

      <div className="executive-chart-grid">
        <ExecutiveBars title="Distribución por acción" values={data.cantidad_por_tipo} />
        <ExecutiveBars title="Distribución por prioridad" values={data.cantidad_por_prioridad} />
        <ExecutiveBars title="Distribución por estado" values={statusValues} />
      </div>

      <section className="executive-panel">
        <div className="executive-panel-heading">
          <div>
            <h3>Reportes disponibles</h3>
            <p>Accesos seguros para profundizar el análisis sin ejecutar operaciones transaccionales.</p>
          </div>
        </div>
        <div className="report-grid">
          <ReportShortcut title="Plan de abastecimiento" detail="Acciones recomendadas y filtros operativos." onClick={() => onNavigate("recomendaciones")} />
          <ReportShortcut title="Kardex proyectado por artículo" detail="Proyección por artículo bajo consulta puntual." onClick={() => onNavigate("diagnostico")} />
          <ReportShortcut title="Auditoría de disponibilidad" detail="Detalle de stock disponible, ingresos, salidas y necesidad estimada." onClick={() => onNavigate("diagnostico")} />
          <ReportShortcut title="Riesgo de quiebre" detail="Resumen analítico de prioridades y exposición." onClick={() => onNavigate("analisis")} />
          <ReportShortcut title="Validaciones de datos" detail="Casos que deben revisarse antes de decidir." onClick={() => onNavigate("validaciones")} />
          <ReportShortcut title="Análisis avanzado" detail="Vista técnica resumida para seguimiento gerencial." onClick={() => onNavigate("analisis")} />
        </div>
      </section>
    </div>
  );
}

function ExecutiveActionCard({
  title,
  value,
  detail,
  buttonLabel,
  tone,
  onClick,
}: {
  title: string;
  value: number;
  detail: string;
  buttonLabel: string;
  tone: string;
  onClick: () => void;
}) {
  return (
    <article className={`executive-action-card executive-${tone}`}>
      <div>
        <span>{title}</span>
        <strong>{formatNumber(value)}</strong>
        <p>{detail}</p>
      </div>
      <button className="secondary-button compact-button" type="button" onClick={onClick}>{buttonLabel}</button>
    </article>
  );
}

function ExecutiveBars({ title, values }: { title: string; values: Record<string, number> }) {
  const entries = Object.entries(values || {}).filter(([, value]) => value > 0).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const max = Math.max(...entries.map(([, value]) => value), 1);
  return (
    <section className="executive-panel executive-bars">
      <h3>{title}</h3>
      {entries.length ? entries.map(([key, value]) => (
        <div className="executive-bar-row" key={key}>
          <span>{formatLabel(key)}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
          </div>
          <strong>{formatNumber(value)}</strong>
        </div>
      )) : <EmptyState message={`Sin datos para ${title}.`} />}
    </section>
  );
}

function ExecutiveTask({ title, value, buttonLabel, onClick }: { title: string; value: number; buttonLabel: string; onClick: () => void }) {
  return (
    <article className="executive-task">
      <div>
        <strong>{title}</strong>
        <span>{formatNumber(value)} artículos</span>
      </div>
      <button className="secondary-button compact-button" type="button" onClick={onClick}>{buttonLabel}</button>
    </article>
  );
}

function ReportShortcut({ title, detail, onClick }: { title: string; detail: string; onClick: () => void }) {
  return (
    <button className="report-shortcut" type="button" onClick={onClick}>
      <strong>{title}</strong>
      <span>{detail}</span>
    </button>
  );
}

type SupplyPlanTab = "general" | "compras" | "traslados" | "validaciones" | "monitoreo";

const supplyTabs: Array<{ key: SupplyPlanTab; label: string }> = [
  { key: "general", label: "Plan general" },
  { key: "compras", label: "Compras sugeridas" },
  { key: "traslados", label: "Traslados sugeridos" },
  { key: "validaciones", label: "Validaciones" },
  { key: "monitoreo", label: "No comprar / monitorear" },
];

function supplyActionLabel(item: RecommendationRecord) {
  if (item.recommendation_type === "comprar" && item.nivel_riesgo === "critico") return "Atender riesgo crítico";
  if (item.recommendation_type === "comprar" || item.recommendation_type === "acelerar_compra_abierta") return "Abastecer ahora";
  if (item.recommendation_type === "trasladar_stock" || item.recommendation_type === "revisar_venta_comprometida") return "Revisar antes de abastecer";
  if (item.recommendation_type === "no_comprar") return "No comprar";
  if (item.recommendation_type === "validar_datos") return "Validar datos";
  if (item.recommendation_type === "revisar_maestro_articulo") return "Revisar maestro";
  return "Monitorear";
}

function supplyActionClass(item: RecommendationRecord) {
  const label = supplyActionLabel(item);
  if (label === "Atender riesgo crítico") return "supply-critical";
  if (label === "Abastecer ahora") return "supply-buy";
  if (label === "Revisar antes de abastecer" || label === "Validar datos" || label === "Revisar maestro") return "supply-review";
  if (label === "No comprar") return "supply-no-buy";
  return "supply-monitor";
}

function actionMatchesFilter(item: RecommendationRecord, value?: string) {
  if (!value) return true;
  return supplyActionLabel(item) === value;
}

function tabMatches(item: RecommendationRecord, tab: SupplyPlanTab) {
  if (tab === "compras") return item.recommendation_type === "comprar" || item.recommendation_type === "acelerar_compra_abierta";
  if (tab === "traslados") return item.recommendation_type === "trasladar_stock";
  if (tab === "validaciones") return ["validar_datos", "revisar_maestro_articulo", "revisar_venta_comprometida"].includes(item.recommendation_type);
  if (tab === "monitoreo") return ["no_comprar", "monitorear", "sin_recomendacion"].includes(item.recommendation_type);
  return true;
}

function buildSupplySummary(items: RecommendationRecord[]) {
  return {
    abastecer: items.filter((item) => supplyActionLabel(item) === "Abastecer ahora" || supplyActionLabel(item) === "Atender riesgo crítico").length,
    revisar: items.filter((item) => ["Revisar antes de abastecer", "Validar datos", "Revisar maestro"].includes(supplyActionLabel(item))).length,
    noComprar: items.filter((item) => supplyActionLabel(item) === "No comprar").length,
    monitorear: items.filter((item) => supplyActionLabel(item) === "Monitorear").length,
  };
}

function RecommendationsPage({ appData, onOpenItem }: { appData: AppDataState; onOpenItem: (itemCode: string) => void }) {
  const [filters, setFilters] = useState<RecommendationFilters & { supply_action?: string }>({ limit: 50, offset: 0 });
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [tab, setTab] = useState<SupplyPlanTab>("general");
  const [supportItem, setSupportItem] = useState<RecommendationRecord | null>(null);
  const diagnosis = supportItem?.item_code ? getCachedItemDiagnosis(supportItem.item_code, supportItem.warehouse_code || undefined) : null;

  useEffect(() => {
    if (supportItem?.item_code) {
      void loadItemDiagnosis(supportItem.item_code, supportItem.warehouse_code || undefined);
    }
  }, [supportItem?.item_code, supportItem?.warehouse_code]);

  const backendFilters = useMemo(() => {
    const typeFromAction =
      filters.supply_action === "No comprar" ? "no_comprar"
        : filters.supply_action === "Monitorear" ? "monitorear"
          : filters.supply_action === "Validar datos" ? "validar_datos"
            : filters.supply_action === "Revisar maestro" ? "revisar_maestro_articulo"
              : undefined;
    return {
      item_code: filters.item_code,
      warehouse: filters.warehouse,
      recommendation_type: typeFromAction,
      priority_level: filters.priority_level,
      confidence_level: filters.confidence_level,
      risk_level: filters.risk_level,
      only_purchase_suggestions: filters.only_purchase_suggestions || tab === "compras",
      only_transfer_suggestions: filters.only_transfer_suggestions || tab === "traslados",
      only_data_validation: filters.only_data_validation || tab === "validaciones",
      min_priority_score: filters.min_priority_score,
      max_priority_score: filters.max_priority_score,
      limit: filters.limit,
      offset: filters.offset,
    };
  }, [filters, tab]);

  useEffect(() => {
    void loadRecommendationsPage(backendFilters);
  }, [backendFilters]);

  const rows = appData.recommendationsItems.data?.items || [];
  const summary = buildSupplySummary(rows);
  const priorityItems = [...rows].sort((a, b) => b.priority_score - a.priority_score).slice(0, 5);

  const updateFilter = (key: keyof (RecommendationFilters & { supply_action?: string }), value: string | number | boolean) => {
    setFilters((current) => ({ ...current, [key]: value || undefined, offset: key === "offset" ? Number(value) : 0 }));
  };
  const updatePage = ({ limit, offset }: { limit: number; offset: number }) => setFilters((current) => ({ ...current, limit, offset }));

  return (
    <div className="page-stack">
      <SectionHeader
        title="Plan de abastecimiento y control de riesgo"
        subtitle="Acciones sugeridas por artículo según inventario actual, documentos abiertos, consumo histórico y riesgo de quiebre."
        icon={pageIcons.recommendations}
      />
      <WarningBox>Las cantidades son referenciales y requieren validación humana antes de operar en SAP.</WarningBox>

      <div className="supply-summary-grid">
        <SupplySummaryCard title="Abastecer ahora" value={summary.abastecer} detail="Inventario insuficiente frente a demanda proyectada." tone="buy" />
        <SupplySummaryCard title="Revisar antes de abastecer" value={summary.revisar} detail="Casos con datos, documentos o compromisos por validar." tone="review" />
        <SupplySummaryCard title="No comprar" value={summary.noComprar} detail="Cobertura suficiente o baja rotación esperada." tone="no-buy" />
        <SupplySummaryCard title="Monitorear" value={summary.monitorear} detail="Seguimiento operativo sin acción inmediata." tone="monitor" />
      </div>

      <div className="supply-tabs" role="tablist" aria-label="Secciones del plan">
        {supplyTabs.map((item) => (
          <button key={item.key} type="button" className={tab === item.key ? "active" : ""} onClick={() => setTab(item.key)}>{item.label}</button>
        ))}
      </div>

      <div className="supply-layout">
        <section className="supply-panel supply-main-panel">
          <div className="supply-panel-header">
            <div>
              <h3>Plan de abastecimiento</h3>
              <p>{rows.length} artículos según filtros actuales</p>
            </div>
            <button className="secondary-button" type="button" onClick={() => setAdvancedOpen((value) => !value)}>
              {advancedOpen ? "Ocultar filtros avanzados" : "Mostrar filtros avanzados"}
            </button>
          </div>
          <SupplyPlanFilters filters={filters} updateFilter={updateFilter} advancedOpen={advancedOpen} />
          <ResourceNotice resource={appData.recommendationsItems} label="plan de abastecimiento" />
          {appData.recommendationsItems.status === "loading" && !appData.recommendationsItems.data ? <LoadingState label="Cargando página del plan..." /> : <SupplyPlanTable items={rows} onSupport={setSupportItem} onOpenItem={onOpenItem} />}
          {appData.recommendationsItems.data ? <PaginationControls total={appData.recommendationsItems.data.total} limit={appData.recommendationsItems.data.limit} offset={appData.recommendationsItems.data.offset} hasNext={appData.recommendationsItems.data.has_next} hasPrevious={appData.recommendationsItems.data.has_previous} onChange={updatePage} /> : null}
        </section>

        <aside className="supply-side">
          <SupplyPriorityPanel items={priorityItems} onSupport={setSupportItem} />
          <SupplyDistribution items={rows} />
        </aside>
      </div>

      {supportItem ? (
        <SupplySupportPanel
          item={supportItem}
          diagnosis={diagnosis?.data || null}
          loading={diagnosis?.status === "loading"}
          error={diagnosis?.error || null}
          onClose={() => setSupportItem(null)}
          onOpenItem={onOpenItem}
        />
      ) : null}
    </div>
  );
}

function SupplySummaryCard({ title, value, detail, tone }: { title: string; value: number; detail: string; tone: string }) {
  return (
    <article className={`supply-summary-card supply-summary-${tone}`}>
      <div className="supply-summary-icon"><ActionIcon type={tone === "buy" ? "comprar" : tone === "review" ? "validar_datos" : tone === "no-buy" ? "no_comprar" : "monitorear"} /></div>
      <div>
        <h3>{title}</h3>
        <strong>{formatNumber(value)} artículos</strong>
        <p>{detail}</p>
      </div>
    </article>
  );
}

function SupplyPlanFilters({
  filters,
  updateFilter,
  advancedOpen,
}: {
  filters: RecommendationFilters & { supply_action?: string };
  updateFilter: (key: keyof (RecommendationFilters & { supply_action?: string }), value: string | number | boolean) => void;
  advancedOpen: boolean;
}) {
  return (
    <div className="supply-filters">
      <label className="filter-field">
        <span>Artículo</span>
        <input value={filters.item_code || ""} onChange={(event) => updateFilter("item_code", event.target.value)} placeholder="Código o parte del código" />
      </label>
      <label className="filter-field">
        <span>Almacén</span>
        <input value={filters.warehouse || ""} onChange={(event) => updateFilter("warehouse", event.target.value)} placeholder="Código almacén" />
      </label>
      <label className="filter-field">
        <span>Acción recomendada</span>
        <select value={filters.supply_action || ""} onChange={(event) => updateFilter("supply_action", event.target.value)}>
          <option value="">Todas</option>
          {["Abastecer ahora", "Revisar antes de abastecer", "Atender riesgo crítico", "No comprar", "Monitorear", "Validar datos", "Revisar maestro"].map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </label>
      <label className="filter-field">
        <span>Prioridad</span>
        <select value={filters.priority_level || ""} onChange={(event) => updateFilter("priority_level", event.target.value)}>
          <option value="">Todas</option>
          {["urgente", "alta", "media", "baja", "informativa"].map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
        </select>
      </label>
      <label className="filter-field">
        <span>Confianza</span>
        <select value={filters.confidence_level || ""} onChange={(event) => updateFilter("confidence_level", event.target.value)}>
          <option value="">Todas</option>
          {["alta", "media", "baja", "sin_confianza"].map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
        </select>
      </label>
      <label className="filter-field">
        <span>Riesgo</span>
        <select value={filters.risk_level || ""} onChange={(event) => updateFilter("risk_level", event.target.value)}>
          <option value="">Todos</option>
          {["critico", "alto", "medio", "bajo", "sin_riesgo_aparente", "sin_diagnostico"].map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
        </select>
      </label>
      {advancedOpen ? (
        <div className="advanced-filters">
          <label><input type="checkbox" checked={Boolean(filters.only_purchase_suggestions)} onChange={(event) => updateFilter("only_purchase_suggestions", event.target.checked)} /> Solo compras sugeridas</label>
          <label><input type="checkbox" checked={Boolean(filters.only_transfer_suggestions)} onChange={(event) => updateFilter("only_transfer_suggestions", event.target.checked)} /> Solo traslados sugeridos</label>
          <label><input type="checkbox" checked={Boolean(filters.only_data_validation)} onChange={(event) => updateFilter("only_data_validation", event.target.checked)} /> Solo validación de datos</label>
          <label><input type="checkbox" checked={Boolean(filters.only_master_review)} onChange={(event) => updateFilter("only_master_review", event.target.checked)} /> Solo maestro de artículos</label>
          <label className="filter-field">
            <span>Mínimo score prioridad</span>
            <input type="number" value={filters.min_priority_score ?? ""} onChange={(event) => updateFilter("min_priority_score", event.target.value ? Number(event.target.value) : "")} placeholder="0" />
          </label>
          <label className="filter-field">
            <span>Máximo score prioridad</span>
            <input type="number" value={filters.max_priority_score ?? ""} onChange={(event) => updateFilter("max_priority_score", event.target.value ? Number(event.target.value) : "")} placeholder="100" />
          </label>
        </div>
      ) : null}
    </div>
  );
}

function SupplyPlanTable({ items, onSupport, onOpenItem }: { items: RecommendationRecord[]; onSupport: (item: RecommendationRecord) => void; onOpenItem: (itemCode: string) => void }) {
  const columns: ResizableTableColumn<RecommendationRecord>[] = [
    { key: "item", header: "Artículo", width: 220, minWidth: 150, maxWidth: 420, kind: "medium", render: (item) => <><strong>{item.item_name || "Sin nombre"}</strong><small>{item.item_code || "-"}</small></> },
    { key: "warehouse", header: "Almacén", width: 110, minWidth: 84, maxWidth: 180, kind: "short", render: (item) => item.warehouse_code || "-" },
    { key: "action", header: "Acción recomendada", width: 190, minWidth: 150, maxWidth: 360, kind: "medium", render: (item) => <span className={`supply-action-pill ${supplyActionClass(item)}`}>{supplyActionLabel(item)}</span> },
    { key: "quantity", header: "Cantidad sugerida", width: 140, minWidth: 110, maxWidth: 220, kind: "short", align: "right", render: (item) => item.suggested_quantity > 0 ? `${formatNumber(item.suggested_quantity, 2)} ref.` : "-" },
    { key: "priority", header: "Prioridad", width: 120, minWidth: 100, maxWidth: 190, kind: "short", render: (item) => <PriorityBadge value={item.priority_level} /> },
    { key: "confidence", header: "Confianza", width: 125, minWidth: 105, maxWidth: 200, kind: "short", render: (item) => <ConfidenceBadge value={item.recommendation_confidence} /> },
    { key: "reason", header: "Motivo", width: 360, minWidth: 220, maxWidth: 700, kind: "long", render: (item) => item.business_reason || item.main_message },
    { key: "next-action", header: "Siguiente acción", width: 190, minWidth: 150, maxWidth: 360, kind: "medium", render: (item) => safeNextAction(item) },
    { key: "detail", header: "Detalle", width: 240, minWidth: 190, maxWidth: 380, kind: "medium", render: (item) => <div className="row-actions"><button className="secondary-button compact-button" type="button" onClick={() => onSupport(item)}>Ver sustento</button><button className="secondary-button compact-button" type="button" onClick={() => item.item_code && onOpenItem(item.item_code)}>Ver diagnóstico</button></div> },
  ];

  return <ResizableTable rows={items} columns={columns} rowKey={(item) => `${item.item_code}-${item.warehouse_code}-${item.recommendation_type}`} storageKey="logistica-table-recommendations-columns" note="La tabla orienta decisiones. No crea documentos SAP ni automatiza compras." emptyMessage="No hay artículos para los filtros actuales del plan." />;
}

function safeNextAction(item: RecommendationRecord) {
  if (item.recommendation_type === "comprar") return "Validar con logística";
  if (item.recommendation_type === "acelerar_compra_abierta") return "Revisar documentos";
  if (item.recommendation_type === "trasladar_stock") return "Validar con logística";
  if (item.recommendation_type === "revisar_venta_comprometida") return "Revisar documentos";
  if (item.recommendation_type === "validar_datos") return "Validar datos";
  if (item.recommendation_type === "revisar_maestro_articulo") return "Revisar maestro";
  return "Monitorear";
}

function SupplyPriorityPanel({ items, onSupport }: { items: RecommendationRecord[]; onSupport: (item: RecommendationRecord) => void }) {
  return (
    <section className="supply-panel">
      <h3>Acciones prioritarias</h3>
      <div className="priority-list">
        {items.length ? items.map((item, index) => (
          <article key={`${item.item_code}-${item.warehouse_code}-${index}`} className="priority-item">
            <span>{index + 1}</span>
            <div>
              <strong>{item.item_name || item.item_code}</strong>
              <small>Cantidad sugerida: {formatNumber(item.suggested_quantity, 2)}</small>
            </div>
            <button className="secondary-button compact-button" type="button" onClick={() => onSupport(item)}>Ver sustento</button>
          </article>
        )) : <EmptyState message="Sin acciones prioritarias con los filtros actuales." />}
      </div>
    </section>
  );
}

function SupplyDistribution({ items }: { items: RecommendationRecord[] }) {
  const summary = buildSupplySummary(items);
  const total = Math.max(items.length, 1);
  const rows = [
    ["Abastecer ahora", summary.abastecer, "buy"],
    ["Revisar", summary.revisar, "review"],
    ["No comprar", summary.noComprar, "no-buy"],
    ["Monitorear", summary.monitorear, "monitor"],
  ] as const;
  return (
    <section className="supply-panel">
      <h3>Distribución de decisiones</h3>
      <div className="decision-bars">
        {rows.map(([label, value, tone]) => (
          <div className="decision-row" key={label}>
            <span>{label}</span>
            <div className="bar-track"><div className={`bar-fill decision-${tone}`} style={{ width: `${(value / total) * 100}%` }} /></div>
            <strong>{formatNumber(value)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function SupplySupportPanel({
  item,
  diagnosis,
  loading,
  error,
  onClose,
  onOpenItem,
}: {
  item: RecommendationRecord;
  diagnosis: ItemDiagnosis | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onOpenItem: (itemCode: string) => void;
}) {
  const audit = diagnosis?.auditoria_disponibilidad;
  const relatedCount = diagnosis
    ? diagnosis.documentos_sap_relacionados.ingresos_esperados.length
      + diagnosis.documentos_sap_relacionados.salidas_comprometidas.length
      + diagnosis.documentos_sap_relacionados.produccion_pendiente.length
      + diagnosis.documentos_sap_relacionados.traslados_pendientes.length
    : 0;
  return (
    <div className="support-overlay" role="dialog" aria-modal="true" aria-label="Sustento de recomendación">
      <aside className="support-panel">
        <div className="support-header">
          <div>
            <h3>Sustento de recomendación</h3>
            <p>{item.item_name || "Sin nombre"} / {item.item_code}</p>
          </div>
          <button className="secondary-button compact-button" type="button" onClick={onClose}>Cerrar</button>
        </div>
        <div className="support-body">
          <span className={`supply-action-pill ${supplyActionClass(item)}`}>{supplyActionLabel(item)}</span>
          <div className="support-kpis">
            <div><span>Cantidad referencial</span><strong>{formatNumber(item.suggested_quantity, 2)}</strong></div>
            <div><span>Riesgo</span><RiskBadge value={item.nivel_riesgo} /></div>
            <div><span>Confianza</span><ConfidenceBadge value={item.recommendation_confidence} /></div>
          </div>
          <section>
            <h4>Motivo</h4>
            <p>{item.business_reason}</p>
            <small>{item.priority_reasons?.join("; ") || item.main_message}</small>
          </section>
          <section>
            <h4>Advertencias</h4>
            <ul>
              <li>Cantidad referencial</li>
              <li>Requiere validación humana</li>
              <li>No genera documentos SAP</li>
              {item.data_quality_notes?.slice(0, 4).map((note) => <li key={note}>{note}</li>)}
            </ul>
          </section>
          {loading ? <LoadingState label="Cargando auditoría de disponibilidad..." /> : error ? <ErrorState message={error} /> : audit ? (
            <section className="support-audit">
              <h4>Auditoría de disponibilidad resumida</h4>
              <div className="support-grid">
                <div><span>Stock disponible</span><strong>{formatNumber(audit.stock_disponible, 2)}</strong></div>
                <div><span>Ingresos esperados</span><strong>{formatNumber(audit.ingresos_esperados, 2)}</strong></div>
                <div><span>Salidas comprometidas</span><strong>{formatNumber(audit.salidas_comprometidas, 2)}</strong></div>
                <div><span>Salidas proyectadas</span><strong>{formatNumber(audit.salidas_proyectadas, 2)}</strong></div>
                <div><span>Necesidad / exceso</span><strong>{formatNumber(audit.stock_final_estimado, 2)}</strong></div>
                <div><span>Documentos relacionados</span><strong>{formatNumber(relatedCount)}</strong></div>
              </div>
            </section>
          ) : null}
          <div className="support-actions">
            <button className="primary-button" type="button" onClick={() => item.item_code && onOpenItem(item.item_code)}>Ver diagnóstico por artículo</button>
            <button className="secondary-button" type="button" onClick={onClose}>Validar con logística</button>
          </div>
        </div>
      </aside>
    </div>
  );
}

function PurchaseCandidatesPage({ resource, onOpenItem }: { resource: CachedResource<PaginatedResponse<RecommendationRecord>>; onOpenItem: (itemCode: string) => void }) {
  const [filters, setFilters] = useState<RecommendationFilters & { vendor?: string }>({ limit: 50, offset: 0 });
  useEffect(() => {
    void loadPurchaseCandidatesPage(filters);
  }, [filters]);
  const rows = useMemo(() => {
    if (!resource.data) return [];
    return resource.data.items.filter((item) => {
      const vendor = filters.vendor?.toLowerCase();
      if (vendor && !`${item.preferred_vendor_code || ""} ${item.preferred_vendor_name || ""}`.toLowerCase().includes(vendor)) return false;
      if (filters.item_code && !String(item.item_code || "").includes(filters.item_code)) return false;
      if (filters.warehouse && !String(item.warehouse_code || "").includes(filters.warehouse)) return false;
      if (filters.priority_level && item.priority_level !== filters.priority_level) return false;
      if (filters.confidence_level && item.recommendation_confidence !== filters.confidence_level) return false;
      if (filters.risk_level && item.nivel_riesgo !== filters.risk_level) return false;
      return true;
    });
  }, [resource.data, filters]);
  const updatePage = ({ limit, offset }: { limit: number; offset: number }) => setFilters((current) => ({ ...current, limit, offset }));

  return (
    <div className="page-stack">
      <SectionHeader title="Compras sugeridas" subtitle="Candidatos referenciales de compra" icon={pageIcons.purchases} />
      <WarningBox>No genera orden de compra. Validar proveedor, minimo de compra, lead time y necesidad real antes de operar en SAP.</WarningBox>
      <FilterBar filters={filters} onChange={setFilters} showBooleans={false} vendorFilter />
      <ResourceNotice resource={resource} label="compras sugeridas" />
      {resource.status === "loading" && !resource.data ? <LoadingState label="Cargando página de compras sugeridas..." /> : <PurchaseTable items={rows} onOpenItem={onOpenItem} />}
      {resource.data ? <PaginationControls total={resource.data.total} limit={resource.data.limit} offset={resource.data.offset} hasNext={resource.data.has_next} hasPrevious={resource.data.has_previous} onChange={updatePage} /> : null}
    </div>
  );
}

function PurchaseTable({ items, onOpenItem }: { items: RecommendationRecord[]; onOpenItem: (itemCode: string) => void }) {
  const columns: ResizableTableColumn<RecommendationRecord>[] = [
    { key: "item", header: "Artículo", width: 220, minWidth: 150, maxWidth: 420, kind: "medium", render: (item) => <><button className="link-button" type="button" onClick={() => item.item_code && onOpenItem(item.item_code)}>{item.item_code || "-"}</button><small>{item.item_name || "Sin nombre"}</small></> },
    { key: "warehouse", header: "Almacén", width: 110, minWidth: 84, maxWidth: 180, kind: "short", render: (item) => item.warehouse_code || "-" },
    { key: "quantity", header: "Cantidad referencial", width: 155, minWidth: 120, maxWidth: 240, kind: "short", align: "right", render: (item) => `${formatNumber(item.suggested_quantity, 2)} ref.` },
    { key: "horizon", header: "Horizonte", width: 110, minWidth: 90, maxWidth: 180, kind: "short", align: "right", render: (item) => item.suggested_horizon_days ? `${item.suggested_horizon_days} días` : "-" },
    { key: "priority", header: "Prioridad", width: 120, minWidth: 100, maxWidth: 190, kind: "short", render: (item) => <PriorityBadge value={item.priority_level} /> },
    { key: "confidence", header: "Confianza", width: 125, minWidth: 105, maxWidth: 200, kind: "short", render: (item) => <ConfidenceBadge value={item.recommendation_confidence} /> },
    { key: "risk", header: "Riesgo", width: 115, minWidth: 95, maxWidth: 190, kind: "short", render: (item) => <RiskBadge value={item.nivel_riesgo} /> },
    { key: "vendor", header: "Proveedor", width: 220, minWidth: 150, maxWidth: 420, kind: "medium", render: (item) => item.preferred_vendor_name || item.preferred_vendor_code || "-" },
    { key: "lead-time", header: "Lead time", width: 110, minWidth: 90, maxWidth: 180, kind: "short", align: "right", render: (item) => item.estimated_lead_time_days ? `${formatNumber(item.estimated_lead_time_days)} días` : "-" },
    { key: "last-purchase", header: "Última compra", width: 180, minWidth: 140, maxWidth: 300, kind: "medium", render: (item) => <>{item.last_purchase_date || "-"}{item.last_purchase_price ? ` / ${formatNumber(item.last_purchase_price, 2)}` : ""}</> },
    { key: "reason", header: "Motivo", width: 360, minWidth: 220, maxWidth: 700, kind: "long", render: (item) => item.business_reason || item.main_message },
  ];

  return <ResizableTable rows={items} columns={columns} rowKey={(item) => `${item.item_code}-${item.warehouse_code}`} storageKey="logistica-table-purchases-columns" emptyMessage="No hay candidatos de compra para los filtros actuales." />;
}

function TransferCandidatesPage({ resource, onOpenItem }: { resource: CachedResource<PaginatedResponse<RecommendationRecord>>; onOpenItem: (itemCode: string) => void }) {
  const [filters, setFilters] = useState<RecommendationFilters>({ limit: 50, offset: 0 });
  useEffect(() => {
    void loadTransferCandidatesPage(filters);
  }, [filters]);
  const rows = useMemo(() => {
    if (!resource.data) return [];
    return resource.data.items.filter((item) => {
      if (filters.item_code && !String(item.item_code || "").includes(filters.item_code)) return false;
      if (filters.warehouse && !`${item.source_warehouse || ""} ${item.target_warehouse || ""}`.includes(filters.warehouse)) return false;
      if (filters.priority_level && item.priority_level !== filters.priority_level) return false;
      if (filters.confidence_level && item.recommendation_confidence !== filters.confidence_level) return false;
      if (filters.risk_level && item.nivel_riesgo !== filters.risk_level) return false;
      return true;
    });
  }, [resource.data, filters]);
  const updatePage = ({ limit, offset }: { limit: number; offset: number }) => setFilters((current) => ({ ...current, limit, offset }));

  return (
    <div className="page-stack">
      <SectionHeader title="Traslados sugeridos" subtitle="Candidatos referenciales de traslado interno" icon={pageIcons.transfers} />
      <WarningBox>No genera solicitud de traslado. Validar fisicamente disponibilidad y prioridad operativa antes de mover stock.</WarningBox>
      <FilterBar filters={filters} onChange={setFilters} showBooleans={false} />
      <ResourceNotice resource={resource} label="traslados sugeridos" />
      {resource.status === "loading" && !resource.data ? <LoadingState label="Cargando página de traslados sugeridos..." /> : <TransferTable items={rows} onOpenItem={onOpenItem} />}
      {resource.data ? <PaginationControls total={resource.data.total} limit={resource.data.limit} offset={resource.data.offset} hasNext={resource.data.has_next} hasPrevious={resource.data.has_previous} onChange={updatePage} /> : null}
    </div>
  );
}

function TransferTable({ items, onOpenItem }: { items: RecommendationRecord[]; onOpenItem: (itemCode: string) => void }) {
  if (!items.length) return <EmptyState message="No hay candidatos de traslado para los filtros actuales." />;
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Articulo</th>
            <th>Origen</th>
            <th>Destino</th>
            <th>Cantidad</th>
            <th>Stock origen antes</th>
            <th>Stock origen despues</th>
            <th>Stock destino antes</th>
            <th>Stock destino despues</th>
            <th>Prioridad</th>
            <th>Motivo</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.item_code}-${item.source_warehouse}-${item.target_warehouse}`}>
              <td><button className="link-button" type="button" onClick={() => item.item_code && onOpenItem(item.item_code)}>{item.item_code}</button><small>{item.item_name || "Sin nombre"}</small></td>
              <td>{item.source_warehouse || "-"}</td>
              <td>{item.target_warehouse || "-"}</td>
              <td>{formatNumber(item.transfer_candidate_quantity, 2)} ref.</td>
              <td>{formatNumber(item.source_projected_stock_before_transfer, 2)}</td>
              <td>{formatNumber(item.source_remaining_stock_after_transfer, 2)}</td>
              <td>{formatNumber(item.target_projected_stock_before_transfer, 2)}</td>
              <td>{formatNumber(item.target_projected_stock_after_transfer, 2)}</td>
              <td><PriorityBadge value={item.priority_level} /></td>
              <td>{item.transfer_reason || item.business_reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ValidationsPage({ resource, onOpenItem }: { resource: CachedResource<PaginatedActionsResponse>; onOpenItem: (itemCode: string) => void }) {
  const [pagination, setPagination] = useState({ limit: 50, offset: 0 });
  useEffect(() => {
    void loadActionsPage(pagination);
  }, [pagination]);
  const rows = useMemo(() => {
    if (!resource.data) return [];
    return [
      ...resource.data.items.articulos_para_validar_datos,
      ...resource.data.items.articulos_para_revisar_maestro,
      ...resource.data.items.ov_a_revisar,
      ...resource.data.items.oc_abiertas_a_acelerar,
    ];
  }, [resource.data]);

  return (
    <div className="page-stack">
      <SectionHeader title="Validaciones" subtitle="Casos que requieren limpieza, revision o analisis antes de comprar" icon={pageIcons.validations} />
      <WarningBox>Estos casos no deben convertirse en compra automatica. Primero validar datos, maestro, compromisos y partidas abiertas.</WarningBox>
      <ResourceNotice resource={resource} label="validaciones" />
      {resource.status === "loading" && !resource.data ? <LoadingState label="Cargando página de validaciones..." /> : <ValidationList items={rows} onOpenItem={onOpenItem} />}
      {resource.data ? <PaginationControls total={resource.data.total} limit={resource.data.limit} offset={resource.data.offset} hasNext={resource.data.has_next} hasPrevious={resource.data.has_previous} onChange={setPagination} /> : null}
    </div>
  );
}

function ValidationList({ items, onOpenItem }: { items: RecommendationRecord[]; onOpenItem: (itemCode: string) => void }) {
  if (!items.length) return <EmptyState message="No hay validaciones pendientes en la muestra actual." />;
  return (
    <div className="validation-list">
      {items.slice(0, 300).map((item) => (
        <article className="validation-row" key={`${item.item_code}-${item.warehouse_code}-${item.recommendation_type}`}>
          <div className="row-icon"><ActionIcon type={item.recommendation_type} /></div>
          <div>
            <button className="link-button" type="button" onClick={() => item.item_code && onOpenItem(item.item_code)}>{item.item_code}</button>
            <p>{item.item_name || "Sin nombre"} / {item.warehouse_code || "-"}</p>
          </div>
          <RecommendationTypeBadge value={item.recommendation_type} />
          <StatusBadge value={item.recommendation_status} />
          <p>{item.next_action_label}: {item.next_action_description}</p>
          <small>{item.data_quality_notes?.join("; ") || item.technical_reason}</small>
        </article>
      ))}
    </div>
  );
}

function ItemDiagnosisPage({ initialItem }: { initialItem: string | null }) {
  const [itemCode, setItemCode] = useState(initialItem || "");
  const [warehouse, setWarehouse] = useState("");
  const [submitted, setSubmitted] = useState({ itemCode: initialItem || "", warehouse: "" });
  useEffect(() => {
    if (initialItem) {
      setItemCode(initialItem);
      setSubmitted((current) => ({ ...current, itemCode: initialItem }));
      void loadItemDiagnosis(initialItem, warehouse || undefined);
    }
  }, [initialItem]);
  const diagnosis = submitted.itemCode ? getCachedItemDiagnosis(submitted.itemCode, submitted.warehouse || undefined) : null;
  const submitDiagnosis = (force = false) => {
    const next = { itemCode: itemCode.trim(), warehouse: warehouse.trim() };
    setSubmitted(next);
    if (next.itemCode) void loadItemDiagnosis(next.itemCode, next.warehouse || undefined, force);
  };
  const data = diagnosis?.data || null;
  const loading = diagnosis?.status === "loading";
  const error = diagnosis?.error || null;

  return (
    <div className="page-stack">
      <SectionHeader title="Diagnóstico por artículo" subtitle="Kardex proyectado y auditoría de disponibilidad" icon={pageIcons.diagnosis} />
      <WarningBox>Cantidad referencial. Requiere validación humana. No genera documentos SAP.</WarningBox>
      <form className="search-panel diagnosis-search" onSubmit={(event) => { event.preventDefault(); submitDiagnosis(false); }}>
        <button className="secondary-button" type="button" disabled={!submitted.itemCode} onClick={() => submitDiagnosis(true)}>Actualizar diagnóstico</button>
        <label>
          <span>Código de artículo</span>
          <input value={itemCode} onChange={(event) => setItemCode(event.target.value)} placeholder="Ej. 100100001" />
        </label>
        <label>
          <span>Almacén opcional</span>
          <input value={warehouse} onChange={(event) => setWarehouse(event.target.value)} placeholder="Ej. PL01" />
        </label>
        <button className="primary-button" type="submit">Ver diagnóstico</button>
      </form>
      {!submitted.itemCode ? <EmptyState message="Ingresa un código de artículo para consultar el diagnóstico." /> : loading ? <LoadingState /> : error ? <ErrorState message={error} /> : data ? <ItemDiagnosisDetail data={data} /> : <EmptyState />}
    </div>
  );
}

function ItemDiagnosisDetail({ data }: { data: ItemDiagnosis }) {
  const recommendation = data.recomendacion_principal;
  const actionNeeded = data.auditoria_disponibilidad.cantidad_sugerida > 0;

  return (
    <div className="diagnosis-detail">
      <section className="diagnosis-summary">
        <div>
          <span className="summary-eyebrow">Artículo evaluado</span>
          <h3>{data.item.item_name || "Sin nombre"}</h3>
          <p>Código del artículo: <strong>{data.item.item_code}</strong>{data.item.warehouse ? ` / Almacén ${data.item.warehouse}` : ""}</p>
        </div>
        <div className="summary-actions">
          <span className={actionNeeded ? "action-pill action-danger" : "action-pill action-neutral"}>{actionNeeded ? "Abastecer ahora" : "Monitorear"}</span>
          <RiskBadge value={data.riesgo} />
          <ConfidenceBadge value={data.confianza} />
          <strong>{formatNumber(data.cantidad_sugerida, 2)} un ref.</strong>
        </div>
      </section>

      <div className="diagnosis-grid">
        <section className="diagnosis-panel diagnosis-wide">
          <div className="panel-title-row">
            <div>
              <h3>Kardex proyectado</h3>
              <p>Los movimientos proyectados no están registrados en SAP; se muestran como apoyo a la decisión.</p>
            </div>
          </div>
          <KardexTable rows={data.kardex_proyectado} />
        </section>

        <AvailabilityAuditCard data={data} />
      </div>

      <div className="diagnosis-grid lower-grid">
        <section className="diagnosis-panel">
          <h3>Proyección del artículo</h3>
          <ProjectedBalanceChart rows={data.kardex_proyectado} />
        </section>
        <section className="diagnosis-panel">
          <h3>Trazabilidad de la recomendación</h3>
          <TraceabilityBlock data={data} />
        </section>
        <section className="diagnosis-panel">
          <h3>Documentos SAP relacionados</h3>
          <RelatedDocumentsBlock data={data} />
        </section>
      </div>

      {recommendation ? <RecommendationTable items={[recommendation]} compact /> : null}
    </div>
  );
}

function AvailabilityAuditCard({ data }: { data: ItemDiagnosis }) {
  const audit = data.auditoria_disponibilidad;
  return (
    <section className="diagnosis-panel audit-panel">
      <h3>Auditoría de disponibilidad</h3>
      <div className="audit-lines">
        {audit.formula_lines.map((line) => (
          <div className="audit-line" key={`${line.operator}-${line.label}`}>
            <span>{line.operator}</span>
            <p>{line.label}</p>
            <strong className={line.value < 0 ? "negative" : ""}>{formatNumber(line.value, 2)}</strong>
          </div>
        ))}
      </div>
      <div className="audit-result">
        <span>Resultado estimado</span>
        <strong className={audit.stock_final_estimado < 0 ? "negative" : "positive"}>{formatNumber(audit.stock_final_estimado, 2)}</strong>
      </div>
      <div className="suggested-quantity">
        <span>Cantidad referencial</span>
        <strong>{formatNumber(audit.cantidad_sugerida, 2)} un</strong>
      </div>
      <p className="audit-note">Requiere validación humana. No genera documentos SAP.</p>
    </section>
  );
}

function KardexTable({ rows }: { rows: ProjectedKardexLine[] }) {
  if (!rows.length) return <EmptyState message="Sin movimientos para el Kardex proyectado." />;
  return (
    <div className="table-wrap kardex-wrap">
      <table className="data-table kardex-table">
        <thead>
          <tr>
            <th>Fecha / periodo</th>
            <th>Tipo de movimiento</th>
            <th>Documento / referencia</th>
            <th>Almacén</th>
            <th>Entrada</th>
            <th>Salida</th>
            <th>Saldo estimado</th>
            <th>Origen</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.sort_key}-${index}`} className={row.origen === "Diagnóstico" ? "diagnosis-total-row" : ""}>
              <td>{row.fecha_periodo || "-"}</td>
              <td>{row.tipo_movimiento}<small>{row.nota || ""}</small></td>
              <td>{row.documento_referencia || "-"}</td>
              <td>{row.almacen || "-"}</td>
              <td className="positive">{row.entrada ? formatNumber(row.entrada, 2) : "-"}</td>
              <td className="negative">{row.salida ? formatNumber(row.salida, 2) : "-"}</td>
              <td className={row.saldo_estimado < 0 ? "negative" : ""}>{formatNumber(row.saldo_estimado, 2)}</td>
              <td><span className={`origin-badge ${originClass(row.origen)}`}>{row.origen}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function originClass(origin: string) {
  if (origin === "SAP real") return "origin-real";
  if (origin === "SAP abierto") return "origin-open";
  if (origin === "Proyección") return "origin-projected";
  if (origin === "Diagnóstico") return "origin-diagnosis";
  return "origin-recommendation";
}

function ProjectedBalanceChart({ rows }: { rows: ProjectedKardexLine[] }) {
  const points = rows
    .filter((row) => Number.isFinite(row.saldo_estimado))
    .slice(-10)
    .map((row) => ({ label: row.fecha_periodo || row.origen, value: row.saldo_estimado, projected: row.origen !== "SAP real" }));
  if (points.length < 2) return <EmptyState message="Sin puntos suficientes para proyectar." />;
  const width = 640;
  const height = 230;
  const padding = 32;
  const values = points.map((point) => point.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;
  const coords = points.map((point, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(points.length - 1, 1);
    const y = height - padding - ((point.value - min) / range) * (height - padding * 2);
    return { ...point, x, y };
  });
  const polyline = coords.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="chart-box">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Proyección de saldo estimado">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} />
        <polyline points={polyline} />
        {coords.map((point) => (
          <g key={`${point.label}-${point.x}`}>
            <circle cx={point.x} cy={point.y} r={4.5} className={point.projected ? "projected-point" : ""} />
            <text x={point.x} y={point.y - 10}>{formatNumber(point.value, 0)}</text>
          </g>
        ))}
      </svg>
      <div className="chart-labels">
        {coords.map((point) => <span key={point.label}>{point.label}</span>)}
      </div>
    </div>
  );
}

function TraceabilityBlock({ data }: { data: ItemDiagnosis }) {
  const trace = data.trazabilidad;
  const traceItems = [
    ...trace.motivos_recomendacion,
    ...trace.motivos_riesgo,
    ...trace.notas_calidad_datos,
    ...trace.advertencias,
  ].filter((item): item is string => Boolean(item)).slice(0, 8);

  return (
    <div className="traceability">
      <p>{trace.mensaje_principal}</p>
      <div className="formula-strip">
        {trace.formula_resumen.map((line) => (
          <span key={`${line.operator}-${line.label}`}>{line.operator} {formatNumber(line.value, 0)}</span>
        ))}
      </div>
      <strong>{trace.siguiente_accion}</strong>
      <ul>
        {traceItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function RelatedDocumentsBlock({ data }: { data: ItemDiagnosis }) {
  const groups: Array<[string, RelatedDocument[]]> = [
    ["Ingresos esperados", data.documentos_sap_relacionados.ingresos_esperados],
    ["Salidas comprometidas", data.documentos_sap_relacionados.salidas_comprometidas],
    ["Producción pendiente", data.documentos_sap_relacionados.produccion_pendiente],
    ["Traslados pendientes", data.documentos_sap_relacionados.traslados_pendientes],
  ];
  return (
    <div className="related-docs">
      {groups.map(([title, documents]) => (
        <div className="doc-group" key={title}>
          <div>
            <strong>{title}</strong>
            <span>{formatNumber(documents.reduce((sum, doc) => sum + doc.cantidad_abierta, 0), 2)} un</span>
          </div>
          {documents.length ? documents.slice(0, 4).map((doc) => <RelatedDocumentRow key={`${title}-${doc.numero_documento}-${doc.almacen}`} doc={doc} />) : <small>Sin documentos abiertos.</small>}
        </div>
      ))}
    </div>
  );
}

function RelatedDocumentRow({ doc }: { doc: RelatedDocument }) {
  return (
    <div className="doc-row">
      <span>{doc.numero_documento || "-"}</span>
      <span>{doc.fecha_esperada || doc.fecha || "-"}</span>
      <span>{doc.tipo_funcional}</span>
      <strong>{formatNumber(doc.cantidad_abierta, 2)}</strong>
    </div>
  );
}

function AdvancedAnalysisPage({ appData }: { appData: AppDataState }) {
  const summary = appData.recommendationsSummary;
  const risk = appData.coverageRiskSummary;
  const stock = appData.stockSummary;
  const warehouses = appData.recommendationsWarehouses;

  if ((summary.status === "loading" || risk.status === "loading" || stock.status === "loading") && (!summary.data || !risk.data || !stock.data)) return <LoadingState />;
  if (!summary.data || !risk.data || !stock.data) return <EmptyState />;

  return (
    <div className="page-stack">
      <SectionHeader title="Analisis avanzado" subtitle="Vista tecnica resumida para analisis de cobertura, prioridad y almacenes" icon={pageIcons.advanced} />
      <ResourceNotice resource={summary} label="resumen de recomendaciones" />
      <ResourceNotice resource={risk} label="riesgo de quiebre" />
      <ResourceNotice resource={stock} label="inventario actual" />
      <ResourceNotice resource={warehouses} label="resumen por almacén" />
      <div className="kpi-grid">
        <KpiCard title="Combinaciones riesgo" value={risk.data.total_combinaciones_evaluadas} />
        <KpiCard title="Riesgo critico" value={risk.data.riesgo_critico} tone="danger" />
        <KpiCard title="Stock fisico total" value={formatNumber(stock.data.stock_fisico_total, 2)} />
        <KpiCard title="Almacenes stock" value={stock.data.total_warehouses} />
      </div>
      <div className="dashboard-grid">
        <DistributionList title="Prioridad" values={summary.data.cantidad_por_prioridad} />
        <DistributionList title="Tipo de recomendacion" values={summary.data.cantidad_por_tipo} />
        <DistributionList title="Confianza" values={summary.data.cantidad_por_confianza} />
      </div>
      <WarehouseTable items={warehouses.data || []} />
    </div>
  );
}

function WarehouseTable({ items }: { items: WarehouseRecommendationSummary[] }) {
  if (!items.length) return <EmptyState message="Sin resumen por almacen." />;
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Almacen</th>
            <th>Urgentes</th>
            <th>Altas</th>
            <th>Compras</th>
            <th>Traslados</th>
            <th>Validaciones</th>
            <th>Sin accion</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.warehouse_code || "sin-almacen"}>
              <td>{item.warehouse_code}<small>{item.warehouse_name || ""}</small></td>
              <td>{formatNumber(item.recomendaciones_urgentes)}</td>
              <td>{formatNumber(item.recomendaciones_altas)}</td>
              <td>{formatNumber(item.compras_sugeridas)}</td>
              <td>{formatNumber(item.traslados_sugeridos)}</td>
              <td>{formatNumber(item.validaciones_datos)}</td>
              <td>{formatNumber(item.articulos_sin_accion)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function App() {
  const appData = useAppData();
  const [page, setPage] = useState<PageKey>("inicio");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [navigationOpen, setNavigationOpen] = useState(false);
  const openItem = (itemCode: string) => {
    setSelectedItem(itemCode);
    setPage("diagnostico");
    setNavigationOpen(false);
  };
  const navigateTo = (nextPage: PageKey) => {
    setPage(nextPage);
    setNavigationOpen(false);
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar${navigationOpen ? " sidebar-open" : ""}`} aria-label="Navegación principal">
        <div className="brand">
          <div className="brand-mark">LP</div>
          <div>
            <strong>Logistica Predictiva</strong>
            <span>SAP B1 V2</span>
          </div>
          <button className="sidebar-close" type="button" aria-label="Cerrar menú" onClick={() => setNavigationOpen(false)}>Cerrar</button>
        </div>
        <nav>
          {navItems.map((item) => (
            <button key={item.key} type="button" className={page === item.key ? "active" : ""} onClick={() => navigateTo(item.key)}>
              {item.key === "inicio" && pageIcons.home}
              {item.key === "recomendaciones" && pageIcons.recommendations}
              {item.key === "compras" && pageIcons.purchases}
              {item.key === "traslados" && pageIcons.transfers}
              {item.key === "validaciones" && pageIcons.validations}
              {item.key === "diagnostico" && pageIcons.diagnosis}
              {item.key === "analisis" && pageIcons.advanced}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <button
        className={`navigation-overlay${navigationOpen ? " navigation-overlay-visible" : ""}`}
        type="button"
        aria-label="Cerrar menú de navegación"
        tabIndex={navigationOpen ? 0 : -1}
        onClick={() => setNavigationOpen(false)}
      />
      <main className="content">
        <header className="mobile-topbar">
          <button className="menu-toggle" type="button" aria-expanded={navigationOpen} onClick={() => setNavigationOpen(true)}>
            Menú
          </button>
          <div>
            <strong>Logística Predictiva</strong>
            <span>Portal operativo</span>
          </div>
        </header>
        <DataRefreshBar appData={appData} />
        {page === "inicio" && <DashboardPage summary={appData.recommendationsSummary} lastUpdated={appData.lastUpdated} onNavigate={navigateTo} />}
        {page === "recomendaciones" && <RecommendationsPage appData={appData} onOpenItem={openItem} />}
        {page === "compras" && <PurchaseCandidatesPage resource={appData.purchaseCandidates} onOpenItem={openItem} />}
        {page === "traslados" && <TransferCandidatesPage resource={appData.transferCandidates} onOpenItem={openItem} />}
        {page === "validaciones" && <ValidationsPage resource={appData.recommendationsActions} onOpenItem={openItem} />}
        {page === "diagnostico" && <ItemDiagnosisPage initialItem={selectedItem} />}
        {page === "analisis" && <AdvancedAnalysisPage appData={appData} />}
      </main>
    </div>
  );
}

function DataRefreshBar({ appData }: { appData: AppDataState }) {
  const lastUpdated = appData.lastUpdated ? new Date(appData.lastUpdated).toLocaleString("es-PE") : "Sin actualización";
  const hasPartialErrors = [
    appData.recommendationsSummary,
    appData.recommendationsItems,
    appData.recommendationsActions,
    appData.purchaseCandidates,
    appData.transferCandidates,
    appData.coverageRiskSummary,
    appData.stockSummary,
    appData.recommendationsWarehouses,
  ].some((resource) => resource.error);

  return (
    <div className="data-refresh-bar">
      <div>
        <strong>{appData.isLoading ? "Actualizando datos..." : "Datos en memoria"}</strong>
        <span>Última actualización: {lastUpdated}</span>
        {hasPartialErrors ? <small>Se muestran datos disponibles; algunos bloques tienen error.</small> : null}
      </div>
      <button className="secondary-button" type="button" disabled={appData.isLoading} onClick={() => void loadInitialAppData(true)}>
        Actualizar datos
      </button>
    </div>
  );
}
