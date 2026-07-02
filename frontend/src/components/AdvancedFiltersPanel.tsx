import { SlidersHorizontal } from "lucide-react";
import { useState, type ReactNode } from "react";

interface AdvancedFiltersPanelProps {
  children: ReactNode;
  resultCount?: number;
}

export function AdvancedFiltersPanel({
  children,
  resultCount,
}: AdvancedFiltersPanelProps) {
  const [open, setOpen] = useState(false);

  return (
    <section className="panel advanced-filter-shell">
      <div className="advanced-filter-header">
        <div>
          <h3>Filtros de trabajo</h3>
          <p>
            {typeof resultCount === "number"
              ? `${resultCount.toLocaleString("es-PE")} artículos encontrados`
              : "Ajuste la lista sin cambiar los cálculos."}
          </p>
        </div>
        <button
          type="button"
          className="button button-secondary"
          onClick={() => setOpen((value) => !value)}
        >
          <SlidersHorizontal size={16} />
          {open ? "Ocultar filtros avanzados" : "Mostrar filtros avanzados"}
        </button>
      </div>
      {open && <div className="advanced-filter-body">{children}</div>}
    </section>
  );
}
