from app.services import recommendation_service
from app.services.recommendation_service import build_recommendation_record, calculate_priority, calculate_suggested_quantities


def _diagnostic(**overrides) -> dict:
    record = {
        "item_code": "A001",
        "item_name": "Articulo A",
        "warehouse_code": "01",
        "warehouse_name": "Central",
        "stock_fisico": 10.0,
        "stock_comprometido": 0.0,
        "stock_pedido": 0.0,
        "stock_disponible": 10.0,
        "stock_proyectado_base": 10.0,
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
        "stock_proyectado_con_partidas": 10.0,
        "consumo_total_historico": 120.0,
        "periodos_historicos_detectados": 12,
        "meses_con_consumo": 12,
        "meses_sin_consumo": 0,
        "fecha_ultimo_consumo": "2026-06-30",
        "consumo_promedio_mensual_3m": 30.0,
        "consumo_promedio_mensual_6m": 30.0,
        "consumo_promedio_mensual_12m": 30.0,
        "consumo_promedio_mensual_general": 30.0,
        "consumo_mediano_mensual": 30.0,
        "consumo_maximo_mensual": 30.0,
        "consumo_minimo_mensual": 30.0,
        "desviacion_consumo_mensual": 0.0,
        "coeficiente_variacion": 0.0,
        "ratio_meses_con_consumo": 1.0,
        "tipo_demanda": "demanda_estable",
        "consumo_base_mensual": 30.0,
        "consumo_base_diario": 1.0,
        "fuente_consumo_base": "promedio_12m",
        "cobertura_dias_stock_disponible": 10.0,
        "cobertura_dias_stock_proyectado": 10.0,
        "cobertura_meses_stock_disponible": 0.33,
        "cobertura_meses_stock_proyectado": 0.33,
        "deficit_30_dias": 20.0,
        "deficit_60_dias": 50.0,
        "deficit_90_dias": 80.0,
        "sobrante_30_dias": 0.0,
        "sobrante_60_dias": 0.0,
        "sobrante_90_dias": 0.0,
        "nivel_riesgo": "critico",
        "nivel_confianza": "media",
        "motivo_confianza": "Historial medio con consumo suficiente",
        "motivos_riesgo": ["Riesgo critico"],
    }
    record.update(overrides)
    return record


def test_buy_recommendation_for_critical_risk_with_deficit_and_confidence() -> None:
    recommendation = build_recommendation_record(_diagnostic())

    assert recommendation["recommendation_type"] == "comprar"
    assert recommendation["recommendation_status"] == "accion_recomendada"
    assert recommendation["suggested_quantity"] == 20.0


def test_no_purchase_without_confidence() -> None:
    recommendation = build_recommendation_record(_diagnostic(nivel_riesgo="sin_diagnostico", nivel_confianza="sin_confianza", consumo_base_mensual=0, consumo_base_diario=0))

    assert recommendation["recommendation_type"] == "validar_datos"
    assert recommendation["recommendation_status"] == "datos_insuficientes"


def test_validate_data_without_diagnosis() -> None:
    recommendation = build_recommendation_record(_diagnostic(nivel_riesgo="sin_diagnostico", nivel_confianza="sin_confianza"))

    assert recommendation["recommendation_type"] == "validar_datos"


def test_review_master_when_stock_without_consumption() -> None:
    diagnostic = _diagnostic(meses_con_consumo=0, nivel_riesgo="sin_diagnostico", nivel_confianza="sin_confianza")
    reconciliation = {"articulos_stock_sin_consumo_historico": ["A001"]}

    recommendation = build_recommendation_record(diagnostic, reconciliation=reconciliation)

    assert recommendation["recommendation_type"] == "revisar_maestro_articulo"


def test_accelerate_open_purchase_when_still_at_risk() -> None:
    recommendation = build_recommendation_record(_diagnostic(entradas_abiertas=5.0))

    assert recommendation["recommendation_type"] == "acelerar_compra_abierta"


def test_transfer_stock_when_other_warehouse_has_excess() -> None:
    target = _diagnostic()
    source = _diagnostic(
        warehouse_code="02",
        nivel_riesgo="bajo",
        stock_proyectado_con_partidas=200.0,
        deficit_30_dias=0.0,
        deficit_60_dias=0.0,
        deficit_90_dias=0.0,
        sobrante_90_dias=100.0,
    )

    recommendation = build_recommendation_record(target, [target, source])

    assert recommendation["recommendation_type"] == "trasladar_stock"
    assert recommendation["source_warehouse"] == "02"
    assert recommendation["transfer_candidate_quantity"] > 0


def test_no_transfer_if_source_stays_critical() -> None:
    target = _diagnostic()
    source = _diagnostic(warehouse_code="02", nivel_riesgo="critico", stock_proyectado_con_partidas=200.0, sobrante_90_dias=100.0)

    recommendation = build_recommendation_record(target, [target, source])

    assert recommendation["recommendation_type"] != "trasladar_stock"


def test_suggested_quantities_by_horizon() -> None:
    quantities = calculate_suggested_quantities(_diagnostic(nivel_riesgo="critico"))
    assert quantities["suggested_horizon_days"] == 30
    assert quantities["suggested_quantity"] == 20

    quantities = calculate_suggested_quantities(_diagnostic(nivel_riesgo="alto"))
    assert quantities["suggested_horizon_days"] == 60
    assert quantities["suggested_quantity"] == 50

    quantities = calculate_suggested_quantities(_diagnostic(nivel_riesgo="medio"))
    assert quantities["suggested_horizon_days"] == 90
    assert quantities["suggested_quantity"] == 80


def test_priority_score_level_and_reasons() -> None:
    score, level, reasons = calculate_priority(_diagnostic())

    assert score > 0
    assert level in {"urgente", "alta", "media", "baja", "informativa"}
    assert "Riesgo critico" in reasons
    assert "Deficit proyectado a 30 dias" in reasons


def test_explainable_reasons_and_missing_lead_time_warning() -> None:
    recommendation = build_recommendation_record(_diagnostic())

    assert recommendation["main_message"]
    assert recommendation["business_reason"]
    assert "Lead time no disponible en SAP o no detectado" in recommendation["data_quality_notes"]


def test_recommendation_items_does_not_drop_filtered_rows(monkeypatch) -> None:
    diagnostics = [_diagnostic(item_code=f"A{i:03d}") for i in range(3)]
    monkeypatch.setattr(recommendation_service, "get_coverage_risk_items", lambda **kwargs: diagnostics)
    monkeypatch.setattr(recommendation_service, "get_coverage_reconciliation", lambda **kwargs: {})

    rows = recommendation_service.get_recommendation_items(limit=10)

    assert len(rows) == 3
    assert {row["item_code"] for row in rows} == {"A000", "A001", "A002"}


def test_paginated_items_applies_limit_after_full_filtered_result(monkeypatch) -> None:
    captured = {}
    rows = [{**build_recommendation_record(_diagnostic(item_code=f"A{i:03d}")), "priority_score": float(100 - i)} for i in range(45)]

    def fake_get_recommendation_items(**kwargs):
        captured.update(kwargs)
        return rows

    monkeypatch.setattr(recommendation_service, "get_recommendation_items", fake_get_recommendation_items)

    page = recommendation_service.get_recommendation_items_page(limit=20, offset=20)

    assert captured["limit"] == 250000
    assert len(page["items"]) == 20
    assert page["total"] == 45
    assert page["items"][0]["item_code"] == "A020"
    assert page["has_next"] is True
    assert page["has_previous"] is True


def test_actions_page_keeps_total_and_groups_current_page(monkeypatch) -> None:
    rows = []
    for index in range(30):
        record = build_recommendation_record(_diagnostic(item_code=f"A{index:03d}"))
        record["recommendation_type"] = "comprar" if index % 2 == 0 else "validar_datos"
        rows.append(record)
    monkeypatch.setattr(recommendation_service, "get_recommendation_items", lambda **kwargs: rows)

    page = recommendation_service.get_recommendation_actions_page(limit=20, offset=0)

    assert page["total"] == 30
    assert len(page["items"]["compras_sugeridas"]) == 10
    assert len(page["items"]["articulos_para_validar_datos"]) == 10
