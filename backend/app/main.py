from fastapi import FastAPI

from app.api.routes import (
    analytics,
    demand,
    forecast,
    health,
    inventory,
    replenishment,
    sap_diagnostics,
)

app = FastAPI(
    title="Logística Predictiva SAP B1",
    description="API de lectura para análisis logístico sobre SAP Business One.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(sap_diagnostics.router)
app.include_router(demand.router)
app.include_router(analytics.router)
app.include_router(forecast.router)
app.include_router(inventory.router)
app.include_router(replenishment.router)
