from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.db.session import execute_read_query
from app.services.inventory_movements_service import classify_movement_type, get_inventory_movements_by_item, get_inventory_movement_types


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _period_from_date(value: Any) -> tuple[int, int, str]:
    if isinstance(value, datetime):
        year = value.year
        month = value.month
    elif isinstance(value, date):
        year = value.year
        month = value.month
    else:
        text = str(value)
        year = int(text[:4])
        month = int(text[5:7])
    return year, month, f"{year:04d}-{month:02d}"


def _limit_value(limit: int | None, default: int = 1000) -> int:
    if limit is None:
        return default
    return max(1, min(int(limit), 100000))


def build_monthly_consumption_records(
    movements: list[dict[str, Any]],
    include_transfers: bool = False,
    include_adjustments: bool = False,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, int, int], dict[str, Any]] = {}
    for movement in movements:
        out_qty = _to_float(movement.get("out_qty") or movement.get("OutQty"))
        if out_qty <= 0:
            continue

        classification = classify_movement_type(movement.get("trans_type") or movement.get("TransType"))
        if classification["is_transfer"] and not include_transfers:
            continue
        if classification["is_adjustment"] and not include_adjustments:
            continue
        if not classification["is_consumption_candidate"] and not classification["is_transfer"] and not classification["is_adjustment"]:
            continue

        item_code = movement.get("item_code") or movement.get("ItemCode")
        warehouse = movement.get("warehouse") or movement.get("Warehouse")
        doc_date = movement.get("doc_date") or movement.get("DocDate")
        year, month, period = _period_from_date(doc_date)
        key = (item_code, warehouse, year, month)
        record = grouped.setdefault(
            key,
            {
                "item_code": item_code,
                "item_description": movement.get("item_description") or movement.get("Dscription"),
                "warehouse": warehouse,
                "year": year,
                "month": month,
                "period": period,
                "consumed_quantity": 0.0,
                "movement_count": 0,
                "first_date": _to_iso(doc_date),
                "last_date": _to_iso(doc_date),
                "quality_flags": set(),
            },
        )
        record["consumed_quantity"] += out_qty
        record["movement_count"] += 1
        current_date = _to_iso(doc_date)
        if current_date:
            record["first_date"] = min(record["first_date"], current_date) if record["first_date"] else current_date
            record["last_date"] = max(record["last_date"], current_date) if record["last_date"] else current_date
        if classification["is_revisable"]:
            record["quality_flags"].add("movimiento_revisable")
        if classification["is_transfer"]:
            record["quality_flags"].add("incluye_transferencias")
        if classification["is_adjustment"]:
            record["quality_flags"].add("incluye_ajustes")

    results = []
    for record in grouped.values():
        record["quality_flags"] = sorted(record["quality_flags"])
        results.append(record)
    return sorted(results, key=lambda item: (item["period"], str(item["item_code"]), str(item["warehouse"])))


def _monthly_where_clause() -> str:
    return """
        WHERE ISNULL(OutQty, 0) > 0
          AND (:item_code IS NULL OR ItemCode = :item_code)
          AND (:warehouse IS NULL OR Warehouse = :warehouse)
          AND (:start_date IS NULL OR DocDate >= :start_date)
          AND (:end_date IS NULL OR DocDate <= :end_date)
    """


def get_monthly_consumption(
    item_code: str | None = None,
    warehouse: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_transfers: bool = False,
    include_adjustments: bool = False,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        WITH classified AS (
            SELECT
                ItemCode AS item_code,
                MAX(Dscription) AS item_description,
                Warehouse AS warehouse,
                YEAR(DocDate) AS year,
                MONTH(DocDate) AS month,
                CONVERT(char(7), DocDate, 120) AS period,
                SUM(CAST(ISNULL(OutQty, 0) AS decimal(19, 6))) AS consumed_quantity,
                COUNT_BIG(*) AS movement_count,
                MIN(DocDate) AS first_date,
                MAX(DocDate) AS last_date,
                SUM(CASE WHEN TransType = 67 THEN 1 ELSE 0 END) AS transfer_count,
                SUM(CASE WHEN TransType IN (59, 60, 10000071) THEN 1 ELSE 0 END) AS adjustment_count,
                SUM(CASE WHEN TransType IS NULL OR TransType NOT IN (13,15,202,59,60,67,10000071) THEN 1 ELSE 0 END) AS revisable_count
            FROM OINM
            {_monthly_where_clause()}
              AND (
                  TransType IN (13, 15, 202)
                  OR (:include_transfers = 1 AND TransType = 67)
                  OR (:include_adjustments = 1 AND TransType IN (59, 60, 10000071))
              )
            GROUP BY ItemCode, Warehouse, YEAR(DocDate), MONTH(DocDate), CONVERT(char(7), DocDate, 120)
        )
        SELECT *
        FROM classified
        ORDER BY period DESC, item_code, warehouse
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {
            "item_code": item_code,
            "warehouse": warehouse,
            "start_date": start_date,
            "end_date": end_date,
            "include_transfers": 1 if include_transfers else 0,
            "include_adjustments": 1 if include_adjustments else 0,
        },
    )
    return [_normalize_monthly_row(row) for row in rows]


def _normalize_monthly_row(row: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    if int(row.get("transfer_count") or 0) > 0:
        flags.append("incluye_transferencias")
    if int(row.get("adjustment_count") or 0) > 0:
        flags.append("incluye_ajustes")
    if int(row.get("revisable_count") or 0) > 0:
        flags.append("movimiento_revisable")
    return {
        "item_code": row.get("item_code"),
        "item_description": row.get("item_description"),
        "warehouse": row.get("warehouse"),
        "year": int(row.get("year") or 0),
        "month": int(row.get("month") or 0),
        "period": row.get("period"),
        "consumed_quantity": _to_float(row.get("consumed_quantity")),
        "movement_count": int(row.get("movement_count") or 0),
        "first_date": _to_iso(row.get("first_date")),
        "last_date": _to_iso(row.get("last_date")),
        "quality_flags": flags,
    }


def get_consumption_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    include_transfers: bool = False,
    include_adjustments: bool = False,
) -> dict[str, Any]:
    monthly = get_monthly_consumption(
        start_date=start_date,
        end_date=end_date,
        include_transfers=include_transfers,
        include_adjustments=include_adjustments,
        limit=100000,
    )
    total_consumed = sum(item["consumed_quantity"] for item in monthly)
    items = {item["item_code"] for item in monthly if item.get("item_code")}
    warehouses = {item["warehouse"] for item in monthly if item.get("warehouse")}
    periods = {item["period"] for item in monthly if item.get("period")}

    item_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"consumed_quantity": 0.0, "movement_count": 0, "item_description": None})
    warehouse_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"consumed_quantity": 0.0, "movement_count": 0})
    for item in monthly:
        item_key = str(item["item_code"])
        whs_key = str(item["warehouse"])
        item_totals[item_key]["consumed_quantity"] += item["consumed_quantity"]
        item_totals[item_key]["movement_count"] += item["movement_count"]
        item_totals[item_key]["item_description"] = item.get("item_description")
        warehouse_totals[whs_key]["consumed_quantity"] += item["consumed_quantity"]
        warehouse_totals[whs_key]["movement_count"] += item["movement_count"]

    excluded = get_excluded_consumption_counts(start_date=start_date, end_date=end_date)

    return {
        "date_range": {
            "start_date": min((item["first_date"] for item in monthly if item.get("first_date")), default=None),
            "end_date": max((item["last_date"] for item in monthly if item.get("last_date")), default=None),
        },
        "total_items_with_consumption": len(items),
        "total_warehouses": len(warehouses),
        "total_periods": len(periods),
        "total_consumed_quantity": total_consumed,
        "total_movements_analyzed": sum(item["movement_count"] for item in monthly),
        "excluded_transfer_movements": excluded["transfer_movements"],
        "revisable_movements": excluded["revisable_movements"],
        "top_items_by_consumption": _top_item_totals(item_totals),
        "top_warehouses_by_consumption": _top_warehouse_totals(warehouse_totals),
    }


def get_excluded_consumption_counts(start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
    rows = execute_read_query(
        """
        SELECT
            SUM(CASE WHEN TransType = 67 AND ISNULL(OutQty, 0) > 0 THEN 1 ELSE 0 END) AS transfer_movements,
            SUM(CASE WHEN (TransType IS NULL OR TransType NOT IN (13,15,202,67) OR TransType IN (59,60,10000071)) AND ISNULL(OutQty, 0) > 0 THEN 1 ELSE 0 END) AS revisable_movements
        FROM OINM
        WHERE (:start_date IS NULL OR DocDate >= :start_date)
          AND (:end_date IS NULL OR DocDate <= :end_date)
        """,
        {"start_date": start_date, "end_date": end_date},
    )
    row = rows[0] if rows else {}
    return {
        "transfer_movements": int(row.get("transfer_movements") or 0),
        "revisable_movements": int(row.get("revisable_movements") or 0),
    }


def _top_item_totals(item_totals: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "item_code": item_code,
            "item_description": values.get("item_description"),
            "consumed_quantity": values["consumed_quantity"],
            "movement_count": values["movement_count"],
        }
        for item_code, values in item_totals.items()
    ]
    return sorted(rows, key=lambda item: item["consumed_quantity"], reverse=True)[:10]


def _top_warehouse_totals(warehouse_totals: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "warehouse": warehouse,
            "consumed_quantity": values["consumed_quantity"],
            "movement_count": values["movement_count"],
        }
        for warehouse, values in warehouse_totals.items()
    ]
    return sorted(rows, key=lambda item: item["consumed_quantity"], reverse=True)[:10]


def get_item_consumption_detail(item_code: str) -> dict[str, Any]:
    monthly = get_monthly_consumption(item_code=item_code, limit=10000)
    item_row = execute_read_query(
        """
        SELECT TOP 1 ItemCode AS item_code, ItemName AS item_name
        FROM OITM
        WHERE ItemCode = :item_code
        """,
        {"item_code": item_code},
    )
    item_data = item_row[0] if item_row else {"item_code": item_code, "item_name": None}
    warehouses = sorted({row["warehouse"] for row in monthly if row.get("warehouse")})
    quality_flags = sorted({flag for row in monthly for flag in row.get("quality_flags", [])})
    return {
        "item": {"item_code": item_data.get("item_code"), "item_name": item_data.get("item_name")},
        "monthly_consumption": monthly,
        "warehouses": warehouses,
        "summary": {
            "total_consumed_quantity": sum(row["consumed_quantity"] for row in monthly),
            "total_movements": sum(row["movement_count"] for row in monthly),
            "periods": len({row["period"] for row in monthly if row.get("period")}),
        },
        "recent_movements": get_inventory_movements_by_item(item_code, limit=20),
        "quality_warnings": quality_flags,
    }


def get_consumption_movement_types() -> list[dict[str, Any]]:
    return get_inventory_movement_types()