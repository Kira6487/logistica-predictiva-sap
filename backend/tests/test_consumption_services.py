from datetime import date

import pytest

from app.db.session import ReadOnlyQueryError, ensure_read_only_query
from app.services.consumption_history_service import build_monthly_consumption_records
from app.services.inventory_movements_service import classify_movement_type


SAMPLE_MOVEMENTS = [
    {
        "item_code": "A001",
        "item_description": "Articulo A",
        "warehouse": "01",
        "doc_date": date(2026, 1, 10),
        "out_qty": 5,
        "trans_type": 15,
    },
    {
        "item_code": "A001",
        "item_description": "Articulo A",
        "warehouse": "01",
        "doc_date": date(2026, 1, 20),
        "out_qty": 3,
        "trans_type": 15,
    },
    {
        "item_code": "A001",
        "item_description": "Articulo A",
        "warehouse": "01",
        "doc_date": date(2026, 1, 21),
        "out_qty": 99,
        "trans_type": 67,
    },
    {
        "item_code": "A001",
        "item_description": "Articulo A",
        "warehouse": "01",
        "doc_date": date(2026, 1, 22),
        "out_qty": 7,
        "trans_type": 60,
    },
    {
        "item_code": "A001",
        "item_description": "Articulo A",
        "warehouse": "02",
        "doc_date": date(2026, 2, 1),
        "out_qty": 4,
        "trans_type": 9999,
    },
]


def test_monthly_aggregation_excludes_transfers_and_adjustments_by_default() -> None:
    records = build_monthly_consumption_records(SAMPLE_MOVEMENTS)

    january = [record for record in records if record["period"] == "2026-01"]

    assert len(january) == 1
    assert january[0]["consumed_quantity"] == 8
    assert january[0]["movement_count"] == 2
    assert january[0]["first_date"] == "2026-01-10"
    assert january[0]["last_date"] == "2026-01-20"


def test_monthly_aggregation_can_include_transfer_and_adjustment_flags() -> None:
    records = build_monthly_consumption_records(
        SAMPLE_MOVEMENTS,
        include_transfers=True,
        include_adjustments=True,
    )
    january = [record for record in records if record["period"] == "2026-01"][0]

    assert january["consumed_quantity"] == 114
    assert "incluye_transferencias" in january["quality_flags"]
    assert "incluye_ajustes" in january["quality_flags"]


def test_unknown_movement_type_is_excluded_from_consumption_by_default() -> None:
    records = build_monthly_consumption_records(SAMPLE_MOVEMENTS)

    assert [record for record in records if record["period"] == "2026-02"] == []


def test_period_format_is_yyyy_mm() -> None:
    records = build_monthly_consumption_records(SAMPLE_MOVEMENTS)

    assert all(len(record["period"]) == 7 for record in records)
    assert all(record["period"][4] == "-" for record in records)


def test_movement_type_classification_identifies_transfer_and_adjustment() -> None:
    assert classify_movement_type(67)["is_transfer"] is True
    assert classify_movement_type(60)["is_adjustment"] is True
    assert classify_movement_type(9999)["is_revisable"] is True


def test_read_only_guard_rejects_write_statement() -> None:
    with pytest.raises(ReadOnlyQueryError):
        ensure_read_only_query("DELETE FROM OINM")