from fastapi import APIRouter

from app.schemas.inventory_position import InventoryPositionItemDetail, InventoryPositionSummary
from app.services.inventory_position_service import get_inventory_position_for_item, get_inventory_position_summary


router = APIRouter(prefix="/inventory-position", tags=["inventory-position"])


@router.get("/summary", response_model=InventoryPositionSummary)
def inventory_position_summary() -> dict:
    return get_inventory_position_summary()


@router.get("/item/{item_code}", response_model=InventoryPositionItemDetail)
def inventory_position_item(item_code: str) -> dict:
    return get_inventory_position_for_item(item_code)