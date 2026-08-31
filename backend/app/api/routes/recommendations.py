from fastapi import APIRouter, Query

from app.schemas.recommendations import (
    PaginatedRecommendationActions,
    PaginatedRecommendations,
    RecommendationItemDetail,
    RecommendationSummary,
    RecommendationWarehouseSummary,
)
from app.services.recommendation_service import (
    get_recommendation_item_detail,
    get_recommendation_actions_page,
    get_recommendation_items_page,
    get_recommendation_warehouses,
    get_recommendations_summary,
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/summary", response_model=RecommendationSummary)
def recommendations_summary(limit: int = Query(default=250000, ge=1, le=250000)) -> dict:
    return get_recommendations_summary(limit=limit)


@router.get("/items", response_model=PaginatedRecommendations)
def recommendation_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    recommendation_type: str | None = None,
    recommendation_status: str | None = None,
    priority_level: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    only_purchase_suggestions: bool = False,
    only_transfer_suggestions: bool = False,
    only_data_validation: bool = False,
    min_priority_score: float | None = None,
    max_priority_score: float | None = None,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=1000),
) -> dict:
    effective_limit = page_size or limit
    effective_offset = ((page - 1) * effective_limit) if page else offset
    return get_recommendation_items_page(
        item_code=item_code,
        warehouse=warehouse,
        recommendation_type=recommendation_type,
        recommendation_status=recommendation_status,
        priority_level=priority_level,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_purchase_suggestions=only_purchase_suggestions,
        only_transfer_suggestions=only_transfer_suggestions,
        only_data_validation=only_data_validation,
        min_priority_score=min_priority_score,
        max_priority_score=max_priority_score,
        limit=effective_limit,
        offset=effective_offset,
    )


@router.get("/item/{item_code}", response_model=RecommendationItemDetail)
def recommendation_item(item_code: str) -> dict:
    return get_recommendation_item_detail(item_code)


@router.get("/warehouses", response_model=list[RecommendationWarehouseSummary])
def recommendation_warehouses(limit: int = Query(default=250000, ge=1, le=250000)) -> list[dict]:
    return get_recommendation_warehouses(limit=limit)


@router.get("/actions", response_model=PaginatedRecommendationActions)
def recommendation_actions(
    item_code: str | None = None,
    warehouse: str | None = None,
    recommendation_type: str | None = None,
    recommendation_status: str | None = None,
    priority_level: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    only_purchase_suggestions: bool = False,
    only_transfer_suggestions: bool = False,
    only_data_validation: bool = False,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=1000),
) -> dict:
    effective_limit = page_size or limit
    effective_offset = ((page - 1) * effective_limit) if page else offset
    return get_recommendation_actions_page(
        item_code=item_code,
        warehouse=warehouse,
        recommendation_type=recommendation_type,
        recommendation_status=recommendation_status,
        priority_level=priority_level,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_purchase_suggestions=only_purchase_suggestions,
        only_transfer_suggestions=only_transfer_suggestions,
        only_data_validation=only_data_validation,
        limit=effective_limit,
        offset=effective_offset,
    )


@router.get("/purchase-candidates", response_model=PaginatedRecommendations)
def recommendation_purchase_candidates(
    item_code: str | None = None,
    warehouse: str | None = None,
    priority_level: str | None = None,
    recommendation_status: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=1000),
) -> dict:
    effective_limit = page_size or limit
    effective_offset = ((page - 1) * effective_limit) if page else offset
    return get_recommendation_items_page(
        item_code=item_code,
        warehouse=warehouse,
        priority_level=priority_level,
        recommendation_status=recommendation_status,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_purchase_suggestions=True,
        limit=effective_limit,
        offset=effective_offset,
    )


@router.get("/transfer-candidates", response_model=PaginatedRecommendations)
def recommendation_transfer_candidates(
    item_code: str | None = None,
    warehouse: str | None = None,
    priority_level: str | None = None,
    recommendation_status: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=1000),
) -> dict:
    effective_limit = page_size or limit
    effective_offset = ((page - 1) * effective_limit) if page else offset
    return get_recommendation_items_page(
        item_code=item_code,
        warehouse=warehouse,
        priority_level=priority_level,
        recommendation_status=recommendation_status,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_transfer_suggestions=True,
        limit=effective_limit,
        offset=effective_offset,
    )
