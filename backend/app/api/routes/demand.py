from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import DatabaseConnectionError
from app.schemas.demand import MonthlyDemand
from app.services.demand_service import get_monthly_demand

router = APIRouter(prefix="/demand", tags=["demand"])


@router.get("/monthly", response_model=list[MonthlyDemand])
def monthly_demand(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    item_code: str | None = Query(default=None, min_length=1, max_length=50),
    warehouse_code: str | None = Query(default=None, min_length=1, max_length=20),
) -> list[MonthlyDemand]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from no puede ser posterior a date_to.",
        )

    try:
        rows = get_monthly_demand(date_from, date_to, item_code, warehouse_code)
        return [MonthlyDemand(**row) for row in rows]
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
