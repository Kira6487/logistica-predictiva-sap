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
  ShoppingCart,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
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

type TableColumnKind = "short" | "medium" | "long";

export interface ResizableTableColumn<T> {
  key: string;
  header: string;
  width: number;
  minWidth: number;
  maxWidth?: number;
  kind?: TableColumnKind;
  align?: "left" | "center" | "right";
  render: (row: T) => ReactNode;
}

interface ResizableTableProps<T> {
  rows: T[];
  columns: ResizableTableColumn<T>[];
  rowKey: (row: T, index: number) => string;
  storageKey: string;
  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string | undefined;
  note?: ReactNode;
  emptyMessage?: string;
}

type ResizeState = { key: string; startX: number; startWidth: number } | null;

function clampWidth(column: Pick<ResizableTableColumn<unknown>, "minWidth" | "maxWidth">, width: number) {
  return Math.min(column.maxWidth ?? Number.POSITIVE_INFINITY, Math.max(column.minWidth, width));
}

function readStoredWidths<T>(storageKey: string, columns: ResizableTableColumn<T>[]) {
  if (typeof window === "undefined") return {};
  try {
    const stored = JSON.parse(window.localStorage.getItem(storageKey) || "{}");
    if (!stored || typeof stored !== "object") return {};
    return Object.fromEntries(
      columns
        .filter((column) => typeof stored[column.key] === "number" && Number.isFinite(stored[column.key]))
        .map((column) => [column.key, clampWidth(column, stored[column.key])]),
    ) as Record<string, number>;
  } catch {
    return {};
  }
}

export function ResizableTable<T>({
  rows,
  columns,
  rowKey,
  storageKey,
  onRowClick,
  rowClassName,
  note,
  emptyMessage,
}: ResizableTableProps<T>) {
  const defaultWidths = useMemo(
    () => Object.fromEntries(columns.map((column) => [column.key, column.width])) as Record<string, number>,
    [columns.map((column) => `${column.key}:${column.width}`).join("|")],
  );
  const columnSignature = columns.map((column) => `${column.key}:${column.width}:${column.minWidth}:${column.maxWidth ?? ""}`).join("|");
  const columnMap = useMemo(() => new Map(columns.map((column) => [column.key, column])), [columnSignature]);
  const [widths, setWidths] = useState<Record<string, number>>(() => ({
    ...defaultWidths,
    ...readStoredWidths(storageKey, columns),
  }));
  const [resizeState, setResizeState] = useState<ResizeState>(null);
  const resizeStateRef = useRef<ResizeState>(null);

  useEffect(() => {
    setWidths((current) => ({
      ...defaultWidths,
      ...Object.fromEntries(
        columns
          .filter((column) => current[column.key] !== undefined)
          .map((column) => [column.key, clampWidth(column, current[column.key])]),
      ),
    }));
  }, [columnMap, columnSignature, defaultWidths]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(widths));
    } catch {
      // Storage can be unavailable in private browsing or locked-down environments.
    }
  }, [storageKey, widths]);

  useEffect(() => {
    resizeStateRef.current = resizeState;
    if (!resizeState) return;

    const handlePointerMove = (event: globalThis.PointerEvent) => {
      const active = resizeStateRef.current;
      if (!active) return;
      const column = columnMap.get(active.key);
      if (!column) return;
      const nextWidth = clampWidth(column, active.startWidth + event.clientX - active.startX);
      setWidths((current) => ({ ...current, [active.key]: nextWidth }));
    };
    const stopResizing = () => setResizeState(null);

    document.body.classList.add("is-resizing-columns");
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopResizing);
    window.addEventListener("pointercancel", stopResizing);
    return () => {
      document.body.classList.remove("is-resizing-columns");
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopResizing);
      window.removeEventListener("pointercancel", stopResizing);
    };
  }, [columnMap, resizeState]);

  const beginResize = (event: PointerEvent<HTMLSpanElement>, column: ResizableTableColumn<T>) => {
    if (event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    setResizeState({ key: column.key, startX: event.clientX, startWidth: widths[column.key] ?? column.width });
  };

  const adjustWithKeyboard = (event: KeyboardEvent<HTMLSpanElement>, column: ResizableTableColumn<T>) => {
    const currentWidth = widths[column.key] ?? column.width;
    const step = event.shiftKey ? 40 : 16;
    let nextWidth: number | null = null;
    if (event.key === "ArrowLeft") nextWidth = currentWidth - step;
    if (event.key === "ArrowRight") nextWidth = currentWidth + step;
    if (event.key === "Home") nextWidth = column.minWidth;
    if (event.key === "End" && column.maxWidth) nextWidth = column.maxWidth;
    if (nextWidth === null) return;
    event.preventDefault();
    setWidths((current) => ({ ...current, [column.key]: clampWidth(column, nextWidth!) }));
  };

  const resetWidths = () => setWidths(defaultWidths);

  if (!rows.length) return <EmptyState message={emptyMessage} />;

  return (
    <div className="table-wrap">
      <div className="table-utility" aria-live="polite">
        <span>Arrastra los divisores de los encabezados para ajustar el ancho.</span>
        <div className="table-utility-actions">
          <span className="table-utility-key">Preferencias guardadas en este navegador</span>
          <button className="table-reset-button" type="button" onClick={resetWidths}>Restablecer columnas</button>
        </div>
      </div>
      <table className={`data-table resizable-table${resizeState ? " is-resizing" : ""}`}>
        <colgroup>
          {columns.map((column) => {
            const width = widths[column.key] ?? column.width;
            return <col key={column.key} style={{ width: `${width}px`, minWidth: `${column.minWidth}px` }} />;
          })}
        </colgroup>
        <thead>
          <tr>
            {columns.map((column) => {
              const width = widths[column.key] ?? column.width;
              const headerStyle: CSSProperties = { textAlign: column.align || "left" };
              return (
                <th key={column.key} className={`table-column--${column.kind || "medium"}`} style={headerStyle}>
                  <span className="table-heading-label">{column.header}</span>
                  <span
                    className="column-resizer"
                    role="separator"
                    aria-orientation="vertical"
                    aria-label={`Ajustar ancho de ${column.header}`}
                    aria-valuemin={column.minWidth}
                    aria-valuemax={column.maxWidth}
                    aria-valuenow={Math.round(width)}
                    tabIndex={0}
                    onPointerDown={(event) => beginResize(event, column)}
                    onKeyDown={(event) => adjustWithKeyboard(event, column)}
                  />
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={rowKey(row, index)} className={[onRowClick ? "clickable-row" : "", rowClassName?.(row) || ""].filter(Boolean).join(" ")} onClick={() => onRowClick?.(row)}>
              {columns.map((column) => (
                <td key={column.key} className={`table-column--${column.kind || "medium"}`} style={{ textAlign: column.align || "left" }}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {note ? <p className="table-note">{note}</p> : null}
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
  const columns: ResizableTableColumn<RecommendationRecord>[] = [
    { key: "item", header: "Artículo", width: 220, minWidth: 150, maxWidth: 420, kind: "medium", render: (item) => <><button className="link-button" type="button" onClick={() => item.item_code && onSelect?.(item.item_code)}><Eye size={14} /> {item.item_code || "-"}</button><small>{item.item_name || "Sin nombre"}</small></> },
    { key: "warehouse", header: "Almacén", width: 110, minWidth: 84, maxWidth: 180, kind: "short", render: (item) => item.warehouse_code || "-" },
    { key: "type", header: "Tipo", width: 190, minWidth: 150, maxWidth: 350, kind: "medium", render: (item) => <RecommendationTypeBadge value={item.recommendation_type} /> },
    { key: "status", header: "Estado", width: 160, minWidth: 120, maxWidth: 280, kind: "short", render: (item) => <StatusBadge value={item.recommendation_status} /> },
    { key: "priority", header: "Prioridad", width: 120, minWidth: 100, maxWidth: 190, kind: "short", render: (item) => <><PriorityBadge value={item.priority_level} /><small>{formatNumber(item.priority_score)}</small></> },
    { key: "risk", header: "Riesgo", width: 115, minWidth: 95, maxWidth: 190, kind: "short", render: (item) => <RiskBadge value={item.nivel_riesgo} /> },
    { key: "confidence", header: "Confianza", width: 125, minWidth: 105, maxWidth: 200, kind: "short", render: (item) => <ConfidenceBadge value={item.recommendation_confidence} /> },
    { key: "message", header: "Mensaje", width: 340, minWidth: 220, maxWidth: 700, kind: "long", render: (item) => item.main_message },
    { key: "quantity", header: "Cantidad", width: 120, minWidth: 100, maxWidth: 200, kind: "short", align: "right", render: (item) => item.suggested_quantity > 0 ? `${formatNumber(item.suggested_quantity, 2)} ref.` : "-" },
    { key: "action", header: "Acción", width: 190, minWidth: 150, maxWidth: 360, kind: "medium", render: (item) => item.next_action_label },
  ];

  return <ResizableTable rows={items} columns={columns} rowKey={(item) => `${item.item_code}-${item.warehouse_code}-${item.recommendation_type}`} storageKey="logistica-table-diagnosis-recommendation-columns" rowClassName={(item) => selectedItem === `${item.item_code}-${item.warehouse_code}-${item.recommendation_type}` ? "selected-row" : undefined} note={!compact ? "Vista limitada por filtros enviados al backend para evitar renderizar miles de filas." : undefined} />;
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
