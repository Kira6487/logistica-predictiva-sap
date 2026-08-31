from __future__ import annotations

from typing import Any

from app.services.open_documents_service import aggregate_open_documents_by_item_warehouse, get_open_documents, summarize_open_documents
from app.services.stock_position_service import get_stock_item_detail, get_stock_items, get_stock_summary


def build_inventory_position_record(stock_record: dict[str, Any], open_totals: dict[str, float] | None = None) -> dict[str, Any]:
    open_totals = open_totals or {"entradas_abiertas": 0.0, "salidas_abiertas": 0.0}
    entradas = float(open_totals.get("entradas_abiertas", 0.0))
    salidas = float(open_totals.get("salidas_abiertas", 0.0))
    stock_disponible = float(stock_record["stock_disponible"])
    return {
        **stock_record,
        "stock_comprometido_sap": stock_record["stock_comprometido"],
        "stock_pedido_sap": stock_record["stock_pedido"],
        "entradas_abiertas": entradas,
        "salidas_abiertas": salidas,
        "stock_proyectado_con_partidas": stock_disponible + entradas - salidas,
    }


def get_inventory_position_for_item(item_code: str) -> dict[str, Any]:
    stock_detail = get_stock_item_detail(item_code)
    documents = get_open_documents(item_code=item_code, limit=100000)
    document_totals = aggregate_open_documents_by_item_warehouse(documents)
    position = [
        build_inventory_position_record(
            stock_record,
            document_totals.get((str(stock_record["item_code"]), str(stock_record["warehouse_code"]))),
        )
        for stock_record in stock_detail["stock_by_warehouse"]
    ]
    return {
        "item_code": item_code,
        "item_name": stock_detail["item_name"],
        "position_by_warehouse": position,
        "open_documents": documents,
        "summary": summarize_inventory_position(position, documents),
    }


def get_inventory_position_summary() -> dict[str, Any]:
    stock_summary = get_stock_summary()
    documents = get_open_documents(limit=100000)
    document_summary = summarize_open_documents(documents)
    return {
        "stock": stock_summary,
        "open_documents": document_summary,
        "stock_projected_with_open_documents_note": "Resumen general; el detalle por articulo calcula stock proyectado con partidas por almacen.",
    }


def get_inventory_positions(limit: int | None = 1000) -> list[dict[str, Any]]:
    stock_records = get_stock_items(only_with_stock=True, limit=limit)
    documents = get_open_documents(limit=100000)
    document_totals = aggregate_open_documents_by_item_warehouse(documents)
    return [
        build_inventory_position_record(
            stock_record,
            document_totals.get((str(stock_record["item_code"]), str(stock_record["warehouse_code"]))),
        )
        for stock_record in stock_records
    ]


def summarize_inventory_position(position: list[dict[str, Any]], documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "warehouses": len({record["warehouse_code"] for record in position if record.get("warehouse_code")}),
        "stock_fisico_total": sum(record["stock_fisico"] for record in position),
        "stock_disponible_total": sum(record["stock_disponible"] for record in position),
        "entradas_abiertas_total": sum(record["entradas_abiertas"] for record in position),
        "salidas_abiertas_total": sum(record["salidas_abiertas"] for record in position),
        "stock_proyectado_con_partidas_total": sum(record["stock_proyectado_con_partidas"] for record in position),
        "open_documents": summarize_open_documents(documents),
    }