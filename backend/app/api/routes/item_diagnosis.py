from fastapi import APIRouter

from app.schemas.item_diagnosis import AvailabilityAudit, ItemDiagnosis, ProjectedKardexLine, RelatedDocumentsGroup
from app.services.item_diagnosis_service import (
    get_item_availability_audit,
    get_item_diagnosis,
    get_item_projected_kardex,
    get_item_related_documents,
)


router = APIRouter(prefix="/item-diagnosis", tags=["item-diagnosis"])


@router.get("/{item_code}", response_model=ItemDiagnosis)
def item_diagnosis(item_code: str, warehouse: str | None = None) -> dict:
    return get_item_diagnosis(item_code=item_code, warehouse=warehouse)


@router.get("/{item_code}/projected-kardex", response_model=list[ProjectedKardexLine])
def item_projected_kardex(item_code: str, warehouse: str | None = None) -> list[dict]:
    return get_item_projected_kardex(item_code=item_code, warehouse=warehouse)


@router.get("/{item_code}/availability-audit", response_model=AvailabilityAudit)
def item_availability_audit(item_code: str, warehouse: str | None = None) -> dict:
    return get_item_availability_audit(item_code=item_code, warehouse=warehouse)


@router.get("/{item_code}/related-documents", response_model=RelatedDocumentsGroup)
def item_related_documents(item_code: str, warehouse: str | None = None) -> dict:
    return get_item_related_documents(item_code=item_code, warehouse=warehouse)
