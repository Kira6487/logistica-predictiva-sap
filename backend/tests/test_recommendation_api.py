from fastapi.testclient import TestClient

from app.api.routes import recommendations
from app.main import app


client = TestClient(app)


def _record() -> dict:
    return {
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
        "recommendation_type": "comprar",
        "recommendation_status": "accion_recomendada",
        "priority_level": "urgente",
        "priority_score": 90.0,
        "priority_reasons": ["Riesgo critico"],
        "suggested_quantity": 20.0,
        "suggested_quantity_30d": 20.0,
        "suggested_quantity_60d": 50.0,
        "suggested_quantity_90d": 80.0,
        "suggested_horizon_days": 30,
        "requires_human_approval": True,
        "recommendation_confidence": "media",
        "recommendation_warning": "Cantidad referencial",
        "preferred_vendor_code": None,
        "preferred_vendor_name": None,
        "item_group_code": None,
        "item_group_name": None,
        "estimated_lead_time_days": None,
        "last_purchase_date": None,
        "last_purchase_vendor": None,
        "last_purchase_price": None,
        "min_stock": None,
        "max_stock": None,
        "min_purchase_qty": None,
        "purchase_multiple": None,
        "demand_during_lead_time": None,
        "coverage_after_lead_time": None,
        "lead_time_risk": "no_calculable",
        "source_warehouse": None,
        "target_warehouse": None,
        "transfer_candidate_quantity": 0.0,
        "source_projected_stock_before_transfer": None,
        "target_projected_stock_before_transfer": None,
        "source_remaining_stock_after_transfer": None,
        "target_projected_stock_after_transfer": None,
        "transfer_reason": None,
        "main_message": "Comprar 20 unidades referenciales",
        "recommendation_detail": "Comprar 20 unidades referenciales",
        "business_reason": "Razon de negocio",
        "technical_reason": "Razon tecnica",
        "data_quality_notes": [],
        "next_action_label": "Validar compra",
        "next_action_description": "Revisar antes de generar OC",
    }


def _summary() -> dict:
    return {
        "total_recomendaciones_evaluadas": 1,
        "total_accion_recomendada": 1,
        "total_requiere_validacion": 0,
        "total_solo_monitoreo": 0,
        "total_sin_accion": 0,
        "total_datos_insuficientes": 0,
        "cantidad_por_tipo": {"comprar": 1},
        "cantidad_por_prioridad": {"urgente": 1},
        "cantidad_por_confianza": {"media": 1},
        "compras_sugeridas": 1,
        "traslados_sugeridos": 0,
        "validaciones_datos_sugeridas": 0,
        "revisiones_maestro_sugeridas": 0,
    }


def test_recommendations_summary_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(recommendations, "get_recommendations_summary", lambda limit=250000: _summary())
    response = client.get("/recommendations/summary")
    assert response.status_code == 200
    assert response.json()["compras_sugeridas"] == 1


def test_recommendations_items_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_items_page",
        lambda **kwargs: {"items": [_record()], "total": 1, "limit": kwargs.get("limit", 50), "offset": kwargs.get("offset", 0), "has_next": False, "has_previous": False},
    )
    response = client.get("/recommendations/items")
    assert response.status_code == 200
    assert response.json()["items"][0]["recommendation_type"] == "comprar"
    assert response.json()["total"] == 1


def test_recommendations_item_detail_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_item_detail",
        lambda item_code: {
            "item_code": item_code,
            "item_name": "Articulo A",
            "recommendations_by_warehouse": [_record()],
            "coverage_diagnosis": {
                "item_code": item_code,
                "item_name": "Articulo A",
                "diagnostics_by_warehouse": [_record()],
                "stock_by_warehouse": [],
                "monthly_consumption": [],
                "open_documents": [],
                "summary": {
                    "total_articulos_evaluados": 1,
                    "total_combinaciones_evaluadas": 1,
                    "riesgo_critico": 1,
                    "riesgo_alto": 0,
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
                },
            },
            "stock_by_warehouse": [],
            "monthly_consumption": [],
            "open_documents": [],
            "purchase_enrichment": {
                "preferred_vendor_code": None,
                "preferred_vendor_name": None,
                "item_group_code": None,
                "item_group_name": None,
                "estimated_lead_time_days": None,
                "last_purchase_date": None,
                "last_purchase_vendor": None,
                "last_purchase_price": None,
                "min_stock": None,
                "max_stock": None,
                "min_purchase_qty": None,
                "purchase_multiple": None,
            },
            "summary": _summary(),
        },
    )
    response = client.get("/recommendations/item/A001")
    assert response.status_code == 200
    assert response.json()["item_code"] == "A001"


def test_recommendations_warehouses_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_warehouses",
        lambda limit=250000: [
            {
                "warehouse_code": "01",
                "warehouse_name": "Central",
                "recomendaciones_urgentes": 1,
                "recomendaciones_altas": 0,
                "compras_sugeridas": 1,
                "traslados_sugeridos": 0,
                "validaciones_datos": 0,
                "articulos_sin_accion": 0,
            }
        ],
    )
    response = client.get("/recommendations/warehouses")
    assert response.status_code == 200
    assert response.json()[0]["warehouse_code"] == "01"


def test_recommendations_actions_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_actions_page",
        lambda **kwargs: {
            "items": {
                "compras_sugeridas": [_record()],
                "traslados_sugeridos": [],
                "oc_abiertas_a_acelerar": [],
                "ov_a_revisar": [],
                "articulos_para_validar_datos": [],
                "articulos_para_revisar_maestro": [],
            },
            "total": 1,
            "limit": kwargs.get("limit", 50),
            "offset": kwargs.get("offset", 0),
            "has_next": False,
            "has_previous": False,
        },
    )
    response = client.get("/recommendations/actions")
    assert response.status_code == 200
    assert len(response.json()["items"]["compras_sugeridas"]) == 1


def test_recommendations_purchase_candidates_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_items_page",
        lambda **kwargs: {"items": [_record()], "total": 1, "limit": kwargs.get("limit", 50), "offset": kwargs.get("offset", 0), "has_next": False, "has_previous": False},
    )
    response = client.get("/recommendations/purchase-candidates")
    assert response.status_code == 200
    assert response.json()["items"][0]["recommendation_type"] == "comprar"


def test_recommendations_transfer_candidates_endpoint(monkeypatch) -> None:
    record = _record()
    record["recommendation_type"] = "trasladar_stock"
    record["source_warehouse"] = "02"
    record["target_warehouse"] = "01"
    record["transfer_candidate_quantity"] = 5.0
    monkeypatch.setattr(
        recommendations,
        "get_recommendation_items_page",
        lambda **kwargs: {"items": [record], "total": 1, "limit": kwargs.get("limit", 50), "offset": kwargs.get("offset", 0), "has_next": False, "has_previous": False},
    )
    response = client.get("/recommendations/transfer-candidates")
    assert response.status_code == 200
    assert response.json()["items"][0]["source_warehouse"] == "02"
