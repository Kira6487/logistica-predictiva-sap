from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    analytics,
    consumption,
    coverage_risk,
    dashboard,
    demand,
    forecast,
    health,
    inventory,
    inventory_position,
    item_diagnosis,
    open_documents,
    recommendations,
    replenishment,
    sap_diagnostics,
    stock,
)
from app.core.config import get_settings
from app.core.config import Settings
from app.core.database import DatabaseConnectionError


def create_app(app_settings: Settings) -> FastAPI:
    application = FastAPI(
        title="Logística Predictiva SAP B1",
        description="API de lectura para análisis logístico sobre SAP Business One.",
        version="1.0.0",
    )

    @application.exception_handler(DatabaseConnectionError)
    async def database_exception_handler(
        _request: Request, _exc: DatabaseConnectionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Azure SQL no está disponible temporalmente."},
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.allowed_origins),
        allow_origin_regex=app_settings.allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(sap_diagnostics.router)
    application.include_router(demand.router)
    application.include_router(analytics.router)
    application.include_router(forecast.router)
    application.include_router(inventory.router)
    application.include_router(replenishment.router)
    application.include_router(dashboard.router)
    application.include_router(consumption.router)
    application.include_router(stock.router)
    application.include_router(open_documents.router)
    application.include_router(inventory_position.router)
    application.include_router(coverage_risk.router)
    application.include_router(recommendations.router)
    application.include_router(item_diagnosis.router)
    return application


app = create_app(get_settings())
