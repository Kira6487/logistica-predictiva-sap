from app.services.inventory_service import calculate_stock_values
from app.services.replenishment_service import (
    calculate_priority_score,
    calculate_safety_stock,
    calculate_suggested_purchase,
    classify_recommendation,
)
from app.services.stock_status_service import (
    calculate_coverage_days,
    classify_stock_status,
)


def test_available_and_projected_stock() -> None:
    available, projected = calculate_stock_values(100, 20, 15)
    assert available == 80
    assert projected == 95


def test_coverage_days() -> None:
    assert calculate_coverage_days(60, 2) == 30
    assert calculate_coverage_days(0, 2) == 0
    assert calculate_coverage_days(60, 0) is None


def test_safety_stock_medium_class_a() -> None:
    safety, factor = calculate_safety_stock(100, "MEDIUM", "A", False)
    assert factor == 0.30
    assert safety == 30


def test_suggested_purchase_rounds_up_and_never_negative() -> None:
    raw, rounded = calculate_suggested_purchase(100, 20, 50, 10)
    assert raw == 60
    assert rounded == 60
    _, zero = calculate_suggested_purchase(10, 0, 30, 0)
    assert zero == 0


def test_stock_status_critical_and_overstock() -> None:
    assert (
        classify_stock_status(
            coverage_days=20,
            forecast_quantity=30,
            available_stock=10,
            forecast_recommended=True,
        )
        == "CRITICAL"
    )
    assert (
        classify_stock_status(
            coverage_days=200,
            forecast_quantity=30,
            available_stock=200,
            forecast_recommended=True,
        )
        == "OVERSTOCK"
    )


def test_purchase_recommendation_by_confidence() -> None:
    assert (
        classify_recommendation(
            suggested_purchase=10,
            confidence="MEDIUM",
            stock_status="CRITICAL",
            forecast_recommended=True,
        )
        == "PURCHASE_SUGGESTED"
    )
    assert (
        classify_recommendation(
            suggested_purchase=10,
            confidence="LOW",
            stock_status="CRITICAL",
            forecast_recommended=True,
        )
        == "REFERENTIAL_PURCHASE"
    )


def test_priority_score_is_bounded_and_classified() -> None:
    score, level = calculate_priority_score(
        stock_status="NO_STOCK_WITH_DEMAND",
        abc_class="A",
        confidence="MEDIUM",
        coverage_days=0,
        suggested_purchase=100,
        projected_demand=50,
        requires_review=False,
    )
    assert score == 100
    assert level == "HIGH"
