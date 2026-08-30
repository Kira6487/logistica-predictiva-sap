from fastapi import APIRouter
from fastapi import HTTPException, status

from app.core.database import DatabaseConnectionError, test_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "logistica-predictiva-backend",
    }


@router.get("/api/health")
async def api_health() -> dict[str, str]:
    return await health()


@router.get("/api/health/db")
def database_health() -> dict[str, object]:
    try:
        result = test_connection()
        return {
            "status": "ok",
            "database": result["database"],
            "read_only": result["read_only"],
        }
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure SQL demo no está disponible temporalmente.",
        ) from exc
