import { useMemo, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { EmptyState } from "./EmptyState";

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
  pageSize?: number;
}

export function DataTable<T>({
  rows,
  columns,
  rowKey,
  onRowClick,
  pageSize = 15,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = useMemo(
    () => rows.slice(safePage * pageSize, (safePage + 1) * pageSize),
    [rows, safePage, pageSize],
  );

  if (!rows.length) return <EmptyState />;

  return (
    <div className="table-shell">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  style={{ width: column.width, textAlign: column.align || "left" }}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr
                key={rowKey(row)}
                className={onRowClick ? "clickable-row" : undefined}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => (
                  <td key={column.key} style={{ textAlign: column.align || "left" }}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <footer className="table-footer">
        <span>
          {rows.length.toLocaleString("es-PE")} registros · Página {safePage + 1} de{" "}
          {pageCount}
        </span>
        <div>
          <button
            className="icon-button"
            disabled={safePage === 0}
            onClick={() => setPage(Math.max(0, safePage - 1))}
            aria-label="Página anterior"
          >
            <ChevronLeft size={17} />
          </button>
          <button
            className="icon-button"
            disabled={safePage >= pageCount - 1}
            onClick={() => setPage(Math.min(pageCount - 1, safePage + 1))}
            aria-label="Página siguiente"
          >
            <ChevronRight size={17} />
          </button>
        </div>
      </footer>
    </div>
  );
}
