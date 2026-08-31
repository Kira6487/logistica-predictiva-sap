from app.services.coverage_risk_service import (
    build_coverage_risk_record,
    calculate_consumption_metrics,
    classify_confidence,
    classify_demand,
)


def _monthly(values: list[float]) -> list[dict]:
    return [
        {
            "item_code": "A001",
            "item_description": "Articulo A",
            "warehouse": "01",
            "year": 2026 if index <= 6 else 2025,
            "month": index if index <= 12 else 12,
            "period": f"2026-{index:02d}",
            "consumed_quantity": value,
            "movement_count": 1,
            "first_date": f"2026-{index:02d}-01",
            "last_date": f"2026-{index:02d}-28",
            "quality_flags": [],
        }
        for index, value in enumerate(values, start=1)
    ]


def _inventory(**overrides) -> dict:
    record = {
        "item_code": "A001",
        "item_name": "Articulo A",
        "warehouse_code": "01",
        "warehouse_name": "Central",
        "stock_fisico": 120.0,
        "stock_comprometido": 0.0,
        "stock_pedido": 0.0,
        "stock_disponible": 120.0,
        "stock_proyectado_base": 120.0,
        "sin_stock": False,
        "stock_negativo": False,
        "comprometido_mayor_stock": False,
        "tiene_stock": True,
        "tiene_pedido_abierto": False,
        "tiene_compromiso_abierto": False,
        "item_inventory": True,
        "item_active": True,
        "warehouse_locked": False,
        "warehouse_inactive": False,
        "stock_comprometido_sap": 0.0,
        "stock_pedido_sap": 0.0,
        "entradas_abiertas": 0.0,
        "salidas_abiertas": 0.0,
        "stock_proyectado_con_partidas": 120.0,
    }
    record.update(overrides)
    return record


def test_consumption_averages_3m_6m_12m() -> None:
    metrics = calculate_consumption_metrics(_monthly([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]))

    assert metrics["consumo_promedio_mensual_3m"] == 110
    assert metrics["consumo_promedio_mensual_6m"] == 95
    assert metrics["consumo_promedio_mensual_12m"] == 65


def test_base_daily_consumption_and_coverage() -> None:
    record = build_coverage_risk_record(_inventory(stock_proyectado_con_partidas=60, stock_disponible=30), _monthly([30] * 12))

    assert record["consumo_base_mensual"] == 30
    assert record["consumo_base_diario"] == 1
    assert record["cobertura_dias_stock_disponible"] == 30
    assert record["cobertura_dias_stock_proyectado"] == 60
    assert record["cobertura_meses_stock_proyectado"] == 2


def test_coverage_not_calculable_without_consumption() -> None:
    record = build_coverage_risk_record(_inventory(), [])

    assert record["cobertura_dias_stock_proyectado"] is None
    assert record["nivel_riesgo"] == "sin_diagnostico"
    assert record["nivel_confianza"] == "sin_confianza"


def test_demand_classifications() -> None:
    assert classify_demand(calculate_consumption_metrics(_monthly([10, 20]))) == "demanda_insuficiente"
    assert classify_demand(calculate_consumption_metrics(_monthly([0, 0, 10, 0, 20, 0, 30, 0, 0, 0]))) == "demanda_intermitente"
    assert classify_demand(calculate_consumption_metrics(_monthly([1, 100, 1, 100, 1, 100]))) == "demanda_variable"
    assert classify_demand(calculate_consumption_metrics(_monthly([10, 11, 9, 10, 10, 11]))) == "demanda_estable"


def test_critical_risk_by_negative_available_stock() -> None:
    record = build_coverage_risk_record(
        _inventory(stock_fisico=-1, stock_disponible=-1, stock_proyectado_con_partidas=-1),
        _monthly([10] * 12),
    )

    assert record["nivel_riesgo"] == "critico"


def test_critical_risk_by_committed_over_stock() -> None:
    record = build_coverage_risk_record(
        _inventory(stock_fisico=5, stock_comprometido_sap=8, stock_comprometido=8, stock_disponible=-3),
        _monthly([10] * 12),
    )

    assert record["nivel_riesgo"] == "critico"
    assert "Comprometido SAP mayor al stock fisico" in record["motivos_riesgo"]


def test_high_risk_by_coverage_under_15_days() -> None:
    record = build_coverage_risk_record(_inventory(stock_disponible=10, stock_proyectado_con_partidas=10), _monthly([30] * 12))

    assert record["nivel_riesgo"] == "alto"


def test_deficits_30_60_90_days() -> None:
    record = build_coverage_risk_record(_inventory(stock_disponible=10, stock_proyectado_con_partidas=10), _monthly([60] * 12))

    assert record["deficit_30_dias"] == 50
    assert record["deficit_60_dias"] == 110
    assert record["deficit_90_dias"] == 170


def test_confidence_levels() -> None:
    assert classify_confidence(calculate_consumption_metrics(_monthly([10] * 12)), "demanda_estable")[0] == "alta"
    assert classify_confidence(calculate_consumption_metrics(_monthly([10] * 6)), "demanda_estable")[0] == "media"
    assert classify_confidence(calculate_consumption_metrics(_monthly([1, 100, 1, 100, 1, 100])), "demanda_variable")[0] == "baja"
    assert classify_confidence(calculate_consumption_metrics([]), "sin_consumo")[0] == "sin_confianza"
