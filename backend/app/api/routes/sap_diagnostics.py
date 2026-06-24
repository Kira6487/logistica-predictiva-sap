from fastapi import APIRouter, HTTPException, status

from app.core.database import DatabaseConnectionError, test_connection

router = APIRouter(prefix="/sap/diagnostics", tags=["sap-diagnostics"])


@router.get("/connection")
def connection_diagnostics() -> dict:
    try:
        return test_connection()
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
