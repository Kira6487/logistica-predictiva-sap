from fastapi.testclient import TestClient

from app.api.routes import consumption
from app.main import app


client = TestClient(app)


def test_consumption_summary_endpoint(monkeypatch) -> None:
    def fake_summary(**kwargs):
        return {
            "date_range": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "total_items_with_consumption": 1,
            "total_warehouses": 1,
            "total_periods": 1,
            "total_consumed_quantity": 8.0,
            "total_movements_analyzed": 2,
            "excluded_transfer_movements": 1,
            "revisable_movements": 1,
            "top_items_by_consumption": [
                {"item_code": "A001", "item_description": "Articulo A", "consumed_quantity": 8.0, "movement_count": 2}
            ],
            "top_warehouses_by_consumption": [
                {"warehouse": "01", "consumed_quantity": 8.0, "movement_count": 2}
            ],
        }

    monkeypatch.setattr(consumption, "get_consumption_summary", fake_summary)
    response = client.get("/consumption/summary")

    assert response.status_code == 200
    assert response.json()["total_consumed_quantity"] == 8.0


def test_monthly_consumption_endpoint(monkeypatch) -> None:
    def fake_monthly(**kwargs):
        return [
            {
                "item_code": "A001",
                "item_description": "Articulo A",
                "warehouse": "01",
                "year": 2026,
                "month": 1,
                "period": "2026-01",
                "consumed_quantity": 8.0,
                "movement_count": 2,
                "first_date": "2026-01-10",
                "last_date": "2026-01-20",
                "quality_flags": [],
            }
        ]

    monkeypatch.setattr(consumption, "get_monthly_consumption", fake_monthly)
    response = client.get("/consumption/monthly?item_code=A001&limit=10")

    assert response.status_code == 200
    assert response.json()[0]["period"] == "2026-01"


def test_item_consumption_endpoint(monkeypatch) -> None:
    def fake_item(item_code: str):
        return {
            "item": {"item_code": item_code, "item_name": "Articulo A"},
            "monthly_consumption": [],
            "warehouses": ["01"],
            "summary": {"total_consumed_quantity": 0.0, "total_movements": 0, "periods": 0},
            "recent_movements": [],
            "quality_warnings": [],
        }

    monkeypatch.setattr(consumption, "get_item_consumption_detail", fake_item)
    response = client.get("/consumption/item/A001")

    assert response.status_code == 200
    assert response.json()["item"]["item_code"] == "A001"


def test_movement_types_endpoint(monkeypatch) -> None:
    def fake_types():
        return [
            {
                "trans_type": 67,
                "movement_count": 10,
                "total_in_qty": 5.0,
                "total_out_qty": 5.0,
                "first_date": "2026-01-01",
                "last_date": "2026-01-31",
                "sample_base_ref": "T1",
                "category": "transferencia",
                "is_transfer": True,
                "is_adjustment": False,
                "is_revisable": False,
                "interpretation": "Transferencia de inventario",
            }
        ]

    monkeypatch.setattr(consumption, "get_consumption_movement_types", fake_types)
    response = client.get("/consumption/movement-types")

    assert response.status_code == 200
    assert response.json()[0]["is_transfer"] is True