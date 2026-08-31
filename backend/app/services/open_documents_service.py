from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.db.session import execute_read_query
from app.services.stock_position_service import get_table_columns, get_table_type, table_exists


OPEN_DOCUMENT_SOURCES: dict[str, dict[str, Any]] = {
    "OPOR": {"description": "Ordenes de compra abiertas", "expected_columns": ["DocEntry", "DocNum", "DocDate", "DocDueDate", "CardCode", "CardName", "DocStatus", "CANCELED", "DocCur"]},
    "POR1": {"description": "Lineas de ordenes de compra abiertas", "expected_columns": ["DocEntry", "LineNum", "ItemCode", "Dscription", "WhsCode", "OpenQty", "Quantity", "DelivrdQty", "LineStatus", "Currency", "Price", "LineTotal"]},
    "ORDR": {"description": "Ordenes de venta abiertas", "expected_columns": ["DocEntry", "DocNum", "DocDate", "DocDueDate", "CardCode", "CardName", "DocStatus", "CANCELED", "DocCur"]},
    "RDR1": {"description": "Lineas de ordenes de venta abiertas", "expected_columns": ["DocEntry", "LineNum", "ItemCode", "Dscription", "WhsCode", "OpenQty", "Quantity", "DelivrdQty", "LineStatus", "Currency", "Price", "LineTotal"]},
    "OWOR": {"description": "Ordenes de fabricacion", "expected_columns": ["DocEntry", "DocNum", "PostDate", "DueDate", "ItemCode", "ProdName", "Warehouse", "PlannedQty", "CmpltQty", "Status"]},
    "WOR1": {"description": "Componentes de ordenes de fabricacion", "expected_columns": ["DocEntry", "LineNum", "ItemCode", "ItemName", "wareHouse", "PlannedQty", "IssuedQty"]},
    "OWTQ": {"description": "Solicitudes de traslado", "expected_columns": ["DocEntry", "DocNum", "DocDate", "DocDueDate", "CardCode", "CardName", "DocStatus", "CANCELED", "DocCur"]},
    "WTQ1": {"description": "Lineas de solicitudes de traslado", "expected_columns": ["DocEntry", "LineNum", "ItemCode", "Dscription", "WhsCode", "FromWhsCod", "OpenQty", "Quantity", "LineStatus", "Currency", "Price", "LineTotal"]},
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
    return max(1, min(int(limit), 100000))


def diagnose_open_document_sources() -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for table_name, config in OPEN_DOCUMENT_SOURCES.items():
        source_type = get_table_type(table_name)
        columns = get_table_columns(table_name) if source_type else []
        diagnostics.append(
            {
                "source": table_name,
                "type": source_type,
                "description": config["description"],
                "exists": source_type is not None,
                "columns": columns,
                "key_columns_found": [column for column in config["expected_columns"] if column in columns],
                "missing_expected_columns": [column for column in config["expected_columns"] if column not in columns],
                "record_count": _table_count(table_name) if source_type else 0,
            }
        )
    return diagnostics


def _table_count(table_name: str) -> int:
    rows = execute_read_query(f"SELECT COUNT_BIG(*) AS record_count FROM {table_name}")
    return int(rows[0]["record_count"] or 0) if rows else 0


def _line_open_qty_expression(table_name: str) -> str:
    columns = set(get_table_columns(table_name))
    if "OpenQty" in columns:
        return "ISNULL(L.OpenQty, 0)"
    if "Quantity" in columns and "DelivrdQty" in columns:
        return "ISNULL(L.Quantity, 0) - ISNULL(L.DelivrdQty, 0)"
    if "Quantity" in columns:
        return "ISNULL(L.Quantity, 0)"
    return "0"


def _base_document_where(alias: str = "H") -> str:
    return f"ISNULL({alias}.CANCELED, 'N') = 'N' AND ISNULL({alias}.DocStatus, 'O') = 'O'"


def normalize_open_document(row: dict[str, Any]) -> dict[str, Any]:
    cantidad_abierta = _to_float(row.get("cantidad_abierta"))
    return {
        "tipo_documento": row.get("tipo_documento"),
        "doc_entry": int(row["doc_entry"]) if row.get("doc_entry") is not None else None,
        "doc_num": int(row["doc_num"]) if row.get("doc_num") is not None else None,
        "line_num": int(row["line_num"]) if row.get("line_num") is not None else None,
        "fecha_documento": _to_iso(row.get("fecha_documento")),
        "fecha_entrega": _to_iso(row.get("fecha_entrega")),
        "card_code": row.get("card_code"),
        "card_name": row.get("card_name"),
        "item_code": row.get("item_code"),
        "item_name": row.get("item_name"),
        "warehouse_code": row.get("warehouse_code"),
        "warehouse_name": row.get("warehouse_name"),
        "cantidad_abierta": cantidad_abierta,
        "moneda": row.get("moneda"),
        "precio": _to_float(row.get("precio")),
        "total_linea": _to_float(row.get("total_linea")),
        "estado_documento": row.get("estado_documento"),
        "estado_linea": row.get("estado_linea"),
        "direction": row.get("direction"),
        "source_table": row.get("source_table"),
    }


def get_open_purchase_orders(
    item_code: str | None = None,
    warehouse: str | None = None,
    card_code: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    if not (table_exists("OPOR") and table_exists("POR1")):
        return []
    open_qty = _line_open_qty_expression("POR1")
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            'orden_compra' AS tipo_documento,
            H.DocEntry AS doc_entry,
            H.DocNum AS doc_num,
            L.LineNum AS line_num,
            H.DocDate AS fecha_documento,
            H.DocDueDate AS fecha_entrega,
            H.CardCode AS card_code,
            H.CardName AS card_name,
            L.ItemCode AS item_code,
            L.Dscription AS item_name,
            L.WhsCode AS warehouse_code,
            WH.WhsName AS warehouse_name,
            CAST({open_qty} AS decimal(19, 6)) AS cantidad_abierta,
            COALESCE(L.Currency, H.DocCur) AS moneda,
            CAST(ISNULL(L.Price, 0) AS decimal(19, 6)) AS precio,
            CAST(ISNULL(L.LineTotal, 0) AS decimal(19, 6)) AS total_linea,
            H.DocStatus AS estado_documento,
            L.LineStatus AS estado_linea,
            'entrada' AS direction,
            'OPOR/POR1' AS source_table
        FROM OPOR H
        INNER JOIN POR1 L ON L.DocEntry = H.DocEntry
        LEFT JOIN OWHS WH ON WH.WhsCode = L.WhsCode
        WHERE {_base_document_where('H')}
          AND ISNULL(L.LineStatus, 'O') = 'O'
          AND {open_qty} > 0
          AND (:item_code IS NULL OR L.ItemCode = :item_code)
          AND (:warehouse IS NULL OR L.WhsCode = :warehouse)
          AND (:card_code IS NULL OR H.CardCode = :card_code)
          AND (:start_date IS NULL OR H.DocDate >= :start_date)
          AND (:end_date IS NULL OR H.DocDate <= :end_date)
        ORDER BY H.DocDueDate, H.DocNum, L.LineNum
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code, "warehouse": warehouse, "card_code": card_code, "start_date": start_date, "end_date": end_date},
    )
    return [normalize_open_document(row) for row in rows]


def get_open_sales_orders(
    item_code: str | None = None,
    warehouse: str | None = None,
    card_code: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    if not (table_exists("ORDR") and table_exists("RDR1")):
        return []
    open_qty = _line_open_qty_expression("RDR1")
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            'orden_venta' AS tipo_documento,
            H.DocEntry AS doc_entry,
            H.DocNum AS doc_num,
            L.LineNum AS line_num,
            H.DocDate AS fecha_documento,
            H.DocDueDate AS fecha_entrega,
            H.CardCode AS card_code,
            H.CardName AS card_name,
            L.ItemCode AS item_code,
            L.Dscription AS item_name,
            L.WhsCode AS warehouse_code,
            WH.WhsName AS warehouse_name,
            CAST({open_qty} AS decimal(19, 6)) AS cantidad_abierta,
            COALESCE(L.Currency, H.DocCur) AS moneda,
            CAST(ISNULL(L.Price, 0) AS decimal(19, 6)) AS precio,
            CAST(ISNULL(L.LineTotal, 0) AS decimal(19, 6)) AS total_linea,
            H.DocStatus AS estado_documento,
            L.LineStatus AS estado_linea,
            'salida' AS direction,
            'ORDR/RDR1' AS source_table
        FROM ORDR H
        INNER JOIN RDR1 L ON L.DocEntry = H.DocEntry
        LEFT JOIN OWHS WH ON WH.WhsCode = L.WhsCode
        WHERE {_base_document_where('H')}
          AND ISNULL(L.LineStatus, 'O') = 'O'
          AND {open_qty} > 0
          AND (:item_code IS NULL OR L.ItemCode = :item_code)
          AND (:warehouse IS NULL OR L.WhsCode = :warehouse)
          AND (:card_code IS NULL OR H.CardCode = :card_code)
          AND (:start_date IS NULL OR H.DocDate >= :start_date)
          AND (:end_date IS NULL OR H.DocDate <= :end_date)
        ORDER BY H.DocDueDate, H.DocNum, L.LineNum
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code, "warehouse": warehouse, "card_code": card_code, "start_date": start_date, "end_date": end_date},
    )
    return [normalize_open_document(row) for row in rows]


def get_open_production_orders(item_code: str | None = None, warehouse: str | None = None, limit: int | None = 1000) -> list[dict[str, Any]]:
    if not table_exists("OWOR"):
        return []
    columns = set(get_table_columns("OWOR"))
    required = {"DocEntry", "DocNum", "ItemCode", "PlannedQty", "CmpltQty", "Status"}
    if not required.issubset(columns):
        return []
    due_column = "DueDate" if "DueDate" in columns else "PostDate"
    warehouse_column = "Warehouse" if "Warehouse" in columns else "NULL"
    name_column = "ProdName" if "ProdName" in columns else "ItemCode"
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            'orden_fabricacion' AS tipo_documento,
            H.DocEntry AS doc_entry,
            H.DocNum AS doc_num,
            0 AS line_num,
            H.PostDate AS fecha_documento,
            H.{due_column} AS fecha_entrega,
            CAST(NULL AS nvarchar(50)) AS card_code,
            CAST(NULL AS nvarchar(200)) AS card_name,
            H.ItemCode AS item_code,
            H.{name_column} AS item_name,
            H.{warehouse_column} AS warehouse_code,
            WH.WhsName AS warehouse_name,
            CAST(ISNULL(H.PlannedQty, 0) - ISNULL(H.CmpltQty, 0) AS decimal(19, 6)) AS cantidad_abierta,
            CAST(NULL AS nvarchar(10)) AS moneda,
            CAST(0 AS decimal(19, 6)) AS precio,
            CAST(0 AS decimal(19, 6)) AS total_linea,
            H.Status AS estado_documento,
            H.Status AS estado_linea,
            'entrada' AS direction,
            'OWOR' AS source_table
        FROM OWOR H
        LEFT JOIN OWHS WH ON WH.WhsCode = H.{warehouse_column}
        WHERE H.Status NOT IN ('L', 'C')
          AND ISNULL(H.PlannedQty, 0) - ISNULL(H.CmpltQty, 0) > 0
          AND (:item_code IS NULL OR H.ItemCode = :item_code)
          AND (:warehouse IS NULL OR H.{warehouse_column} = :warehouse)
        ORDER BY H.{due_column}, H.DocNum
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code, "warehouse": warehouse},
    )
    return [normalize_open_document(row) for row in rows]


def get_open_transfer_requests(item_code: str | None = None, warehouse: str | None = None, limit: int | None = 1000) -> list[dict[str, Any]]:
    if not (table_exists("OWTQ") and table_exists("WTQ1")):
        return []
    columns = set(get_table_columns("WTQ1"))
    if "OpenQty" not in columns:
        return []
    safe_limit = _limit_value(limit)
    rows = execute_read_query(
        f"""
        SELECT
            'solicitud_traslado' AS tipo_documento,
            H.DocEntry AS doc_entry,
            H.DocNum AS doc_num,
            L.LineNum AS line_num,
            H.DocDate AS fecha_documento,
            H.DocDueDate AS fecha_entrega,
            H.CardCode AS card_code,
            H.CardName AS card_name,
            L.ItemCode AS item_code,
            L.Dscription AS item_name,
            L.WhsCode AS warehouse_code,
            WH.WhsName AS warehouse_name,
            CAST(ISNULL(L.OpenQty, 0) AS decimal(19, 6)) AS cantidad_abierta,
            COALESCE(L.Currency, H.DocCur) AS moneda,
            CAST(ISNULL(L.Price, 0) AS decimal(19, 6)) AS precio,
            CAST(ISNULL(L.LineTotal, 0) AS decimal(19, 6)) AS total_linea,
            H.DocStatus AS estado_documento,
            L.LineStatus AS estado_linea,
            'entrada' AS direction,
            'OWTQ/WTQ1' AS source_table
        FROM OWTQ H
        INNER JOIN WTQ1 L ON L.DocEntry = H.DocEntry
        LEFT JOIN OWHS WH ON WH.WhsCode = L.WhsCode
        WHERE {_base_document_where('H')}
          AND ISNULL(L.LineStatus, 'O') = 'O'
          AND ISNULL(L.OpenQty, 0) > 0
          AND (:item_code IS NULL OR L.ItemCode = :item_code)
          AND (:warehouse IS NULL OR L.WhsCode = :warehouse)
        ORDER BY H.DocDueDate, H.DocNum, L.LineNum
        OFFSET 0 ROWS FETCH NEXT {safe_limit} ROWS ONLY
        """,
        {"item_code": item_code, "warehouse": warehouse},
    )
    return [normalize_open_document(row) for row in rows]


def get_open_documents(
    item_code: str | None = None,
    warehouse: str | None = None,
    document_type: str | None = None,
    card_code: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    document_type = document_type.lower() if document_type else None
    per_source_limit = _limit_value(limit)
    documents: list[dict[str, Any]] = []
    if document_type in (None, "orden_compra", "compra", "oc"):
        documents.extend(get_open_purchase_orders(item_code, warehouse, card_code, start_date, end_date, per_source_limit))
    if document_type in (None, "orden_venta", "venta", "ov"):
        documents.extend(get_open_sales_orders(item_code, warehouse, card_code, start_date, end_date, per_source_limit))
    if document_type in (None, "orden_fabricacion", "fabricacion", "of"):
        documents.extend(get_open_production_orders(item_code, warehouse, per_source_limit))
    if document_type in (None, "solicitud_traslado", "traslado"):
        documents.extend(get_open_transfer_requests(item_code, warehouse, per_source_limit))
    return documents[:per_source_limit]


def summarize_open_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = defaultdict(int)
    entrada = 0.0
    salida = 0.0
    affected_items: set[str] = set()
    for document in documents:
        by_type[str(document["tipo_documento"])] += 1
        affected_items.add(str(document["item_code"]))
        if document.get("direction") == "entrada":
            entrada += document["cantidad_abierta"]
        elif document.get("direction") == "salida":
            salida += document["cantidad_abierta"]
    return {
        "open_purchase_orders": by_type.get("orden_compra", 0),
        "open_sales_orders": by_type.get("orden_venta", 0),
        "open_production_orders": by_type.get("orden_fabricacion", 0),
        "open_transfer_requests": by_type.get("solicitud_traslado", 0),
        "open_incoming_quantity": entrada,
        "open_outgoing_quantity": salida,
        "affected_items": len(affected_items),
        "total_documents": len(documents),
    }


def get_open_documents_summary() -> dict[str, Any]:
    return summarize_open_documents(get_open_documents(limit=100000))


def get_open_documents_by_item(item_code: str) -> dict[str, Any]:
    documents = get_open_documents(item_code=item_code, limit=100000)
    return {"item_code": item_code, "documents": documents, "summary": summarize_open_documents(documents)}


def aggregate_open_documents_by_item_warehouse(documents: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"entradas_abiertas": 0.0, "salidas_abiertas": 0.0})
    for document in documents:
        key = (str(document.get("item_code")), str(document.get("warehouse_code")))
        if document.get("direction") == "entrada":
            totals[key]["entradas_abiertas"] += document["cantidad_abierta"]
        elif document.get("direction") == "salida":
            totals[key]["salidas_abiertas"] += document["cantidad_abierta"]
    return totals