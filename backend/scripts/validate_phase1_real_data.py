from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import pandas as pd
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseConnectionError, get_engine  # noqa: E402
from app.services.demand_service import get_monthly_demand  # noqa: E402
from app.services.sap_queries import (  # noqa: E402
    CRITICAL_COLUMNS,
    OPTIONAL_SAP_TABLES,
    SAP_TABLES,
)


EXPORT_DIR = Path(__file__).resolve().parents[1] / "exports"
REPORT_PATH = EXPORT_DIR / "phase1_validation_report.txt"
YEARLY_PATH = EXPORT_DIR / "phase1_yearly_summary.csv"
MONTHLY_PATH = EXPORT_DIR / "phase1_monthly_summary.csv"
ISSUES_PATH = EXPORT_DIR / "phase1_data_issues.csv"


@dataclass
class ValidationState:
    lines: list[str] = field(default_factory=list)
    critical_issues: list[str] = field(default_factory=list)
    noncritical_issues: list[str] = field(default_factory=list)
    tables_found: list[str] = field(default_factory=list)
    tables_missing: list[str] = field(default_factory=list)
    invoice_min: Any = None
    invoice_max: Any = None
    credit_min: Any = None
    credit_max: Any = None
    demand_stats: dict[str, Any] = field(default_factory=dict)

    def write(self, value: str = "") -> None:
        self.lines.append(value)
        print(value)


def read_frame(connection: Connection, query: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql_query(text(query), connection, params=params or {})


def object_type(connection: Connection, object_name: str) -> str | None:
    return connection.execute(
        text(
            """
            SELECT type_desc
            FROM sys.objects
            WHERE object_id = OBJECT_ID(:object_name)
            """
        ),
        {"object_name": object_name},
    ).scalar_one_or_none()


def column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT CASE WHEN COL_LENGTH(:table_name, :column_name) IS NULL
                    THEN 0 ELSE 1 END
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar_one()
    )


def inspect_server(connection: Connection, state: ValidationState) -> None:
    row = connection.execute(
        text(
            """
            SELECT
                DB_NAME() AS database_name,
                SYSDATETIME() AS server_datetime,
                CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128))
                    AS product_version,
                CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) AS edition
            """
        )
    ).mappings().one()
    state.write("1. CONEXIÓN SQL SERVER")
    state.write("Estado: OK")
    state.write(f"Base: {row['database_name']}")
    state.write(f"Fecha/hora SQL: {row['server_datetime']}")
    state.write(f"Versión: {row['product_version']} / {row['edition']}")
    state.write()


def inspect_tables(connection: Connection, state: ValidationState) -> None:
    state.write("2. TABLAS SAP")
    for table_name in SAP_TABLES + OPTIONAL_SAP_TABLES:
        object_kind = object_type(connection, table_name)
        if object_kind:
            count = connection.execute(
                text(f"SELECT COUNT_BIG(*) FROM [{table_name}]")
            ).scalar_one()
            state.tables_found.append(table_name)
            state.write(
                f"[OK] {table_name}: {count:,} registros ({object_kind})"
            )
        else:
            state.tables_missing.append(table_name)
            marker = "CRÍTICA" if table_name in SAP_TABLES else "OPCIONAL"
            state.write(f"[FALTA {marker}] {table_name}")
            if table_name in SAP_TABLES:
                state.critical_issues.append(f"Falta tabla principal {table_name}")
            else:
                state.noncritical_issues.append(f"Falta tabla opcional {table_name}")
    state.write()


def inspect_columns(connection: Connection, state: ValidationState) -> pd.DataFrame:
    state.write("3. COLUMNAS CRÍTICAS")
    records = []
    state.write(f"{'Tabla':<8} {'Columna':<16} {'Existe':<8} Observación")
    for table_name, columns in CRITICAL_COLUMNS.items():
        for column_name in columns:
            exists = column_exists(connection, table_name, column_name)
            observation = "Compatible" if exists else "Requiere ajuste"
            state.write(
                f"{table_name:<8} {column_name:<16} "
                f"{('Sí' if exists else 'No'):<8} {observation}"
            )
            records.append(
                {
                    "category": "critical_column",
                    "table": table_name,
                    "item": column_name,
                    "count": 0 if exists else 1,
                    "severity": "ok" if exists else "critical",
                    "example": observation,
                }
            )
            if not exists:
                state.critical_issues.append(
                    f"Falta columna {table_name}.{column_name}"
                )
    state.write()
    return pd.DataFrame(records)


def inspect_ranges(connection: Connection, state: ValidationState) -> None:
    state.write("4. RANGOS DE FECHAS")
    for table_name, prefix in (("OINV", "invoice"), ("ORIN", "credit")):
        if table_name not in state.tables_found:
            continue
        row = connection.execute(
            text(
                f"""
                SELECT MIN(DocDate) AS min_date, MAX(DocDate) AS max_date
                FROM [{table_name}]
                WHERE CANCELED = 'N'
                """
            )
        ).mappings().one()
        setattr(state, f"{prefix}_min", row["min_date"])
        setattr(state, f"{prefix}_max", row["max_date"])
    state.write(f"Facturas: {state.invoice_min} a {state.invoice_max}")
    state.write(f"Notas de crédito: {state.credit_min} a {state.credit_max}")

    all_dates = [
        value
        for value in (
            state.invoice_min,
            state.invoice_max,
            state.credit_min,
            state.credit_max,
        )
        if value is not None
    ]
    if all_dates:
        state.write(f"Rango total: {min(all_dates)} a {max(all_dates)}")
        if min(all_dates).year < 2014 or max(all_dates).year > 2025:
            state.noncritical_issues.append(
                "Existen fechas activas fuera del rango esperado 2014-2025"
            )
    state.write()


def build_yearly_summary(connection: Connection) -> pd.DataFrame:
    return read_frame(
        connection,
        """
        WITH invoice_lines AS (
            SELECT
                YEAR(H.DocDate) AS [year],
                SUM(CAST(L.Quantity AS decimal(28, 6))) AS invoice_quantity,
                SUM(CAST(L.LineTotal AS decimal(28, 6))) AS invoice_amount,
                COUNT(DISTINCT H.DocEntry) AS invoice_documents
            FROM OINV H
            INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
            WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
            GROUP BY YEAR(H.DocDate)
        ),
        credit_lines AS (
            SELECT
                YEAR(H.DocDate) AS [year],
                SUM(CAST(L.Quantity AS decimal(28, 6))) AS credit_quantity,
                SUM(CAST(L.LineTotal AS decimal(28, 6))) AS credit_amount,
                COUNT(DISTINCT H.DocEntry) AS credit_documents
            FROM ORIN H
            INNER JOIN RIN1 L ON L.DocEntry = H.DocEntry
            WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
            GROUP BY YEAR(H.DocDate)
        ),
        distinct_items AS (
            SELECT YEAR(DocDate) AS [year], COUNT(DISTINCT ItemCode) AS distinct_items
            FROM (
                SELECT H.DocDate, L.ItemCode
                FROM OINV H INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
                WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
                UNION ALL
                SELECT H.DocDate, L.ItemCode
                FROM ORIN H INNER JOIN RIN1 L ON L.DocEntry = H.DocEntry
                WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
            ) D
            GROUP BY YEAR(DocDate)
        )
        SELECT
            COALESCE(I.[year], C.[year]) AS [year],
            COALESCE(I.invoice_quantity, 0) AS invoice_quantity,
            COALESCE(C.credit_quantity, 0) AS credit_quantity,
            COALESCE(I.invoice_quantity, 0) - COALESCE(C.credit_quantity, 0)
                AS net_quantity,
            COALESCE(I.invoice_amount, 0) AS invoice_amount,
            COALESCE(C.credit_amount, 0) AS credit_amount,
            COALESCE(I.invoice_amount, 0) - COALESCE(C.credit_amount, 0)
                AS net_amount,
            COALESCE(I.invoice_documents, 0) AS invoice_documents,
            COALESCE(C.credit_documents, 0) AS credit_documents,
            COALESCE(D.distinct_items, 0) AS distinct_items
        FROM invoice_lines I
        FULL OUTER JOIN credit_lines C ON C.[year] = I.[year]
        LEFT JOIN distinct_items D
            ON D.[year] = COALESCE(I.[year], C.[year])
        ORDER BY [year]
        """,
    )


def build_monthly_summary(connection: Connection, max_date: Any) -> pd.DataFrame:
    return read_frame(
        connection,
        """
        WITH limits AS (
            SELECT DATEADD(month, -23, DATEFROMPARTS(YEAR(:max_date),
                MONTH(:max_date), 1)) AS date_from,
                CAST(:max_date AS date) AS date_to
        ),
        documents AS (
            SELECT
                CONVERT(char(7), H.DocDate, 120) AS period,
                L.ItemCode,
                CAST(L.Quantity AS decimal(28, 6)) AS invoice_quantity,
                CAST(0 AS decimal(28, 6)) AS credit_quantity,
                CAST(L.LineTotal AS decimal(28, 6)) AS invoice_amount,
                CAST(0 AS decimal(28, 6)) AS credit_amount
            FROM OINV H
            INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
            CROSS JOIN limits X
            WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
              AND H.DocDate >= X.date_from
              AND H.DocDate < DATEADD(day, 1, X.date_to)
            UNION ALL
            SELECT
                CONVERT(char(7), H.DocDate, 120),
                L.ItemCode,
                0,
                CAST(L.Quantity AS decimal(28, 6)),
                0,
                CAST(L.LineTotal AS decimal(28, 6))
            FROM ORIN H
            INNER JOIN RIN1 L ON L.DocEntry = H.DocEntry
            CROSS JOIN limits X
            WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
              AND H.DocDate >= X.date_from
              AND H.DocDate < DATEADD(day, 1, X.date_to)
        )
        SELECT
            period,
            SUM(invoice_quantity) AS invoice_quantity,
            SUM(credit_quantity) AS credit_quantity,
            SUM(invoice_quantity) - SUM(credit_quantity) AS net_quantity,
            SUM(invoice_amount) AS invoice_amount,
            SUM(credit_amount) AS credit_amount,
            SUM(invoice_amount) - SUM(credit_amount) AS net_amount,
            COUNT(DISTINCT ItemCode) AS distinct_items
        FROM documents
        GROUP BY period
        ORDER BY period
        """,
        {"max_date": max_date},
    )


def inspect_demand(state: ValidationState) -> pd.DataFrame:
    state.write("5. DEMANDA MENSUAL NETA")
    rows = get_monthly_demand(state.invoice_min, state.invoice_max)
    demand = pd.DataFrame(rows)
    if demand.empty:
        state.critical_issues.append("La consulta de demanda mensual no devolvió datos")
        state.write("Sin datos.")
        state.write()
        return demand
    state.demand_stats = {
        "period_count": int(demand["period"].nunique()),
        "first_period": demand["period"].min(),
        "last_period": demand["period"].max(),
        "distinct_items": int(demand["item_code"].nunique()),
        "net_quantity": float(demand["net_quantity"].sum()),
        "net_amount": float(demand["net_sales_total"].sum()),
        "rows": len(demand),
    }
    for key, value in state.demand_stats.items():
        state.write(f"{key}: {value:,}" if isinstance(value, int) else f"{key}: {value}")
    state.write("Muestra (máximo 5 filas):")
    state.write(demand.head(5).to_string(index=False))
    state.write()
    return demand


def issue_count(
    connection: Connection,
    category: str,
    query: str,
    severity: str = "warning",
) -> dict[str, Any]:
    row = connection.execute(text(query)).mappings().one()
    return {
        "category": category,
        "table": row.get("source_table"),
        "item": row.get("item"),
        "count": int(row["issue_count"] or 0),
        "severity": severity,
        "example": row.get("example"),
    }


def inspect_issues(
    connection: Connection,
    demand: pd.DataFrame,
    state: ValidationState,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    queries = {
        "invoice_lines_without_item": """
            SELECT 'INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(Dscription) AS example, NULL AS item
            FROM INV1 WHERE ItemCode IS NULL
        """,
        "credit_lines_without_item": """
            SELECT 'RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(Dscription) AS example, NULL AS item
            FROM RIN1 WHERE ItemCode IS NULL
        """,
        "invoice_zero_quantity": """
            SELECT 'INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM INV1 WHERE Quantity = 0
        """,
        "credit_zero_quantity": """
            SELECT 'RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM RIN1 WHERE Quantity = 0
        """,
        "invoice_zero_line_total": """
            SELECT 'INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM INV1 WHERE LineTotal = 0
        """,
        "credit_zero_line_total": """
            SELECT 'RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM RIN1 WHERE LineTotal = 0
        """,
        "invoice_item_not_in_master": """
            SELECT 'INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(L.ItemCode) AS example, NULL AS item
            FROM INV1 L LEFT JOIN OITM I ON I.ItemCode = L.ItemCode
            WHERE L.ItemCode IS NOT NULL AND I.ItemCode IS NULL
        """,
        "credit_item_not_in_master": """
            SELECT 'RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(L.ItemCode) AS example, NULL AS item
            FROM RIN1 L LEFT JOIN OITM I ON I.ItemCode = L.ItemCode
            WHERE L.ItemCode IS NOT NULL AND I.ItemCode IS NULL
        """,
        "cancelled_invoice_lines_excluded": """
            SELECT 'OINV/INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(CAST(H.DocEntry AS varchar(30))) AS example, NULL AS item
            FROM OINV H INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
            WHERE H.CANCELED = 'Y'
        """,
        "cancelled_credit_lines_excluded": """
            SELECT 'ORIN/RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(CAST(H.DocEntry AS varchar(30))) AS example, NULL AS item
            FROM ORIN H INNER JOIN RIN1 L ON L.DocEntry = H.DocEntry
            WHERE H.CANCELED = 'Y'
        """,
        "dates_outside_expected_range": """
            SELECT 'OINV/ORIN' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(CONVERT(varchar(10), DocDate, 120)) AS example, NULL AS item
            FROM (
                SELECT DocDate FROM OINV WHERE CANCELED = 'N'
                UNION ALL
                SELECT DocDate FROM ORIN WHERE CANCELED = 'N'
            ) D
            WHERE DocDate < '20140101' OR DocDate >= '20260101'
        """,
        "different_descriptions_per_item": """
            SELECT 'INV1/RIN1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM (
                SELECT ItemCode
                FROM (
                    SELECT ItemCode, Dscription FROM INV1 WHERE ItemCode IS NOT NULL
                    UNION
                    SELECT ItemCode, Dscription FROM RIN1 WHERE ItemCode IS NOT NULL
                ) X
                GROUP BY ItemCode
                HAVING COUNT(DISTINCT Dscription) > 1
            ) D
        """,
        "credits_greater_than_invoices_by_item": """
            SELECT 'OINV/ORIN' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(ItemCode) AS example, NULL AS item
            FROM (
                SELECT ItemCode
                FROM (
                    SELECT L.ItemCode,
                        SUM(CAST(L.Quantity AS decimal(28, 6))) AS invoice_quantity,
                        CAST(0 AS decimal(28, 6)) AS credit_quantity
                    FROM OINV H
                    INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
                    WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
                    GROUP BY L.ItemCode
                    UNION ALL
                    SELECT L.ItemCode, 0,
                        SUM(CAST(L.Quantity AS decimal(28, 6)))
                    FROM ORIN H
                    INNER JOIN RIN1 L ON L.DocEntry = H.DocEntry
                    WHERE H.CANCELED = 'N' AND L.ItemCode IS NOT NULL
                    GROUP BY L.ItemCode
                ) X
                GROUP BY ItemCode
                HAVING SUM(credit_quantity) > SUM(invoice_quantity)
            ) D
        """,
        "active_invoices_zero_total_with_nonzero_lines": """
            SELECT 'OINV/INV1' AS source_table, COUNT_BIG(*) AS issue_count,
                MIN(CAST(DocEntry AS varchar(30))) AS example, NULL AS item
            FROM (
                SELECT H.DocEntry
                FROM OINV H
                INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
                WHERE H.CANCELED = 'N' AND H.DocTotal = 0
                GROUP BY H.DocEntry
                HAVING SUM(L.LineTotal) <> 0
            ) D
        """,
    }
    for category, query in queries.items():
        records.append(issue_count(connection, category, query))

    if not demand.empty:
        negative_months = (
            demand.groupby("period", as_index=False)["net_quantity"].sum()
        )
        negative_months = negative_months[negative_months["net_quantity"] < 0]
        negative_amount_months = (
            demand.groupby("period", as_index=False)["net_sales_total"].sum()
        )
        negative_amount_months = negative_amount_months[
            negative_amount_months["net_sales_total"] < 0
        ]
        records.append(
            {
                "category": "months_with_negative_net_demand",
                "table": "monthly_demand",
                "item": None,
                "count": len(negative_months),
                "severity": "warning",
                "example": (
                    negative_months.iloc[0]["period"] if len(negative_months) else None
                ),
            }
        )
        item_totals = demand.groupby("item_code", as_index=False).agg(
            net_quantity=("net_quantity", "sum"),
            active_months=("period", "nunique"),
        )
        negative_items = item_totals[item_totals["net_quantity"] < 0]
        sparse_items = item_totals[item_totals["active_months"] <= 2]
        records.extend(
            [
                {
                    "category": "months_with_negative_net_amount",
                    "table": "monthly_demand",
                    "item": None,
                    "count": len(negative_amount_months),
                    "severity": "warning",
                    "example": (
                        negative_amount_months.iloc[0]["period"]
                        if len(negative_amount_months)
                        else None
                    ),
                },
                {
                    "category": "items_with_negative_accumulated_demand",
                    "table": "monthly_demand",
                    "item": None,
                    "count": len(negative_items),
                    "severity": "warning",
                    "example": (
                        negative_items.iloc[0]["item_code"]
                        if len(negative_items)
                        else None
                    ),
                },
                {
                    "category": "items_with_one_or_two_active_months",
                    "table": "monthly_demand",
                    "item": None,
                    "count": len(sparse_items),
                    "severity": "info",
                    "example": (
                        sparse_items.iloc[0]["item_code"] if len(sparse_items) else None
                    ),
                },
            ]
        )

    issues = pd.DataFrame(records)
    state.write("8. POSIBLES INCONSISTENCIAS")
    state.write(issues.to_string(index=False))
    state.write()
    for row in issues[issues["count"] > 0].itertuples():
        state.noncritical_issues.append(f"{row.category}: {row.count}")
    return issues


def inspect_currency(connection: Connection, state: ValidationState) -> None:
    state.write("9. VALIDACIÓN DE LINETOTAL Y MONEDA")
    sample = read_frame(
        connection,
        """
        SELECT TOP (10)
            H.DocEntry,
            H.DocCur,
            H.DocRate,
            H.DocTotal,
            H.DocTotalFC,
            SUM(L.LineTotal) AS sum_line_total,
            SUM(L.TotalFrgn) AS sum_total_foreign
        FROM OINV H
        INNER JOIN INV1 L ON L.DocEntry = H.DocEntry
        WHERE H.CANCELED = 'N'
        GROUP BY H.DocEntry, H.DocCur, H.DocRate, H.DocTotal, H.DocTotalFC
        ORDER BY H.DocEntry DESC
        """,
    )
    state.write(sample.to_string(index=False))
    state.write(
        "Supuesto actual: LineTotal se trata como importe de línea en moneda "
        "local; TotalFrgn es el candidato para moneda extranjera. Impuestos, "
        "gastos, descuentos de cabecera y redondeos explican diferencias con DocTotal."
    )
    state.write()


def save_outputs(
    state: ValidationState,
    yearly: pd.DataFrame,
    monthly: pd.DataFrame,
    issues: pd.DataFrame,
) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    yearly.to_csv(YEARLY_PATH, index=False, encoding="utf-8-sig")
    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8-sig")
    issues.to_csv(ISSUES_PATH, index=False, encoding="utf-8-sig")
    REPORT_PATH.write_text("\n".join(state.lines) + "\n", encoding="utf-8")


def empty_outputs(state: ValidationState) -> None:
    save_outputs(
        state,
        pd.DataFrame(
            columns=[
                "year",
                "invoice_quantity",
                "credit_quantity",
                "net_quantity",
                "invoice_amount",
                "credit_amount",
                "net_amount",
                "invoice_documents",
                "credit_documents",
                "distinct_items",
            ]
        ),
        pd.DataFrame(
            columns=[
                "period",
                "invoice_quantity",
                "credit_quantity",
                "net_quantity",
                "invoice_amount",
                "credit_amount",
                "net_amount",
                "distinct_items",
            ]
        ),
        pd.DataFrame(
            [
                {
                    "category": "connection_failed",
                    "table": None,
                    "item": None,
                    "count": 1,
                    "severity": "critical",
                    "example": "No fue posible abrir una conexión SQL Server.",
                }
            ]
        ),
    )


def main() -> int:
    settings = get_settings()
    state = ValidationState()
    state.write("VALIDACIÓN FASE 1 - DATOS REALES")
    state.write(f"Fecha de ejecución: {datetime.now().isoformat(timespec='seconds')}")
    state.write(f"Servidor: {settings.db_server}")
    state.write(f"Base objetivo: {settings.db_name}")
    state.write("Modo: solo lectura")
    state.write("=" * 72)
    state.write()

    try:
        with get_engine().connect() as connection:
            inspect_server(connection, state)
            inspect_tables(connection, state)
            column_issues = inspect_columns(connection, state)
            inspect_ranges(connection, state)
            demand = inspect_demand(state)

            state.write("6. RESUMEN ANUAL")
            yearly = build_yearly_summary(connection)
            state.write(yearly.to_string(index=False))
            state.write()

            state.write("7. ÚLTIMOS 24 MESES")
            monthly = build_monthly_summary(connection, state.invoice_max)
            state.write(monthly.to_string(index=False))
            state.write()

            issues = inspect_issues(connection, demand, state)
            issues = pd.concat([column_issues, issues], ignore_index=True)
            inspect_currency(connection, state)

            state.write("10. DECISIÓN")
            can_continue = (
                not state.critical_issues
                and not demand.empty
                and state.invoice_min is not None
                and state.invoice_max is not None
            )
            state.write(
                "¿Podemos pasar a Fase 2 ABC/XYZ?: "
                f"{'SÍ' if can_continue else 'NO'}"
            )
            if state.critical_issues:
                state.write("Bloqueos:")
                for issue in state.critical_issues:
                    state.write(f"- {issue}")
            if state.noncritical_issues:
                state.write("Hallazgos no bloqueantes:")
                for issue in state.noncritical_issues:
                    state.write(f"- {issue}")

            save_outputs(state, yearly, monthly, issues)
            state.write()
            state.write(f"Reporte: {REPORT_PATH}")
            state.write(f"Resumen anual: {YEARLY_PATH}")
            state.write(f"Resumen mensual: {MONTHLY_PATH}")
            state.write(f"Problemas: {ISSUES_PATH}")
            REPORT_PATH.write_text("\n".join(state.lines) + "\n", encoding="utf-8")
            return 0 if can_continue else 2
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        state.critical_issues.append("Conexión SQL Server no disponible")
        state.write("1. CONEXIÓN SQL SERVER")
        state.write("Estado: ERROR")
        state.write(
            "No fue posible conectar. Verifique servidor/instancia, servicio "
            "SQL Server, TCP/puerto y credenciales."
        )
        state.write(f"Detalle controlado: {type(exc).__name__}")
        state.write()
        state.write("DECISIÓN: NO se puede aprobar el paso a Fase 2 sin datos reales.")
        empty_outputs(state)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
