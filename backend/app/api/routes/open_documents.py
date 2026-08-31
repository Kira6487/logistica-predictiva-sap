from fastapi import APIRouter, Query

from app.schemas.inventory_position import OpenDocumentRecord, OpenDocumentsItemDetail, OpenDocumentsSummary
from app.services.open_documents_service import get_open_documents, get_open_documents_by_item, get_open_documents_summary


router = APIRouter(prefix="/open-documents", tags=["open-documents"])


@router.get("/summary", response_model=OpenDocumentsSummary)
def open_documents_summary() -> dict:
    return get_open_documents_summary()


@router.get("/items", response_model=list[OpenDocumentRecord])
def open_documents_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    document_type: str | None = None,
    card_code: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(default=1000, ge=1, le=100000),
) -> list[dict]:
    return get_open_documents(
        item_code=item_code,
        warehouse=warehouse,
        document_type=document_type,
        card_code=card_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/item/{item_code}", response_model=OpenDocumentsItemDetail)
def open_documents_item(item_code: str) -> dict:
    return get_open_documents_by_item(item_code)