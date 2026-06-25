from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import DatabaseConnectionError
from app.services.inventory_service import (
    get_current_inventory,
    inventory_records,
    load_inventory_artifact,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/current")
def current_inventory(
    item_code: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    only_with_stock: bool = Query(default=False),
) -> list[dict]:
    try:
        if item_code is None and warehouse_code is None and item_group is None:
            artifact = load_inventory_artifact()
            if artifact is not None:
                if only_with_stock:
                    artifact = artifact[
                        (artifact["physical_stock"] != 0)
                        | (artifact["committed_stock"] != 0)
                        | (artifact["on_order_stock"] != 0)
                    ]
                return inventory_records(artifact.reset_index(drop=True))
        frame = get_current_inventory(
            item_code=item_code,
            warehouse_code=warehouse_code,
            item_group=item_group,
            only_with_stock=only_with_stock,
        )
        return inventory_records(frame)
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
