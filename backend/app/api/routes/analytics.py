from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import DatabaseConnectionError
from app.services.eda_service import (
    build_analytics,
    dataframe_records,
    load_analytics_artifacts,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsFilters:
    def __init__(
        self,
        date_from: date | None = Query(default=None),
        date_to: date | None = Query(default=None),
        item_code: str | None = Query(default=None, min_length=1, max_length=50),
        item_group: str | None = Query(default=None, min_length=1, max_length=100),
        warehouse_code: str | None = Query(
            default=None,
            min_length=1,
            max_length=20,
        ),
        min_months: int = Query(default=12, ge=1, le=120),
        abc_basis: Literal["quantity", "amount"] = Query(default="quantity"),
    ) -> None:
        self.date_from = date_from
        self.date_to = date_to
        self.item_code = item_code
        self.item_group = item_group
        self.warehouse_code = warehouse_code
        self.min_months = min_months
        self.abc_basis = abc_basis


def _analysis(filters: AnalyticsFilters):
    try:
        if (
            filters.date_from is None
            and filters.date_to is None
            and filters.item_code is None
            and filters.item_group is None
            and filters.warehouse_code is None
            and filters.min_months == 12
        ):
            artifact = load_analytics_artifacts()
            if artifact is not None:
                return artifact
        return build_analytics(
            date_from=filters.date_from,
            date_to=filters.date_to,
            item_code=filters.item_code,
            item_group=filters.item_group,
            warehouse_code=filters.warehouse_code,
            min_months=filters.min_months,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/data-quality")
def data_quality(filters: AnalyticsFilters = Depends()) -> list[dict]:
    result = _analysis(filters)
    columns = [
        "item_code",
        "item_name",
        "item_group",
        "months_with_sales",
        "total_months_available",
        "is_negative_demand",
        "has_amount_anomaly",
        "is_intermittent",
        "has_zero_or_null_values",
        "data_quality_status",
    ]
    return dataframe_records(result.metrics[columns])


@router.get("/abc")
def abc(filters: AnalyticsFilters = Depends()) -> list[dict]:
    result = _analysis(filters)
    if filters.abc_basis == "amount":
        return dataframe_records(result.abc_amount)
    return dataframe_records(result.abc_quantity)


@router.get("/abc-value")
def abc_value(filters: AnalyticsFilters = Depends()) -> list[dict]:
    return dataframe_records(_analysis(filters).abc_amount)


@router.get("/xyz")
def xyz(filters: AnalyticsFilters = Depends()) -> list[dict]:
    return dataframe_records(_analysis(filters).xyz)


@router.get("/abc-xyz")
def abc_xyz(filters: AnalyticsFilters = Depends()) -> list[dict]:
    return dataframe_records(_analysis(filters).combined)


@router.get("/summary")
def summary(filters: AnalyticsFilters = Depends()) -> dict:
    return _analysis(filters).summary
