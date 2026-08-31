from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.db.session import execute_read_query


INVENTORY_SOURCES: dict[str, dict[str, Any]] = {
    "OINM": {
        "description": "Movimientos de inventario registrados en SAP",
        "expected_columns": [
            "ItemCode", "Dscription", "DocDate", "Warehouse", "InQty", "OutQty", "TransType",
            "CreatedBy", "BaseRef", "DocLineNum", "CardCode", "DocTime",
        ],
        "key_columns": ["ItemCode", "DocDate", "Warehouse", "InQty", "OutQty", "TransType"],
        "date_column": "DocDate",
    },
    "OITM": {
        "description": "Articulos",
        "expected_columns": ["ItemCode", "ItemName", "ItmsGrpCod", "InvntItem", "validFor"],
        "key_columns": ["ItemCode", "ItemName"],
        "date_column": None,
    },
    "OITW": {
        "description": "Stock por articulo y almacen",
        "expected_columns": ["ItemCode", "WhsCode", "OnHand", "IsCommited", "OnOrder"],
        "key_columns": ["ItemCode", "WhsCode", "OnHand"],
        "date_column": None,
    },
    "OWHS": {
        "description": "Almacenes",
        "expected_columns": ["WhsCode", "WhsName", "Inactive"],
        "key_columns": ["WhsCode", "WhsName"],
        "date_column": None,
    },
}

TRANSFER_TYPES = {67}
ADJUSTMENT_TYPES = {59, 60, 10000071}
CONSUMPTION_CANDIDATE_TYPES = {13, 15, 202}
NON_CONSUMPTION_REVISABLE_TYPES = {14, 16, 18, 19, 20, 21, 69, 162}
KNOWN_MOVEMENT_TYPES = CONSUMPTION_CANDIDATE_TYPES | NON_CONSUMPTION_REVISABLE_TYPES | TRANSFER_TYPES | ADJUSTMENT_TYPES
MOVEMENT_TYPE_DESCRIPTIONS: dict[int, str] = {
    13: "Factura de cliente / salida por venta",
    14: "Nota de credito de cliente / devolucion",
    15: "Entrega de cliente / salida comprometida",
    16: "Devolucion de cliente / ingreso",
    18: "Factura de proveedor / ingreso",
    19: "Nota de credito de proveedor / salida por devolucion",
    20: "Entrada de mercancias de compra",
    21: "Devolucion de mercancias de compra",
    59: "Entrada de mercancias o ajuste positivo revisable",
    60: "Salida de mercancias o ajuste negativo revisable",
    67: "Transferencia de inventario",
    162: "Revalorizacion de inventario",
    202: "Orden de fabricacion",
    10000071: "Conteo o contabilizacion de inventario revisable",
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


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def classify_movement_type(trans_type: Any) -> dict[str, Any]:
    trans_type_int = _safe_int(trans_type)
    is_transfer = trans_type_int in TRANSFER_TYPES
    is_adjustment = trans_type_int in ADJUSTMENT_TYPES
    is_known = trans_type_int in KNOWN_MOVEMENT_TYPES
    is_consumption_candidate = trans_type_int in CONSUMPTION_CANDIDATE_TYPES
    is_non_consumption_revisable = trans_type_int in NON_CONSUMPTION_REVISABLE_TYPES
    is_revisable = (trans_type_int is None) or (not is_known) or is_adjustment or is_non_consumption_revisable

    if is_transfer:
        category = "transferencia"
    elif is_adjustment:
        category = "ajuste_revisable"
    elif is_consumption_candidate:
        category = "consumo_candidato"
    elif is_non_consumption_revisable:
        category = "entrada_devolucion_o_revisable"
    else:
        category = "revisable"

    return {
        "trans_type": trans_type_int,
        "category": category,
        "is_transfer": is_transfer,
        "is_adjustment": is_adjustment,
        "is_revisable": is_revisable,
        "is_consumption_candidate": is_consumption_candidate,
        "interpretation": MOVEMENT_TYPE_DESCRIPTIONS.get(trans_type_int, "Movimiento revisable sin interpretacion definida"),
    }


def get_source_columns(table_name: str) -> list[str]:
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


def _source_type(table_name: str) -> str | None:
    rows = execute_read_query(
        """
        SELECT TABLE_TYPE AS table_type
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = :table_name
        """,
        {"table_name": table_name},
    )
    return str(rows[0]["table_type"]) if rows else None


def _row_count(table_name: str) -> int | None:
    if table_name not in INVENTORY_SOURCES:
        return None
    rows = execute_read_query(f"SELECT COUNT_BIG(*) AS record_count FROM {table_name}")
    return int(rows[0]["record_count"]) if rows else None


def _date_range(table_name: str, date_column: str | None) -> dict[str, str | None]:
    if not date_column:
        return {"min_date": None, "max_date": None}
    rows = execute_read_query(
        f"SELECT MIN({date_column}) AS min_date, MAX({date_column}) AS max_date FROM {table_name}"
    )
    row = rows[0] if rows else {}
    return {"min_date": _to_iso(row.get("min_date")), "max_date": _to_iso(row.get("max_date"))}


def diagnose_inventory_sources() -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for table_name, config in INVENTORY_SOURCES.items():
        columns = get_source_columns(table_name)
        expected = list(config["expected_columns"])
        key_columns = [column for column in config["key_columns"] if column in columns]
        missing = [column for column in expected if column not in columns]
        date_range = _date_range(table_name, config.get("date_column"))
        diagnostics.append(
            {
                "source": table_name,
                "type": _source_type(table_name),
                "description": config["description"],
                "columns": columns,
                "key_columns_found": key_columns,
                "missing_expected_columns": missing,
                "record_count": _row_count(table_name),
                "date_range": date_range,
            }
        )
    return diagnostics


def _limit_value(limit: int | None, default: int = 500) -> int:
    if limit is None:
        return default
    return max(1, min(int(limit), 5000))


def get_inventory_date_range() -> dict[str, Any]:
    rows = execute_read_query(
        """
        SELECT MIN(DocDate) AS min_date, MAX(DocDate) AS max_date, COUNT_BIG(*) AS movement_count
        FROM OINM
        """
    )
    row = rows[0] if rows else {}
    return {
        "min_date": _to_iso(row.get("min_date")),
        "max_date": _to_iso(row.get("max_date")),
        "movement_count": int(row.get("movement_count") or 0),
    }


def get_inventory_movement_types() -> list[dict[str, Any]]:
    rows = execute_read_query(
        """
        SELECT
            TransType AS trans_type,
            COUNT_BIG(*) AS movement_count,
            SUM(CAST(ISNULL(InQty, 0) AS decimal(19, 6))) AS total_in_qty,
            SUM(CAST(ISNULL(OutQty, 0) AS decimal(19, 6))) AS total_out_qty,
            MIN(DocDate) AS first_date,
            MAX(DocDate) AS last_date,
            MIN(BASE_REF) AS sample_base_ref
        FROM OINM
        GROUP BY TransType
        ORDER BY movement_count DESC
        """
    )
    results: list[dict[str, Any]] = []
    for row in rows:
        classification = classify_movement_type(row.get("trans_type"))
        results.append(
            {
                "trans_type": classification["trans_type"],
                "movement_count": int(row.get("movement_count") or 0),
                "total_in_qty": _to_float(row.get("total_in_qty")),
                "total_out_qty": _to_float(row.get("total_out_qty")),
                "first_date": _to_iso(row.get("first_date")),
                "last_date": _to_iso(row.get("last_date")),
                "sample_base_ref": row.get("sample_base_ref"),
                "category": classification["category"],
                "is_transfer": classification["is_transfer"],
                "is_adjustment": classification["is_adjustment"],
                "is_revisable": classification["is_revisable"],
                "interpretation": classification["interpretation"],
            }
        )
    return results


def get_inventory_movements_summary() -> dict[str, Any]:
    date_range = get_inventory_date_range()
    movement_types = get_inventory_movement_types()
    return {
        "date_range": {"start_date": date_range["min_date"], "end_date": date_range["max_date"]},
        "movement_count": date_range["movement_count"],
        "movement_type_count": len(movement_types),
        "transfer_type_count": sum(1 for item in movement_types if item["is_transfer"]),
        "adjustment_type_count": sum(1 for item in movement_types if item["is_adjustment"]),
        "revisable_type_count": sum(1 for item in movement_types if item["is_revisable"]),
    }


def get_inventory_movements_by_month(
    item_code: str | None = None,
    warehouse: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 500,
) -> list[dict[str, Any]]:
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            ItemCode AS item_code,
            MAX(Dscription) AS item_description,
            Warehouse AS warehouse,
            YEAR(DocDate) AS year,
            MONTH(DocDate) AS month,
            CONVERT(char(7), DocDate, 120) AS period,
            SUM(CAST(ISNULL(InQty, 0) AS decimal(19, 6))) AS total_in_qty,
            SUM(CAST(ISNULL(OutQty, 0) AS decimal(19, 6))) AS total_out_qty,
            COUNT_BIG(*) AS movement_count,
            MIN(DocDate) AS first_date,
            MAX(DocDate) AS last_date
        FROM OINM
        WHERE (:item_code IS NULL OR ItemCode = :item_code)
          AND (:warehouse IS NULL OR Warehouse = :warehouse)
          AND (:start_date IS NULL OR DocDate >= :start_date)
          AND (:end_date IS NULL OR DocDate <= :end_date)
        GROUP BY ItemCode, Warehouse, YEAR(DocDate), MONTH(DocDate), CONVERT(char(7), DocDate, 120)
        ORDER BY period DESC, item_code, warehouse
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code, "warehouse": warehouse, "start_date": start_date, "end_date": end_date},
    )
    return [
        {
            "item_code": row.get("item_code"),
            "item_description": row.get("item_description"),
            "warehouse": row.get("warehouse"),
            "year": int(row.get("year") or 0),
            "month": int(row.get("month") or 0),
            "period": row.get("period"),
            "total_in_qty": _to_float(row.get("total_in_qty")),
            "total_out_qty": _to_float(row.get("total_out_qty")),
            "movement_count": int(row.get("movement_count") or 0),
            "first_date": _to_iso(row.get("first_date")),
            "last_date": _to_iso(row.get("last_date")),
        }
        for row in rows
    ]


def get_inventory_movements_by_item(item_code: str, limit: int | None = 50) -> list[dict[str, Any]]:
    safe_limit = _limit_value(limit, default=50)
    rows = execute_read_query(
        f"""
        SELECT
            ItemCode AS item_code,
            Dscription AS item_description,
            DocDate AS doc_date,
            Warehouse AS warehouse,
            CAST(ISNULL(InQty, 0) AS decimal(19, 6)) AS in_qty,
            CAST(ISNULL(OutQty, 0) AS decimal(19, 6)) AS out_qty,
            TransType AS trans_type,
            BASE_REF AS base_ref,
            CreatedBy AS created_by
        FROM OINM
        WHERE ItemCode = :item_code
        ORDER BY DocDate DESC
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code},
    )
    movements: list[dict[str, Any]] = []
    for row in rows:
        classification = classify_movement_type(row.get("trans_type"))
        movements.append(
            {
                "item_code": row.get("item_code"),
                "item_description": row.get("item_description"),
                "doc_date": _to_iso(row.get("doc_date")),
                "warehouse": row.get("warehouse"),
                "in_qty": _to_float(row.get("in_qty")),
                "out_qty": _to_float(row.get("out_qty")),
                "trans_type": classification["trans_type"],
                "movement_category": classification["category"],
                "base_ref": row.get("base_ref"),
                "created_by": row.get("created_by"),
            }
        )
    return movements