from __future__ import annotations


def calculate_coverage_days(
    available_stock: float,
    average_daily_demand: float,
) -> float | None:
    if average_daily_demand <= 0:
        return None
    if available_stock <= 0:
        return 0.0
    return max(0.0, available_stock / average_daily_demand)


def classify_stock_status(
    *,
    coverage_days: float | None,
    forecast_quantity: float,
    available_stock: float,
    forecast_recommended: bool,
) -> str:
    if not forecast_recommended:
        return "NOT_RECOMMENDED"
    if forecast_quantity > 0 and available_stock <= 0:
        return "NO_STOCK_WITH_DEMAND"
    if forecast_quantity <= 0:
        return "NO_DEMAND"
    if coverage_days is not None and coverage_days < 30:
        return "CRITICAL"
    if coverage_days is not None and coverage_days < 60:
        return "REVIEW"
    if coverage_days is not None and coverage_days > 180:
        return "OVERSTOCK"
    return "HEALTHY"
