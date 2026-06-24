from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import DatabaseConnectionError
from app.services.eda_service import dataframe_records
from app.services.replenishment_service import (
    build_replenishment,
    filter_replenishment,
)

router = APIRouter(prefix="/replenishment", tags=["replenishment"])


def _result(
    date_from: date | None,
    date_to: date | None,
    item_group: str | None,
    warehouse_code: str | None,
    horizon_months: int,
    include_low_confidence: bool,
):
    try:
        return build_replenishment(
            date_from,
            date_to,
            item_group,
            warehouse_code,
            horizon_months,
            include_low_confidence,
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


def _filtered(
    *,
    date_from: date | None,
    date_to: date | None,
    item_code: str | None,
    item_group: str | None,
    warehouse_code: str | None,
    confidence: str | None,
    stock_status: str | None,
    recommendation_type: str | None,
    priority_level: str | None,
    only_purchase_suggested: bool,
    horizon_months: int,
    include_low_confidence: bool,
):
    result = _result(
        date_from,
        date_to,
        item_group,
        warehouse_code,
        horizon_months,
        include_low_confidence,
    )
    return result, filter_replenishment(
        result.suggestions,
        item_code=item_code,
        confidence=confidence,
        stock_status=stock_status,
        recommendation_type=recommendation_type,
        priority_level=priority_level,
        only_purchase_suggested=only_purchase_suggested,
    )


@router.get("/summary")
def summary(
    date_from: date | None = None,
    date_to: date | None = None,
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    horizon_months: Literal[3, 6] = Query(default=3),
    include_low_confidence: bool = Query(default=True),
) -> dict:
    return _result(
        date_from,
        date_to,
        item_group,
        warehouse_code,
        horizon_months,
        include_low_confidence,
    ).summary


@router.get("/suggestions")
def suggestions(
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    confidence: Literal["HIGH", "MEDIUM", "LOW"] | None = Query(default=None),
    stock_status: str | None = Query(default=None),
    recommendation_type: str | None = Query(default=None),
    priority_level: Literal["HIGH", "MEDIUM", "LOW"] | None = Query(default=None),
    only_purchase_suggested: bool = Query(default=False),
    horizon_months: Literal[3, 6] = Query(default=3),
    include_low_confidence: bool = Query(default=True),
) -> list[dict]:
    _, frame = _filtered(
        date_from=date_from,
        date_to=date_to,
        item_code=item_code,
        item_group=item_group,
        warehouse_code=warehouse_code,
        confidence=confidence,
        stock_status=stock_status,
        recommendation_type=recommendation_type,
        priority_level=priority_level,
        only_purchase_suggested=only_purchase_suggested,
        horizon_months=horizon_months,
        include_low_confidence=include_low_confidence,
    )
    return dataframe_records(frame)


@router.get("/critical")
def critical(
    warehouse_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    horizon_months: Literal[3, 6] = Query(default=3),
    include_low_confidence: bool = Query(default=True),
) -> list[dict]:
    result = _result(
        None, None, item_group, warehouse_code, horizon_months, include_low_confidence
    )
    frame = result.suggestions[
        result.suggestions["stock_status"].isin(
            ["CRITICAL", "NO_STOCK_WITH_DEMAND"]
        )
    ]
    return dataframe_records(frame)


@router.get("/overstock")
def overstock(
    warehouse_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    horizon_months: Literal[3, 6] = Query(default=3),
) -> list[dict]:
    result = _result(None, None, item_group, warehouse_code, horizon_months, True)
    return dataframe_records(
        result.suggestions[result.suggestions["stock_status"] == "OVERSTOCK"]
    )


@router.get("/item/{item_code}")
def item_detail(
    item_code: str,
    warehouse_code: str | None = Query(default=None),
    horizon_months: Literal[3, 6] = Query(default=3),
    include_low_confidence: bool = Query(default=True),
) -> dict:
    result = _result(
        None, None, None, warehouse_code, horizon_months, include_low_confidence
    )
    row = result.suggestions[result.suggestions["item_code"] == item_code]
    if row.empty:
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    forecast = (
        result.forecast.future[
            result.forecast.future["item_code"].astype(str) == item_code
        ]
        if result.forecast is not None
        else None
    )
    return {
        "replenishment": dataframe_records(row)[0],
        "forecast": (
            dataframe_records(forecast) if forecast is not None else []
        ),
    }


@router.get("/export-preview")
def export_preview(
    warehouse_code: str | None = Query(default=None),
    horizon_months: Literal[3, 6] = Query(default=3),
) -> list[dict]:
    result = _result(None, None, None, warehouse_code, horizon_months, True)
    columns = [
        "item_code",
        "item_name",
        "warehouse_code",
        "abc_class_quantity",
        "xyz_class",
        "forecast_confidence",
        "physical_stock",
        "available_stock",
        "on_order_stock",
        "projected_demand_horizon",
        "coverage_days",
        "safety_stock",
        "suggested_purchase_quantity",
        "stock_status",
        "recommendation_type",
        "priority_score",
        "priority_level",
        "recommendation_reason",
    ]
    return dataframe_records(result.suggestions[columns])
