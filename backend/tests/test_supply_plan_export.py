from scripts.export_supply_plan import _action_label, _row, _safe_next_action


def test_supply_plan_export_uses_safe_functional_actions() -> None:
    record = {
        "item_code": "A001",
        "item_name": "Articulo A",
        "warehouse_code": "01",
        "recommendation_type": "comprar",
        "nivel_riesgo": "critico",
        "suggested_quantity": 12.0,
        "priority_level": "urgente",
        "recommendation_confidence": "alta",
        "business_reason": "Inventario actual insuficiente frente a salidas proyectadas.",
    }

    assert _action_label(record) == "Atender riesgo crítico"
    assert _safe_next_action(record) == "Validar con logística"
    assert _row(record)["acción recomendada"] == "Atender riesgo crítico"


def test_supply_plan_export_does_not_use_document_creation_language() -> None:
    labels = [
        _action_label({"recommendation_type": "comprar", "nivel_riesgo": "alto"}),
        _safe_next_action({"recommendation_type": "comprar"}),
        _safe_next_action({"recommendation_type": "acelerar_compra_abierta"}),
    ]

    visible_text = " ".join(labels)
    assert "Generar OC" not in visible_text
    assert "Crear documento SAP" not in visible_text
    assert "Comprar ahora" not in visible_text
