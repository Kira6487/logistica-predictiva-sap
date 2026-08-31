from fastapi.testclient import TestClient

from app.api.routes import coverage_risk
from app.main import app


client = TestClient(app)


def _record() -> dict:
    return {
        "item_code": "A001",
        "item_name": "Articulo A",
        "warehouse_code": "01",
        "warehouse_name": "Central",
        "stock_fisico": 10.0,
        "stock_comprometido": 1.0,
        "stock_pedido": 0.0,
        "stock_disponible": 9.0,
        "stock_proyectado_base": 9.0,
        "sin_stock": False,
        "stock_negativo": False,
        "comprometido_mayor_stock": False,
        "tiene_stock": True,
        "tiene_pedido_abierto": False,
        "tiene_compromiso_abierto": True,
        "item_inventory": True,
        "item_active": True,
        "warehouse_locked": False,
        "warehouse_inactive": False,
        "stock_comprometido_sap": 1.0,
        "stock_pedido_sap": 0.0,
        "entradas_abiertas": 0.0,
        "salidas_abiertas": 0.0,
        "stock_proyectado_con_partidas": 9.0,
        "consumo_total_historico": 30.0,
        "periodos_historicos_detectados": 3,
        "meses_con_consumo": 3,
        "meses_sin_consumo": 0,
        "fecha_ultimo_consumo": "2026-03-31",
        "consumo_promedio_mensual_3m": 10.0,
        "consumo_promedio_mensual_6m": 10.0,
        "consumo_promedio_mensual_12m": 10.0,
        "consumo_promedio_mensual_general": 10.0,
        "consumo_mediano_mensual": 10.0,
        "consumo_maximo_mensual": 10.0,
        "consumo_minimo_mensual": 10.0,
        "desviacion_consumo_mensual": 0.0,
        "coeficiente_variacion": 0.0,
        "ratio_meses_con_consumo": 1.0,
        "tipo_demanda": "demanda_estable",
        "consumo_base_mensual": 10.0,
        "consumo_base_diario": 0.3333333333,
        "fuente_consumo_base": "promedio_3m",
        "cobertura_dias_stock_disponible": 27.0,
        "cobertura_dias_stock_proyectado": 27.0,
        "cobertura_meses_stock_disponible": 0.9,
        "cobertura_meses_stock_proyectado": 0.9,
        "deficit_30_dias": 1.0,
        "deficit_60_dias": 11.0,
        "deficit_90_dias": 21.0,
        "sobrante_30_dias": 0.0,
        "sobrante_60_dias": 0.0,
        "sobrante_90_dias": 0.0,
        "nivel_riesgo": "alto",
        "nivel_confianza": "media",
        "motivo_confianza": "Historial medio con consumo suficiente",
        "motivos_riesgo": ["Deficit a 30 dias"],
    }


def _summary() -> dict:
    return {
        "total_articulos_evaluados": 1,
        "total_combinaciones_evaluadas": 1,
        "riesgo_critico": 0,
        "riesgo_alto": 1,
        "riesgo_medio": 0,
        "riesgo_bajo": 0,
        "sin_diagnostico": 0,
        "sin_riesgo_aparente": 0,
        "confianza_alta": 0,
        "confianza_media": 1,
        "confianza_baja": 0,
        "sin_confianza": 0,
        "articulos_stock_disponible_negativo": 0,
        "articulos_comprometido_mayor_stock": 0,
        "articulos_deficit_30_dias": 1,
        "articulos_deficit_60_dias": 1,
        "articulos_deficit_90_dias": 1,
        "almacenes_consumo_sin_stock_actual": 0,
        "almacenes_stock_sin_consumo_historico": 0,
    }


def _reconciliation() -> dict:
    return {
        "almacenes_consumo_sin_stock_actual": [],
        "almacenes_stock_sin_consumo_historico": [],
        "articulos_consumo_sin_stock_actual": [],
        "articulos_stock_sin_consumo_historico": [],
        "articulos_partidas_abiertas_sin_consumo_historico": [],
        "articulos_partidas_abiertas_sin_stock_actual": [],
        "total_combinaciones_consumo": 1,
        "total_combinaciones_stock": 1,
        "total_combinaciones_partidas_abiertas": 0,
    }


def test_coverage_risk_summary_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(coverage_risk, "get_coverage_risk_summary", lambda limit=100000: _summary())

    response = client.get("/coverage-risk/summary")

    assert response.status_code == 200
    assert response.json()["riesgo_alto"] == 1


def test_coverage_risk_items_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(coverage_risk, "get_coverage_risk_items", lambda **kwargs: [_record()])

    response = client.get("/coverage-risk/items")

    assert response.status_code == 200
    assert response.json()[0]["item_code"] == "A001"


def test_coverage_risk_item_detail_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        coverage_risk,
        "get_coverage_risk_item_detail",
        lambda item_code: {
            "item_code": item_code,
            "item_name": "Articulo A",
            "diagnostics_by_warehouse": [_record()],
            "stock_by_warehouse": [],
            "monthly_consumption": [],
            "open_documents": [],
            "summary": _summary(),
        },
    )

    response = client.get("/coverage-risk/item/A001")

    assert response.status_code == 200
    assert response.json()["item_code"] == "A001"


def test_coverage_risk_warehouses_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        coverage_risk,
        "get_coverage_risk_warehouses",
        lambda limit=100000: [
            {
                "warehouse_code": "01",
                "warehouse_name": "Central",
                "articulos_evaluados": 1,
                "criticos": 0,
                "altos": 1,
                "medios": 0,
                "bajos": 0,
                "sin_diagnostico": 0,
                "deficit_total_30_dias": 1.0,
                "deficit_total_60_dias": 11.0,
                "deficit_total_90_dias": 21.0,
                "articulos_sin_stock_con_consumo": 0,
            }
        ],
    )

    response = client.get("/coverage-risk/warehouses")

    assert response.status_code == 200
    assert response.json()[0]["warehouse_code"] == "01"


def test_coverage_risk_reconciliation_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(coverage_risk, "get_coverage_reconciliation", lambda **kwargs: _reconciliation())

    response = client.get("/coverage-risk/reconciliation")

    assert response.status_code == 200
    assert response.json()["total_combinaciones_stock"] == 1
