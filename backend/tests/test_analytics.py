from datetime import date

import pandas as pd

from app.services.eda_service import (
    assign_abc_classes,
    calculate_item_metrics,
    classify_xyz_value,
    combine_abc_xyz,
)


def test_abc_classification_uses_80_95_thresholds() -> None:
    frame = pd.DataFrame(
        {
            "item_code": ["A", "B", "C"],
            "net_quantity_total": [80.0, 15.0, 5.0],
        }
    )

    result = assign_abc_classes(
        frame,
        "net_quantity_total",
        "abc_quantity_class",
    ).set_index("item_code")

    assert result.loc["A", "abc_quantity_class"] == "A"
    assert result.loc["B", "abc_quantity_class"] == "B"
    assert result.loc["C", "abc_quantity_class"] == "C"


def test_xyz_classification_by_coefficient_of_variation() -> None:
    common = {
        "months_with_sales": 12,
        "min_months": 12,
        "is_intermittent": False,
        "is_negative_demand": False,
    }

    assert classify_xyz_value(coefficient_of_variation=0.5, **common) == "X"
    assert classify_xyz_value(coefficient_of_variation=0.8, **common) == "Y"
    assert classify_xyz_value(coefficient_of_variation=1.2, **common) == "Z"


def test_xyz_marks_insufficient_history_and_negative_demand() -> None:
    assert (
        classify_xyz_value(
            coefficient_of_variation=0.2,
            months_with_sales=11,
            min_months=12,
            is_intermittent=False,
            is_negative_demand=False,
        )
        == "INSUFFICIENT_HISTORY"
    )
    assert (
        classify_xyz_value(
            coefficient_of_variation=0.2,
            months_with_sales=12,
            min_months=12,
            is_intermittent=False,
            is_negative_demand=True,
        )
        == "REVIEW_REQUIRED"
    )


def test_item_metrics_detect_negative_demand() -> None:
    rows = [
        {
            "period": "2025-01",
            "item_code": "NEG",
            "item_name": "Artículo negativo",
            "item_group": "Prueba",
            "warehouse_code": "01",
            "net_quantity": -2.0,
            "net_sales_total": -20.0,
        }
    ]

    result = calculate_item_metrics(
        rows,
        date(2025, 1, 1),
        date(2025, 12, 31),
    ).iloc[0]

    assert bool(result["is_negative_demand"]) is True
    assert result["months_with_sales"] == 0
    assert result["data_quality_status"] == "NEGATIVE_DEMAND"


def test_combined_abc_xyz_labels() -> None:
    assert combine_abc_xyz("A", "X") == "AX"
    assert combine_abc_xyz("C", "INSUFFICIENT_HISTORY") == (
        "C-INSUFFICIENT_HISTORY"
    )
    assert combine_abc_xyz("A", "INTERMITTENT") == "A-INTERMITTENT"
