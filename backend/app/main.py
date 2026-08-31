from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analytics,
    demand,
    forecast,
    health,
    inventory,
    replenishment,
    sap_diagnostics,
)
from app.core.config import get_settings
from app.core.config import Settings


def create_app(app_settings: Settings) -> FastAPI:
    application = FastAPI(
        title="Logística Predictiva SAP B1",
        description="API de lectura para análisis logístico sobre SAP Business One.",
        version="1.0.0",
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
    return application


app = create_app(get_settings())
