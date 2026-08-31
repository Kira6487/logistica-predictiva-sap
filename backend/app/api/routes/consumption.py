from fastapi import APIRouter, Query

from app.schemas.consumption import ConsumptionSummary, ItemConsumptionDetail, MonthlyConsumptionRecord, MovementTypeSummary
from app.services.consumption_history_service import (
    get_consumption_movement_types,
    get_consumption_summary,
    get_item_consumption_detail,
    get_monthly_consumption,
)


router = APIRouter(prefix="/consumption", tags=["consumption"])


@router.get("/summary", response_model=ConsumptionSummary)
def consumption_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    include_transfers: bool = False,
    include_adjustments: bool = False,
) -> dict:
    return get_consumption_summary(
        start_date=start_date,
        end_date=end_date,
        include_transfers=include_transfers,
        include_adjustments=include_adjustments,
    )


@router.get("/monthly", response_model=list[MonthlyConsumptionRecord])
def monthly_consumption(
    item_code: str | None = None,
    warehouse: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_transfers: bool = False,
    include_adjustments: bool = False,
    limit: int = Query(default=1000, ge=1, le=10000),
) -> list[dict]:
    return get_monthly_consumption(
        item_code=item_code,
        warehouse=warehouse,
        start_date=start_date,
        end_date=end_date,
        include_transfers=include_transfers,
        include_adjustments=include_adjustments,
        limit=limit,
    )


@router.get("/item/{item_code}", response_model=ItemConsumptionDetail)
def item_consumption(item_code: str) -> dict:
    return get_item_consumption_detail(item_code)


@router.get("/movement-types", response_model=list[MovementTypeSummary])
def movement_types() -> list[dict]:
    return get_consumption_movement_types()