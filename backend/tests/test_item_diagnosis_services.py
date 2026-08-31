import json

from app.services.item_diagnosis_service import (
    PROJECTED_NOTE,
    build_availability_audit,
    build_projected_kardex,
    group_related_documents,
)


def _recommendation(**overrides) -> dict:
    record = {
        "item_code": "A001",
        "item_name": "Articulo A",
        "warehouse_code": "01",
        "stock_disponible": 100.0,
        "entradas_abiertas": 40.0,
        "salidas_abiertas": 15.0,
        "consumo_base_diario": 1.0,
        "suggested_horizon_days": 90,
        "min_stock": 10.0,
        "suggested_quantity": 20.0,
        "recommendation_type": "comprar",
        "recommendation_confidence": "media",
        "nivel_riesgo": "alto",
        "priority_reasons": ["Riesgo alto"],
        "motivos_riesgo": ["Deficit proyectado"],
        "data_quality_notes": [],
        "main_message": "Comprar cantidad referencial",
        "next_action_description": "Validar compra antes de operar",
    }
    record.update(overrides)
    return record


def _movements() -> list[dict]:
    return [
        {
            "doc_date": "2026-01-03",
            "movement_category": "consumo_candidato",
            "base_ref": "SAL-1",
            "warehouse": "01",
            "in_qty": 0.0,
            "out_qty": 20.0,
        },
        {
            "doc_date": "2026-01-01",
            "movement_category": "entrada_devolucion_o_revisable",
            "base_ref": "ENT-1",
            "warehouse": "01",
            "in_qty": 50.0,
            "out_qty": 0.0,
        },
    ]


def _documents() -> list[dict]:
    return [
        {
            "tipo_documento": "orden_compra",
            "doc_num": "OC-1",
            "fecha_documento": "2026-01-04",
            "fecha_entrega": "2026-01-10",
            "warehouse_code": "01",
            "cantidad_abierta": 40.0,
            "direction": "entrada",
            "card_name": "Proveedor",
            "estado_documento": "Abierto",
        },
        {
            "tipo_documento": "orden_venta",
            "doc_num": "OV-1",
            "fecha_documento": "2026-01-05",
            "fecha_entrega": "2026-01-11",
            "warehouse_code": "01",
            "cantidad_abierta": 15.0,
            "direction": "salida",
            "card_name": "Cliente",
            "estado_documento": "Abierto",
        },
        {
            "tipo_documento": "orden_fabricacion",
            "doc_num": "OF-1",
            "fecha_documento": "2026-01-06",
            "warehouse_code": "01",
            "cantidad_abierta": 5.0,
            "direction": "salida",
        },
        {
            "tipo_documento": "solicitud_traslado",
            "doc_num": "TR-1",
            "fecha_documento": "2026-01-07",
            "warehouse_code": "01",
            "cantidad_abierta": 3.0,
            "direction": "entrada",
        },
    ]


def test_availability_audit_calculates_estimated_need_and_formula() -> None:
    audit = build_availability_audit(_recommendation())

    assert audit["stock_final_estimado"] == 25.0
    assert audit["necesidad_estimada"] == 0.0
    assert audit["exceso_estimado"] == 25.0
    assert audit["cantidad_sugerida"] == 20.0
    assert [line["label"] for line in audit["formula_lines"]] == [
        "Stock disponible",
        "Ingresos esperados",
        "Salidas comprometidas",
        "Salidas proyectadas",
        "Stock de seguridad",
        "Necesidad o exceso estimado",
    ]


def test_projected_kardex_is_sorted_and_reconciles_estimated_balance() -> None:
    rows = build_projected_kardex("A001", _recommendation(), _movements(), _documents(), warehouse="01")

    assert [row["sort_key"] for row in rows] == sorted(row["sort_key"] for row in rows)
    assert rows[0]["saldo_estimado"] == 120.0
    assert rows[1]["saldo_estimado"] == 100.0
    assert rows[-1]["origen"] == "Diagnóstico"
    assert rows[-1]["saldo_estimado"] == 25.0


def test_projected_movements_are_marked_as_not_registered_in_sap() -> None:
    rows = build_projected_kardex("A001", _recommendation(), _movements(), _documents(), warehouse="01")
    projected = [row for row in rows if row["origen"] == "Proyección"]

    assert projected
    assert all(row["nota"] == PROJECTED_NOTE for row in projected)


def test_related_documents_are_grouped_with_functional_labels() -> None:
    grouped = group_related_documents(_documents())

    assert grouped["ingresos_esperados"][0]["tipo_funcional"] == "Ingreso esperado"
    assert grouped["salidas_comprometidas"][0]["tipo_funcional"] == "Salida comprometida"
    assert grouped["produccion_pendiente"][0]["tipo_funcional"] == "Produccion pendiente"
    assert grouped["traslados_pendientes"][0]["tipo_funcional"] == "Traslado pendiente"


def test_visible_diagnosis_texts_do_not_expose_technical_table_names() -> None:
    rows = build_projected_kardex("A001", _recommendation(), _movements(), _documents(), warehouse="01")
    grouped = group_related_documents(_documents())
    audit = build_availability_audit(_recommendation())
    visible_payload = json.dumps({"kardex": rows, "documents": grouped, "audit": audit}, ensure_ascii=False)

    for technical_name in ("OINM", "OITW", "OPOR", "POR1", "ORDR", "RDR1", "OWOR", "WOR1"):
        assert technical_name not in visible_payload
