from fastapi import APIRouter, HTTPException, status

from app.core.database import DatabaseConnectionError, test_connection
from app.services.diagnostics_service import inspect_demo_database

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


@router.get("/schema")
def schema_diagnostics() -> dict:
    try:
        return inspect_demo_database()
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure SQL demo no está disponible temporalmente.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
