from fastapi import APIRouter, Query

from app.schemas.inventory_position import StockItemDetail, StockPositionRecord, StockSummary, WarehouseStockSummary
from app.services.stock_position_service import get_stock_item_detail, get_stock_items, get_stock_summary, get_warehouse_stock_summary


router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/summary", response_model=StockSummary)
def stock_summary() -> dict:
    return get_stock_summary()


@router.get("/items", response_model=list[StockPositionRecord])
def stock_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    only_with_stock: bool = False,
    only_negative: bool = False,
    only_committed_over_stock: bool = False,
    include_inactive: bool = False,
    include_locked_warehouses: bool = False,
    limit: int = Query(default=1000, ge=1, le=100000),
) -> list[dict]:
    return get_stock_items(
        item_code=item_code,
        warehouse=warehouse,
        only_with_stock=only_with_stock,
        only_negative=only_negative,
        only_committed_over_stock=only_committed_over_stock,
        include_inactive=include_inactive,
        include_locked_warehouses=include_locked_warehouses,
        limit=limit,
    )


@router.get("/item/{item_code}", response_model=StockItemDetail)
def stock_item(item_code: str) -> dict:
    return get_stock_item_detail(item_code)


@router.get("/warehouses", response_model=list[WarehouseStockSummary])
def stock_warehouses() -> list[dict]:
    return get_warehouse_stock_summary()