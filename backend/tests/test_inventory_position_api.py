from fastapi.testclient import TestClient

from app.api.routes import inventory_position, open_documents, stock
from app.main import app


client = TestClient(app)


def test_stock_summary_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        stock,
        "get_stock_summary",
        lambda: {
            "total_items_with_stock": 1,
            "total_warehouses": 1,
            "stock_fisico_total": 10.0,
            "stock_disponible_total": 7.0,
            "items_without_stock": 0,
            "negative_stock_items": 0,
            "committed_over_stock_items": 0,
            "items_with_open_orders": 1,
        },
    )

    response = client.get("/stock/summary")

    assert response.status_code == 200
    assert response.json()["stock_disponible_total"] == 7.0


def test_open_documents_summary_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        open_documents,
        "get_open_documents_summary",
        lambda: {
            "open_purchase_orders": 1,
            "open_sales_orders": 1,
            "open_production_orders": 0,
            "open_transfer_requests": 0,
            "open_incoming_quantity": 5.0,
            "open_outgoing_quantity": 3.0,
            "affected_items": 1,
            "total_documents": 2,
        },
    )

    response = client.get("/open-documents/summary")

    assert response.status_code == 200
    assert response.json()["open_incoming_quantity"] == 5.0


def test_inventory_position_item_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        inventory_position,
        "get_inventory_position_for_item",
        lambda item_code: {
            "item_code": item_code,
            "item_name": "Articulo A",
            "position_by_warehouse": [],
            "open_documents": [],
            "summary": {
                "warehouses": 0,
                "stock_fisico_total": 0.0,
                "stock_disponible_total": 0.0,
                "entradas_abiertas_total": 0.0,
                "salidas_abiertas_total": 0.0,
                "stock_proyectado_con_partidas_total": 0.0,
                "open_documents": {
                    "open_purchase_orders": 0,
                    "open_sales_orders": 0,
                    "open_production_orders": 0,
                    "open_transfer_requests": 0,
                    "open_incoming_quantity": 0.0,
                    "open_outgoing_quantity": 0.0,
                    "affected_items": 0,
                    "total_documents": 0,
                },
            },
        },
    )

    response = client.get("/inventory-position/item/A001")

    assert response.status_code == 200
    assert response.json()["item_code"] == "A001"