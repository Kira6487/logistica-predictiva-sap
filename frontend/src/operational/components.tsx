import {
  AlertTriangle,
  ArrowRightLeft,
  BarChart3,
  Boxes,
  CheckCircle2,
  CircleHelp,
  ClipboardCheck,
  DatabaseZap,
  Eye,
  FileWarning,
  Loader2,
  PackageCheck,
  Search,
  ShieldAlert,
  ShoppingCart,
} from "lucide-react";
import type { ReactNode } from "react";
import type { RecommendationFilters, RecommendationRecord } from "./types";

export const RECOMMENDATION_TYPES = [
  "comprar",
  "acelerar_compra_abierta",
  "trasladar_stock",
  "revisar_venta_comprometida",
  "monitorear",
  "no_comprar",
  "validar_datos",
  "revisar_maestro_articulo",
  "sin_recomendacion",
];

export const PRIORITY_LEVELS = ["urgente", "alta", "media", "baja", "informativa"];
export const RISK_LEVELS = ["critico", "alto", "medio", "bajo", "sin_riesgo_aparente", "sin_diagnostico"];
export const CONFIDENCE_LEVELS = ["alta", "media", "baja", "sin_confianza"];
export const STATUS_LEVELS = ["accion_recomendada", "requiere_validacion", "solo_monitoreo", "no_accion", "datos_insuficientes"];

const labelMap: Record<string, string> = {
  comprar: "Abastecer ahora",
  acelerar_compra_abierta: "Revisar ingresos esperados",
  trasladar_stock: "Evaluar traslado",
  revisar_venta_comprometida: "Revisar salidas comprometidas",
  monitorear: "Monitorear",
  no_comprar: "No comprar",
  validar_datos: "Validar datos",
  revisar_maestro_articulo: "Revisar maestro",
  sin_recomendacion: "Monitorear",
  accion_recomendada: "Accion sugerida",
  requiere_validacion: "Requiere validacion",
  solo_monitoreo: "Solo monitoreo",
  no_accion: "Sin accion",
  datos_insuficientes: "Datos insuficientes",
  sin_riesgo_aparente: "Sin riesgo",
  sin_diagnostico: "Sin diagnostico",
  sin_confianza: "Sin confianza",
};

export function formatLabel(value: string | null | undefined) {
  if (!value) return "Sin dato";
  return labelMap[value] || value.replace(/_/g, " ");
}

export function formatNumber(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("es-PE", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
}

export function KpiCard({ title, value, tone = "neutral", icon }: { title: string; value: number | string; tone?: string; icon?: ReactNode }) {
  return (
    <section className={`kpi kpi-${tone}`}>
      <div className="kpi-icon">{icon || <BarChart3 size={18} />}</div>
      <div>
        <p>{title}</p>
        <strong>{typeof value === "number" ? formatNumber(value) : value}</strong>
      </div>
    </section>
  );
}

function Badge({ children, tone }: { children: ReactNode; tone: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function PriorityBadge({ value }: { value: string }) {
  const tone = value === "urgente" ? "danger" : value === "alta" ? "orange" : value === "media" ? "amber" : value === "baja" ? "blue" : "muted";
  return <Badge tone={tone}>{formatLabel(value)}</Badge>;
}

export function RiskBadge({ value }: { value: string }) {
  const tone = value === "critico" ? "danger" : value === "alto" ? "orange" : value === "medio" ? "amber" : value === "bajo" ? "blue" : "muted";
  return <Badge tone={tone}>{formatLabel(value)}</Badge>;
}

export function ConfidenceBadge({ value }: { value: string | null }) {
  const tone = value === "alta" ? "success" : value === "media" ? "blue" : value === "baja" ? "amber" : "muted";
  return <Badge tone={tone}>{formatLabel(value)}</Badge>;
}

export function StatusBadge({ value }: { value: string }) {
  const tone = value === "accion_recomendada" ? "success" : value === "requiere_validacion" ? "amber" : value === "datos_insuficientes" ? "muted" : "blue";
  return <Badge tone={tone}>{formatLabel(value)}</Badge>;
}

export function RecommendationTypeBadge({ value }: { value: string }) {
  const tone =
    value === "comprar"
      ? "success"
      : value === "trasladar_stock"
        ? "blue"
        : value === "validar_datos" || value === "revisar_maestro_articulo"
          ? "amber"
          : value === "revisar_venta_comprometida"
            ? "orange"
            : "muted";
  return <Badge tone={tone}>{formatLabel(value)}</Badge>;
}

export function WarningBox({ children, icon = <ShieldAlert size={18} /> }: { children: ReactNode; icon?: ReactNode }) {
  return (
    <div className="warning-box">
      {icon}
      <span>{children}</span>
    </div>
  );
}

export function LoadingState({ label = "Cargando datos del backend..." }: { label?: string }) {
  return (
    <div className="state-panel">
      <Loader2 className="spin" size={20} />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state-panel state-error">
      <AlertTriangle size={20} />
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ message = "No hay datos para los filtros seleccionados." }: { message?: string }) {
  return (
    <div className="state-panel">
      <CircleHelp size={20} />
      <span>{message}</span>
    </div>
  );
}

export function SectionHeader({ title, subtitle, icon }: { title: string; subtitle?: string; icon?: ReactNode }) {
  return (
    <header className="section-header">
      <div className="section-title">
        {icon}
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
    </header>
  );
}

function SelectFilter({
  label,
  value,
  values,
  onChange,
}: {
  label: string;
  value?: string;
  values: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select value={value || ""} onChange={(event) => onChange(event.target.value)}>
        <option value="">Todos</option>
        {values.map((item) => (
          <option key={item} value={item}>
            {formatLabel(item)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function FilterBar({
  filters,
  onChange,
  showBooleans = true,
  vendorFilter = false,
}: {
  filters: RecommendationFilters & { vendor?: string };
  onChange: (filters: RecommendationFilters & { vendor?: string }) => void;
  showBooleans?: boolean;
  vendorFilter?: boolean;
}) {
  const update = (key: string, value: string | boolean) => onChange({ ...filters, [key]: value || undefined });
  return (
    <div className="filter-bar">
      <label className="filter-field">
        <span>Articulo</span>
        <div className="input-icon">
          <Search size={15} />
          <input value={filters.item_code || ""} onChange={(event) => update("item_code", event.target.value)} placeholder="Codigo" />
        </div>
      </label>
      <label className="filter-field">
        <span>Almacen</span>
        <input value={filters.warehouse || ""} onChange={(event) => update("warehouse", event.target.value)} placeholder="Codigo almacen" />
      </label>
      {vendorFilter ? (
        <label className="filter-field">
          <span>Proveedor</span>
          <input value={filters.vendor || ""} onChange={(event) => update("vendor", event.target.value)} placeholder="Nombre o codigo" />
        </label>
      ) : null}
      <SelectFilter label="Accion recomendada" value={filters.recommendation_type} values={RECOMMENDATION_TYPES} onChange={(value) => update("recommendation_type", value)} />
      <SelectFilter label="Estado" value={filters.recommendation_status} values={STATUS_LEVELS} onChange={(value) => update("recommendation_status", value)} />
      <SelectFilter label="Prioridad" value={filters.priority_level} values={PRIORITY_LEVELS} onChange={(value) => update("priority_level", value)} />
      <SelectFilter label="Riesgo" value={filters.risk_level} values={RISK_LEVELS} onChange={(value) => update("risk_level", value)} />
      <SelectFilter label="Confianza" value={filters.confidence_level} values={CONFIDENCE_LEVELS} onChange={(value) => update("confidence_level", value)} />
      {showBooleans ? (
        <div className="filter-checks">
          <label><input type="checkbox" checked={Boolean(filters.only_actionable)} onChange={(event) => update("only_actionable", event.target.checked)} /> Accionables</label>
          <label><input type="checkbox" checked={Boolean(filters.only_purchase_suggestions)} onChange={(event) => update("only_purchase_suggestions", event.target.checked)} /> Compras</label>
          <label><input type="checkbox" checked={Boolean(filters.only_transfer_suggestions)} onChange={(event) => update("only_transfer_suggestions", event.target.checked)} /> Traslados</label>
          <label><input type="checkbox" checked={Boolean(filters.only_data_validation)} onChange={(event) => update("only_data_validation", event.target.checked)} /> Validar datos</label>
        </div>
      ) : null}
    </div>
  );
}

export function RecommendationDetailPanel({ item }: { item: RecommendationRecord }) {
  return (
    <div className="detail-panel">
      <div>
        <h3>{item.main_message}</h3>
        <p>{item.business_reason}</p>
      </div>
      <div className="detail-grid">
        <div>
          <span>Razon tecnica</span>
          <p>{item.technical_reason}</p>
        </div>
        <div>
          <span>Siguiente accion</span>
          <p>{item.next_action_label}: {item.next_action_description}</p>
        </div>
        <div>
          <span>Notas de calidad</span>
          <p>{item.data_quality_notes?.length ? item.data_quality_notes.join("; ") : "Sin notas adicionales"}</p>
        </div>
        <div>
          <span>Motivos de prioridad</span>
          <p>{item.priority_reasons?.length ? item.priority_reasons.join("; ") : "Sin motivos adicionales"}</p>
        </div>
      </div>
      <WarningBox>Cantidad referencial. Requiere validacion humana. No genera documentos SAP.</WarningBox>
    </div>
  );
}

export function RecommendationTable({
  items,
  onSelect,
  selectedItem,
  compact = false,
}: {
  items: RecommendationRecord[];
  onSelect?: (itemCode: string) => void;
  selectedItem?: string | null;
  compact?: boolean;
}) {
  if (!items.length) return <EmptyState />;
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Articulo</th>
            <th>Almacen</th>
            <th>Tipo</th>
            <th>Estado</th>
            <th>Prioridad</th>
            <th>Riesgo</th>
            <th>Confianza</th>
            <th>Mensaje</th>
            <th>Cantidad</th>
            <th>Accion</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const key = `${item.item_code}-${item.warehouse_code}-${item.recommendation_type}`;
            const selected = selectedItem === key;
            return (
              <tr key={key} className={selected ? "selected-row" : ""}>
                <td>
                  <button className="link-button" type="button" onClick={() => item.item_code && onSelect?.(item.item_code)}>
                    <Eye size={14} /> {item.item_code || "-"}
                  </button>
                  <small>{item.item_name || "Sin nombre"}</small>
                </td>
                <td>{item.warehouse_code || "-"}</td>
                <td><RecommendationTypeBadge value={item.recommendation_type} /></td>
                <td><StatusBadge value={item.recommendation_status} /></td>
                <td><PriorityBadge value={item.priority_level} /> <small>{formatNumber(item.priority_score)}</small></td>
                <td><RiskBadge value={item.nivel_riesgo} /></td>
                <td><ConfidenceBadge value={item.recommendation_confidence} /></td>
                <td>{item.main_message}</td>
                <td>{item.suggested_quantity > 0 ? `${formatNumber(item.suggested_quantity, 2)} ref.` : "-"}</td>
                <td>{item.next_action_label}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {!compact ? <p className="table-note">Vista limitada por filtros enviados al backend para evitar renderizar miles de filas.</p> : null}
    </div>
  );
}

export function ActionIcon({ type }: { type: string }) {
  if (type === "comprar") return <ShoppingCart size={18} />;
  if (type === "trasladar_stock") return <ArrowRightLeft size={18} />;
  if (type === "validar_datos") return <FileWarning size={18} />;
  if (type === "revisar_maestro_articulo") return <DatabaseZap size={18} />;
  if (type === "no_comprar") return <CheckCircle2 size={18} />;
  if (type === "monitorear") return <BarChart3 size={18} />;
  return <ClipboardCheck size={18} />;
}

export const pageIcons = {
  home: <Boxes size={18} />,
  recommendations: <ClipboardCheck size={18} />,
  purchases: <ShoppingCart size={18} />,
  transfers: <ArrowRightLeft size={18} />,
  validations: <FileWarning size={18} />,
  diagnosis: <Search size={18} />,
  advanced: <BarChart3 size={18} />,
  stock: <PackageCheck size={18} />,
};
