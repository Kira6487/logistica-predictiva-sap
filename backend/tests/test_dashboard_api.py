from fastapi.testclient import TestClient

from app.api.routes import dashboard
from app.main import app


client = TestClient(app)


def test_dashboard_bootstrap_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        dashboard,
        "get_dashboard_bootstrap",
        lambda limit=5000: {
            "total_recomendaciones_evaluadas": 10,
            "total_accion_recomendada": 2,
            "total_requiere_validacion": 3,
            "total_solo_monitoreo": 4,
            "total_sin_accion": 1,
            "total_datos_insuficientes": 0,
            "compras_sugeridas": 2,
            "traslados_sugeridos": 1,
            "validaciones_datos_sugeridas": 1,
            "revisiones_maestro_sugeridas": 1,
            "distribucion_por_accion": {"comprar": 2},
            "distribucion_por_prioridad": {"urgente": 1},
            "distribucion_por_confianza": {"media": 10},
            "distribucion_por_estado": {"accion_recomendada": 2, "requiere_validacion": 3},
            "calculado_en": "2026-07-10T00:00:00+00:00",
        },
    )

    response = client.get("/dashboard/bootstrap")

    assert response.status_code == 200
    assert response.json()["compras_sugeridas"] == 2
    assert response.json()["distribucion_por_accion"]["comprar"] == 2
    assert response.json()["distribucion_por_confianza"]["media"] == 10
