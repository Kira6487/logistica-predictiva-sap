from fastapi import FastAPI

from app.api.routes import demand, health, sap_diagnostics

app = FastAPI(
    title="Logística Predictiva SAP B1",
    description="API de lectura para análisis logístico sobre SAP Business One.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(sap_diagnostics.router)
app.include_router(demand.router)
