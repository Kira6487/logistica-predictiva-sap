from fastapi import APIRouter, Query

from app.schemas.coverage_risk import CoverageReconciliation, CoverageRiskItemDetail, CoverageRiskRecord, CoverageRiskSummary, CoverageRiskWarehouseSummary
from app.services.coverage_risk_service import (
    get_coverage_reconciliation,
    get_coverage_risk_item_detail,
    get_coverage_risk_items,
    get_coverage_risk_summary,
    get_coverage_risk_warehouses,
)


router = APIRouter(prefix="/coverage-risk", tags=["coverage-risk"])


@router.get("/summary", response_model=CoverageRiskSummary)
def coverage_risk_summary(limit: int = Query(default=250000, ge=1, le=250000)) -> dict:
    return get_coverage_risk_summary(limit=limit)


@router.get("/items", response_model=list[CoverageRiskRecord])
def coverage_risk_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    demand_type: str | None = None,
    only_critical: bool = False,
    only_with_deficit: bool = False,
    only_without_diagnosis: bool = False,
    min_coverage_days: float | None = None,
    max_coverage_days: float | None = None,
    limit: int = Query(default=1000, ge=1, le=250000),
) -> list[dict]:
    return get_coverage_risk_items(
        item_code=item_code,
        warehouse=warehouse,
        risk_level=risk_level,
        confidence_level=confidence_level,
        demand_type=demand_type,
        only_critical=only_critical,
        only_with_deficit=only_with_deficit,
        only_without_diagnosis=only_without_diagnosis,
        min_coverage_days=min_coverage_days,
        max_coverage_days=max_coverage_days,
        limit=limit,
    )


@router.get("/item/{item_code}", response_model=CoverageRiskItemDetail)
def coverage_risk_item(item_code: str) -> dict:
    return get_coverage_risk_item_detail(item_code)


@router.get("/warehouses", response_model=list[CoverageRiskWarehouseSummary])
def coverage_risk_warehouses(limit: int = Query(default=250000, ge=1, le=250000)) -> list[dict]:
    return get_coverage_risk_warehouses(limit=limit)


@router.get("/reconciliation", response_model=CoverageReconciliation)
def coverage_risk_reconciliation(
    item_code: str | None = None,
    warehouse: str | None = None,
    limit: int = Query(default=250000, ge=1, le=250000),
) -> dict:
    return get_coverage_reconciliation(item_code=item_code, warehouse=warehouse, limit=limit)
