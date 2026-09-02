import { useMemo, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ResizableTable, type ResizableTableColumn } from "../operational/components";

export interface Column<T> {
  key: string;
  header: string;
  width?: string;
  align?: "left" | "center" | "right";
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  storageKey?: string;
  pageSize?: number;
}

function parseWidth(width: string | undefined) {
  const parsed = width ? Number.parseInt(width, 10) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : 180;
}

export function DataTable<T>({
  rows,
  columns,
  rowKey,
  onRowClick,
  storageKey,
  pageSize = 15,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = useMemo(
    () => rows.slice(safePage * pageSize, (safePage + 1) * pageSize),
    [rows, safePage, pageSize],
  );

  const resizableColumns: ResizableTableColumn<T>[] = columns.map((column) => {
    const width = parseWidth(column.width);
    const kind = column.align ? "short" : "medium";
    return {
      ...column,
      width,
      minWidth: Math.max(96, Math.min(width, 140)),
      kind,
    };
  });
  const tableStorageKey = storageKey || `logistica-table-legacy-${columns.map((column) => column.key).join("-")}`;

  return (
    <>
      <ResizableTable rows={pageRows} columns={resizableColumns} rowKey={(row) => rowKey(row)} storageKey={tableStorageKey} onRowClick={onRowClick} />
      <footer className="pagination-bar table-pagination">
        <span>
          {rows.length.toLocaleString("es-PE")} registros · Página {safePage + 1} de{" "}
          {pageCount}
        </span>
        <div>
          <button
            className="secondary-button compact-button"
            disabled={safePage === 0}
            onClick={() => setPage(Math.max(0, safePage - 1))}
            aria-label="Página anterior"
          >
            <ChevronLeft size={17} />
          </button>
          <button
            className="secondary-button compact-button"
            disabled={safePage >= pageCount - 1}
            onClick={() => setPage(Math.min(pageCount - 1, safePage + 1))}
            aria-label="Página siguiente"
          >
            <ChevronRight size={17} />
          </button>
        </div>
      </footer>
    </>
  );
}
