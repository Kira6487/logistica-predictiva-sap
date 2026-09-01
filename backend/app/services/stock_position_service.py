from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.db.session import execute_read_query


STOCK_SOURCES: dict[str, dict[str, Any]] = {
    "OITW": {
        "description": "Stock por articulo y almacen",
        "expected_columns": ["ItemCode", "WhsCode", "OnHand", "IsCommited", "OnOrder"],
        "key_columns": ["ItemCode", "WhsCode", "OnHand", "IsCommited", "OnOrder"],
    },
    "OITM": {
        "description": "Maestro de articulos",
        "expected_columns": ["ItemCode", "ItemName", "InvntItem", "validFor"],
        "key_columns": ["ItemCode", "ItemName", "InvntItem", "validFor"],
    },
    "OWHS": {
        "description": "Maestro de almacenes",
        "expected_columns": ["WhsCode", "WhsName", "Inactive"],
        "key_columns": ["WhsCode", "WhsName", "Inactive"],
    },
}


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


def _limit_value(limit: int | None, default: int = 1000) -> int:
    if limit is None:
        return default
    return max(1, min(int(limit), 250000))


def get_table_columns(table_name: str) -> list[str]:
    rows = execute_read_query(
        """
        SELECT COLUMN_NAME AS column_name
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = :table_name
        ORDER BY ORDINAL_POSITION
        """,
        {"table_name": table_name},
    )
    return [str(row["column_name"]) for row in rows]


def get_table_type(table_name: str) -> str | None:
    rows = execute_read_query(
        """
        SELECT TABLE_TYPE AS table_type
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = :table_name
        """,
        {"table_name": table_name},
    )
    return str(rows[0]["table_type"]) if rows else None


def table_exists(table_name: str) -> bool:
    return get_table_type(table_name) is not None


def diagnose_stock_sources() -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for table_name, config in STOCK_SOURCES.items():
        columns = get_table_columns(table_name)
        diagnostics.append(
            {
                "source": table_name,
                "type": get_table_type(table_name),
                "description": config["description"],
                "columns": columns,
                "key_columns_found": [column for column in config["key_columns"] if column in columns],
                "missing_expected_columns": [column for column in config["expected_columns"] if column not in columns],
                "record_count": _table_count(table_name) if columns else 0,
            }
        )
    return diagnostics


def _table_count(table_name: str) -> int:
    rows = execute_read_query(f"SELECT COUNT_BIG(*) AS record_count FROM {table_name}")
    return int(rows[0]["record_count"] or 0) if rows else 0


def build_stock_position_record(row: dict[str, Any]) -> dict[str, Any]:
    stock_fisico = _to_float(row.get("stock_fisico"))
    stock_comprometido = _to_float(row.get("stock_comprometido"))
    stock_pedido = _to_float(row.get("stock_pedido"))
    stock_disponible = stock_fisico - stock_comprometido
    stock_proyectado_base = stock_disponible + stock_pedido
    warehouse_locked = str(row.get("warehouse_locked") or "N") == "Y"
    warehouse_inactive = str(row.get("warehouse_inactive") or "N") == "Y"
    item_inventory = str(row.get("item_inventory") or "") == "Y"
    item_active = str(row.get("item_active") or "") == "Y"
    return {
        "item_code": row.get("item_code"),
        "item_name": row.get("item_name"),
        "warehouse_code": row.get("warehouse_code"),
        "warehouse_name": row.get("warehouse_name"),
        "stock_fisico": stock_fisico,
        "stock_comprometido": stock_comprometido,
        "stock_pedido": stock_pedido,
        "stock_disponible": stock_disponible,
        "stock_proyectado_base": stock_proyectado_base,
        "sin_stock": stock_fisico == 0,
        "stock_negativo": stock_fisico < 0,
        "comprometido_mayor_stock": stock_comprometido > stock_fisico,
        "tiene_stock": stock_fisico > 0,
        "tiene_pedido_abierto": stock_pedido > 0,
        "tiene_compromiso_abierto": stock_comprometido > 0,
        "item_inventory": item_inventory,
        "item_active": item_active,
        "warehouse_locked": warehouse_locked,
        "warehouse_inactive": warehouse_inactive,
    }


def get_stock_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    only_with_stock: bool = False,
    only_negative: bool = False,
    only_committed_over_stock: bool = False,
    include_inactive: bool = False,
    include_locked_warehouses: bool = False,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            W.ItemCode AS item_code,
            I.ItemName AS item_name,
            W.WhsCode AS warehouse_code,
            H.WhsName AS warehouse_name,
            CAST(ISNULL(W.OnHand, 0) AS decimal(19, 6)) AS stock_fisico,
            CAST(ISNULL(W.IsCommited, 0) AS decimal(19, 6)) AS stock_comprometido,
            CAST(ISNULL(W.OnOrder, 0) AS decimal(19, 6)) AS stock_pedido,
            I.InvntItem AS item_inventory,
            I.validFor AS item_active,
            ISNULL(W.Locked, 'N') AS warehouse_locked,
            ISNULL(H.Inactive, 'N') AS warehouse_inactive
        FROM OITW W
        INNER JOIN OITM I ON I.ItemCode = W.ItemCode
        LEFT JOIN OWHS H ON H.WhsCode = W.WhsCode
        WHERE (:item_code IS NULL OR W.ItemCode = :item_code)
          AND (:warehouse IS NULL OR W.WhsCode = :warehouse)
          AND (:include_inactive = 1 OR (I.InvntItem = 'Y' AND I.validFor = 'Y'))
          AND (:include_locked_warehouses = 1 OR (ISNULL(W.Locked, 'N') <> 'Y' AND ISNULL(H.Inactive, 'N') <> 'Y'))
          AND (:only_with_stock = 0 OR ISNULL(W.OnHand, 0) <> 0 OR ISNULL(W.IsCommited, 0) <> 0 OR ISNULL(W.OnOrder, 0) <> 0)
          AND (:only_negative = 0 OR ISNULL(W.OnHand, 0) < 0)
          AND (:only_committed_over_stock = 0 OR ISNULL(W.IsCommited, 0) > ISNULL(W.OnHand, 0))
        ORDER BY W.ItemCode, W.WhsCode
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {
            "item_code": item_code,
            "warehouse": warehouse,
            "include_inactive": 1 if include_inactive else 0,
            "include_locked_warehouses": 1 if include_locked_warehouses else 0,
            "only_with_stock": 1 if only_with_stock else 0,
            "only_negative": 1 if only_negative else 0,
            "only_committed_over_stock": 1 if only_committed_over_stock else 0,
        },
    )
    return [build_stock_position_record(row) for row in rows]


def get_stock_summary() -> dict[str, Any]:
    rows = execute_read_query(
        """
        SELECT
            COUNT_BIG(DISTINCT CASE WHEN ISNULL(W.OnHand, 0) <> 0 THEN W.ItemCode END) AS total_items,
            COUNT_BIG(DISTINCT W.WhsCode) AS total_warehouses,
            SUM(CAST(ISNULL(W.OnHand, 0) AS decimal(19, 6))) AS stock_fisico_total,
            SUM(CAST(ISNULL(W.OnHand, 0) - ISNULL(W.IsCommited, 0) AS decimal(19, 6))) AS stock_disponible_total,
            SUM(CASE WHEN ISNULL(W.OnHand, 0) = 0 THEN 1 ELSE 0 END) AS items_without_stock,
            SUM(CASE WHEN ISNULL(W.OnHand, 0) < 0 THEN 1 ELSE 0 END) AS negative_stock_items,
            SUM(CASE WHEN ISNULL(W.IsCommited, 0) > ISNULL(W.OnHand, 0) THEN 1 ELSE 0 END) AS committed_over_stock_items,
            SUM(CASE WHEN ISNULL(W.OnOrder, 0) > 0 THEN 1 ELSE 0 END) AS items_with_open_orders
        FROM OITW W
        INNER JOIN OITM I ON I.ItemCode = W.ItemCode
        LEFT JOIN OWHS H ON H.WhsCode = W.WhsCode
        WHERE I.InvntItem = 'Y'
          AND I.validFor = 'Y'
          AND ISNULL(W.Locked, 'N') <> 'Y'
          AND ISNULL(H.Inactive, 'N') <> 'Y'
        """
    )
    row = rows[0] if rows else {}
    return {
        "total_items_with_stock": int(row.get("total_items") or 0),
        "total_warehouses": int(row.get("total_warehouses") or 0),
        "stock_fisico_total": _to_float(row.get("stock_fisico_total")),
        "stock_disponible_total": _to_float(row.get("stock_disponible_total")),
        "items_without_stock": int(row.get("items_without_stock") or 0),
        "negative_stock_items": int(row.get("negative_stock_items") or 0),
        "committed_over_stock_items": int(row.get("committed_over_stock_items") or 0),
        "items_with_open_orders": int(row.get("items_with_open_orders") or 0),
    }


def get_stock_item_detail(item_code: str) -> dict[str, Any]:
    stock_by_warehouse = get_stock_items(item_code=item_code, include_inactive=True, include_locked_warehouses=True, limit=10000)
    return {
        "item_code": item_code,
        "item_name": stock_by_warehouse[0]["item_name"] if stock_by_warehouse else None,
        "stock_by_warehouse": stock_by_warehouse,
        "summary": summarize_stock_records(stock_by_warehouse),
    }


def summarize_stock_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "warehouses": len({record["warehouse_code"] for record in records if record.get("warehouse_code")}),
        "stock_fisico_total": sum(record["stock_fisico"] for record in records),
        "stock_disponible_total": sum(record["stock_disponible"] for record in records),
        "stock_pedido_total": sum(record["stock_pedido"] for record in records),
        "stock_proyectado_base_total": sum(record["stock_proyectado_base"] for record in records),
        "negative_stock_count": sum(1 for record in records if record["stock_negativo"]),
        "committed_over_stock_count": sum(1 for record in records if record["comprometido_mayor_stock"]),
    }


def get_warehouse_stock_summary() -> list[dict[str, Any]]:
    rows = execute_read_query(
        """
        SELECT
            W.WhsCode AS warehouse_code,
            MAX(H.WhsName) AS warehouse_name,
            COUNT_BIG(DISTINCT CASE WHEN ISNULL(W.OnHand, 0) <> 0 THEN W.ItemCode END) AS total_items,
            SUM(CAST(ISNULL(W.OnHand, 0) AS decimal(19, 6))) AS stock_fisico_total,
            SUM(CAST(ISNULL(W.OnHand, 0) - ISNULL(W.IsCommited, 0) AS decimal(19, 6))) AS stock_disponible_total,
            SUM(CAST(ISNULL(W.OnOrder, 0) AS decimal(19, 6))) AS stock_pedido_total,
            SUM(CASE WHEN ISNULL(W.OnHand, 0) < 0 THEN 1 ELSE 0 END) AS negative_stock_items,
            SUM(CASE WHEN ISNULL(W.IsCommited, 0) > ISNULL(W.OnHand, 0) THEN 1 ELSE 0 END) AS committed_over_stock_items
        FROM OITW W
        INNER JOIN OITM I ON I.ItemCode = W.ItemCode
        LEFT JOIN OWHS H ON H.WhsCode = W.WhsCode
        WHERE I.InvntItem = 'Y' AND I.validFor = 'Y'
        GROUP BY W.WhsCode
        ORDER BY W.WhsCode
        """
    )
    return [
        {
            "warehouse_code": row.get("warehouse_code"),
            "warehouse_name": row.get("warehouse_name"),
            "total_items": int(row.get("total_items") or 0),
            "stock_fisico_total": _to_float(row.get("stock_fisico_total")),
            "stock_disponible_total": _to_float(row.get("stock_disponible_total")),
            "stock_pedido_total": _to_float(row.get("stock_pedido_total")),
            "negative_stock_items": int(row.get("negative_stock_items") or 0),
            "committed_over_stock_items": int(row.get("committed_over_stock_items") or 0),
        }
        for row in rows
    ]
