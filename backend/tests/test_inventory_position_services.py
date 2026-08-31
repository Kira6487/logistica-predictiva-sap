from app.services.inventory_position_service import build_inventory_position_record
from app.services.open_documents_service import aggregate_open_documents_by_item_warehouse, normalize_open_document, summarize_open_documents
from app.services.stock_position_service import build_stock_position_record


def test_stock_record_calculates_available_and_projected_base() -> None:
    record = build_stock_position_record(
        {
            "item_code": "A001",
            "item_name": "Articulo A",
            "warehouse_code": "01",
            "warehouse_name": "Central",
            "stock_fisico": 10,
            "stock_comprometido": 3,
            "stock_pedido": 5,
            "item_inventory": "Y",
            "item_active": "Y",
            "warehouse_locked": "N",
            "warehouse_inactive": "N",
        }
    )

    assert record["stock_disponible"] == 7
    assert record["stock_proyectado_base"] == 12
    assert record["tiene_stock"] is True
    assert record["tiene_pedido_abierto"] is True
    assert record["tiene_compromiso_abierto"] is True


def test_stock_record_flags_negative_and_committed_over_stock() -> None:
    record = build_stock_position_record(
        {
            "item_code": "A002",
            "warehouse_code": "01",
            "stock_fisico": -2,
            "stock_comprometido": 4,
            "stock_pedido": 0,
        }
    )

    assert record["stock_negativo"] is True
    assert record["comprometido_mayor_stock"] is True
    assert record["stock_disponible"] == -6


def test_open_document_normalization_and_summary() -> None:
    purchase = normalize_open_document(
        {
            "tipo_documento": "orden_compra",
            "doc_entry": 1,
            "doc_num": 100,
            "line_num": 0,
            "item_code": "A001",
            "warehouse_code": "01",
            "cantidad_abierta": 5,
            "direction": "entrada",
        }
    )
    sales = normalize_open_document(
        {
            "tipo_documento": "orden_venta",
            "doc_entry": 2,
            "doc_num": 200,
            "line_num": 0,
            "item_code": "A001",
            "warehouse_code": "01",
            "cantidad_abierta": 3,
            "direction": "salida",
        }
    )

    summary = summarize_open_documents([purchase, sales])

    assert summary["open_purchase_orders"] == 1
    assert summary["open_sales_orders"] == 1
    assert summary["open_incoming_quantity"] == 5
    assert summary["open_outgoing_quantity"] == 3


def test_open_documents_aggregate_by_item_and_warehouse() -> None:
    documents = [
        {"item_code": "A001", "warehouse_code": "01", "cantidad_abierta": 5, "direction": "entrada"},
        {"item_code": "A001", "warehouse_code": "01", "cantidad_abierta": 2, "direction": "salida"},
        {"item_code": "A001", "warehouse_code": "02", "cantidad_abierta": 4, "direction": "entrada"},
    ]

    totals = aggregate_open_documents_by_item_warehouse(documents)

    assert totals[("A001", "01")]["entradas_abiertas"] == 5
    assert totals[("A001", "01")]["salidas_abiertas"] == 2
    assert totals[("A001", "02")]["entradas_abiertas"] == 4


def test_inventory_position_projected_with_open_documents() -> None:
    stock_record = build_stock_position_record(
        {
            "item_code": "A001",
            "warehouse_code": "01",
            "stock_fisico": 10,
            "stock_comprometido": 3,
            "stock_pedido": 5,
        }
    )

    position = build_inventory_position_record(stock_record, {"entradas_abiertas": 8, "salidas_abiertas": 4})

    assert position["stock_disponible"] == 7
    assert position["stock_proyectado_con_partidas"] == 11