from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import text

from app.core.database import read_rows
from app.services.demand_service import get_monthly_demand
from app.services.schema_service import DEMO_TABLES, get_available_schema
from app.services.sap_queries import (
    build_document_date_range_query,
    has_table,
    pick_column,
    quote_identifier,
    table_columns,
)


def _active_filter(columns: set[str], alias: str) -> str:
    if "canceled" not in columns:
        return ""
    prefix = f"{alias}." if alias else ""
    return f" AND {prefix}{quote_identifier('CANCELED')} = 'N'"


def inspect_demo_database() -> dict[str, Any]:
    schema = get_available_schema()
    tables: dict[str, dict[str, Any]] = {}
    for table in DEMO_TABLES:
        columns = sorted(schema.get(table, set()))
        entry: dict[str, Any] = {
            "exists": bool(columns),
            "columns": columns,
            "row_count": None,
        }
        if columns:
            entry["row_count"] = int(
                read_rows(text(f"SELECT COUNT_BIG(*) AS row_count FROM {quote_identifier(table)}"))[0]["row_count"]
            )
        tables[table] = entry

    date_range = read_rows(build_document_date_range_query(schema))[0]
    min_date = date_range["min_date"]
    max_date = date_range["max_date"]
    month_count = 0
    if min_date is not None:
        date_query = _document_month_count_query(schema)
        month_count = int(read_rows(date_query)[0]["month_count"])
    monthly = _build_monthly_diagnostics(schema)
    validation = _validation_summary(schema, min_date, max_date)
    return {
        "provider": "demo",
        "tables": tables,
        "date_range": {
            "min_date": _iso_date(min_date),
            "max_date": _iso_date(max_date),
            "distinct_months": month_count,
        },
        "monthly_summary": monthly,
        "validation": validation,
    }


def _iso_date(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else (str(value) if value else None)


def _document_month_count_query(schema):
    parts = []
    for table in ("OINV", "ORIN"):
        if not has_table(schema, table):
            continue
        columns = table_columns(schema, table)
        date_column = pick_column(columns, "DocDate", "TaxDate", "CreateDate")
        if date_column:
            parts.append(
                f"SELECT CONVERT(char(7), {quote_identifier(date_column)}, 120) AS period "
                f"FROM {quote_identifier(table)} WHERE 1 = 1 {_active_filter(columns, '')}"
            )
    return text("SELECT COUNT(DISTINCT period) AS month_count FROM (" + " UNION ALL ".join(parts) + ") D")


def _build_monthly_diagnostics(schema) -> list[dict[str, Any]]:
    rows = get_monthly_demand()
    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "period": None,
            "sales": 0.0,
            "units_sold": 0.0,
            "returns": 0.0,
            "inventory_receipts": 0.0,
            "inventory_issues": 0.0,
            "available_stock": None,
            "purchases": 0.0,
            "open_purchase_orders": 0.0,
        }
    )
    for row in rows:
        period = str(row["period"])
        current = summary[period]
        current["period"] = period
        quantity = float(row.get("net_quantity") or 0)
        amount = float(row.get("net_sales_total") or 0)
        current["sales"] += amount
        current["units_sold"] += max(0.0, quantity)
        current["returns"] += max(0.0, -quantity)

    for field, table, lines, date_names, quantity_names, amount_names in (
        ("inventory_receipts", "OPDN", "PDN1", ("DocDate", "TaxDate"), ("Quantity", "Qty"), ("LineTotal", "Amount")),
        ("purchases", "OPOR", "POR1", ("DocDate", "TaxDate"), ("Quantity", "Qty"), ("LineTotal", "Amount")),
    ):
        for period, value in _optional_monthly_metric(
            schema, table, lines, date_names, quantity_names, amount_names
        ).items():
            summary[period]["period"] = period
            summary[period][field] += value

    for period, value in _inventory_movement_metrics(schema).items():
        summary[period]["period"] = period
        summary[period]["inventory_receipts"] += value["receipts"]
        summary[period]["inventory_issues"] += value["issues"]

    # OITW is a current snapshot; it is intentionally reported only on the
    # latest period and never projected backward into historical months.
    if has_table(schema, "OITW"):
        stock_columns = table_columns(schema, "OITW")
        stock_column = pick_column(stock_columns, "OnHand", "PhysicalStock", "Stock")
        if stock_column:
            stock = read_rows(text(f"SELECT SUM({quote_identifier(stock_column)}) AS available_stock FROM [OITW]"))[0]
            latest = max(summary) if summary else date.today().strftime("%Y-%m")
            summary[latest]["period"] = latest
            summary[latest]["available_stock"] = float(stock["available_stock"] or 0)
    return [summary[key] for key in sorted(summary)]


def _optional_monthly_metric(schema, header, lines, date_names, quantity_names, amount_names):
    if not (has_table(schema, header) and has_table(schema, lines)):
        return {}
    hcols, lcols = table_columns(schema, header), table_columns(schema, lines)
    date_column = pick_column(hcols, *date_names)
    quantity_column = pick_column(lcols, *quantity_names)
    amount_column = pick_column(lcols, *amount_names)
    if not (date_column and (quantity_column or amount_column)):
        return {}
    value_column = quantity_column or amount_column
    cancelled = _active_filter(hcols, "H")
    query = text(
        f"SELECT CONVERT(char(7), H.{quote_identifier(date_column)}, 120) AS period, "
        f"SUM(CAST(L.{quote_identifier(value_column)} AS decimal(19, 6))) AS value "
        f"FROM {quote_identifier(header)} H INNER JOIN {quote_identifier(lines)} L "
        f"ON L.[DocEntry] = H.[DocEntry] WHERE 1 = 1 {cancelled} "
        f"GROUP BY CONVERT(char(7), H.{quote_identifier(date_column)}, 120)"
    )
    return {str(row["period"]): float(row["value"] or 0) for row in read_rows(query)}


def _inventory_movement_metrics(schema):
    if not has_table(schema, "OINM"):
        return {}
    cols = table_columns(schema, "OINM")
    date_column = pick_column(cols, "DocDate", "CreateDate", "TransDate")
    in_column = pick_column(cols, "InQty", "InQuantity", "ReceiptQty")
    out_column = pick_column(cols, "OutQty", "OutQuantity", "IssueQty")
    if not (date_column and (in_column or out_column)):
        return {}
    in_expr = f"SUM(CAST({quote_identifier(in_column)} AS decimal(19, 6)))" if in_column else "0"
    out_expr = f"SUM(CAST({quote_identifier(out_column)} AS decimal(19, 6)))" if out_column else "0"
    query = text(
        f"SELECT CONVERT(char(7), {quote_identifier(date_column)}, 120) AS period, "
        f"{in_expr} AS receipts, {out_expr} AS issues FROM [OINM] "
        f"GROUP BY CONVERT(char(7), {quote_identifier(date_column)}, 120)"
    )
    return {
        str(row["period"]): {
            "receipts": float(row["receipts"] or 0),
            "issues": float(row["issues"] or 0),
        }
        for row in read_rows(query)
    }


def _validation_summary(schema, min_date, max_date):
    checks: dict[str, int | None] = {}
    for table, lines in (("OINV", "INV1"), ("ORIN", "RIN1")):
        if not (has_table(schema, table) and has_table(schema, lines)):
            continue
        hcols, lcols = table_columns(schema, table), table_columns(schema, lines)
        if "docentry" in lcols and "docentry" in hcols:
            checks[f"orphan_{lines.lower()}_docentry"] = int(read_rows(text(
                f"SELECT COUNT_BIG(*) AS issue_count FROM {quote_identifier(lines)} L "
                f"WHERE NOT EXISTS (SELECT 1 FROM {quote_identifier(table)} H WHERE H.[DocEntry] = L.[DocEntry])"
            ))[0]["issue_count"])
        if "itemcode" in lcols:
            checks[f"null_{lines.lower()}_itemcode"] = int(read_rows(text(
                f"SELECT COUNT_BIG(*) AS issue_count FROM {quote_identifier(lines)} WHERE [ItemCode] IS NULL"
            ))[0]["issue_count"])
        quantity = pick_column(lcols, "Quantity", "Qty", "QuantityBase")
        if quantity:
            checks[f"negative_{lines.lower()}_quantity"] = int(read_rows(text(
                f"SELECT COUNT_BIG(*) AS issue_count FROM {quote_identifier(lines)} WHERE {quote_identifier(quantity)} < 0"
            ))[0]["issue_count"])
    demand = get_monthly_demand()
    by_item: dict[str, set[str]] = defaultdict(set)
    for row in demand:
        by_item[str(row["item_code"])].add(str(row["period"]))
    checks["items_with_at_least_12_months"] = sum(len(periods) >= 12 for periods in by_item.values())
    checks["items_with_less_than_12_months"] = sum(len(periods) < 12 for periods in by_item.values())
    return {
        "checks": checks,
        "period_start": _iso_date(min_date),
        "period_end": _iso_date(max_date),
        "notes": [
            "Los nulos, huérfanos y cantidades negativas se cuentan sin modificar datos.",
            "OITW es un snapshot actual; no se atribuye a meses históricos.",
        ],
    }
