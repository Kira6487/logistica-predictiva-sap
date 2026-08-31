from fastapi import APIRouter, Query

from app.schemas.dashboard import DashboardBootstrap
from app.services.dashboard_service import get_dashboard_bootstrap


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/bootstrap", response_model=DashboardBootstrap)
def dashboard_bootstrap(limit: int = Query(default=5000, ge=1, le=250000)) -> dict:
    return get_dashboard_bootstrap(limit=limit)
