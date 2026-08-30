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

settings = get_settings()

app = FastAPI(
    title="Logística Predictiva SAP B1",
    description="API de lectura para análisis logístico sobre SAP Business One.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sap_diagnostics.router)
app.include_router(demand.router)
app.include_router(analytics.router)
app.include_router(forecast.router)
app.include_router(inventory.router)
app.include_router(replenishment.router)
