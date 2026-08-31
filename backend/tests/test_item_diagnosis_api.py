from fastapi.testclient import TestClient

from app.api.routes import item_diagnosis
from app.main import app


client = TestClient(app)


def _audit() -> dict:
    return {
        "stock_disponible": 100.0,
        "ingresos_esperados": 40.0,
        "salidas_comprometidas": 15.0,
        "salidas_proyectadas": 90.0,
        "stock_seguridad": 10.0,
        "stock_final_estimado": 25.0,
        "necesidad_estimada": 0.0,
        "exceso_estimado": 25.0,
        "cantidad_sugerida": 20.0,
        "accion_recomendada": "comprar",
        "confianza": "media",
        "riesgo": "alto",
        "formula_lines": [
            {"label": "Stock disponible", "operator": "+", "value": 100.0},
            {"label": "Ingresos esperados", "operator": "+", "value": 40.0},
            {"label": "Salidas comprometidas", "operator": "-", "value": 15.0},
            {"label": "Salidas proyectadas", "operator": "-", "value": 90.0},
            {"label": "Stock de seguridad", "operator": "-", "value": 10.0},
            {"label": "Necesidad o exceso estimado", "operator": "=", "value": 25.0},
        ],
    }


def _related_documents() -> dict:
    return {
        "ingresos_esperados": [
            {
                "tipo_funcional": "Ingreso esperado",
                "numero_documento": "OC-1",
                "fecha": "2026-01-04",
                "fecha_esperada": "2026-01-10",
                "socio_negocio": "Proveedor",
                "almacen": "01",
                "cantidad_abierta": 40.0,
                "estado": "Abierto",
            }
        ],
        "salidas_comprometidas": [],
        "produccion_pendiente": [],
        "traslados_pendientes": [],
    }


def _kardex() -> list[dict]:
    return [
        {
            "fecha_periodo": "2026-01-01",
            "tipo_movimiento": "Ingreso registrado",
            "documento_referencia": "ENT-1",
            "almacen": "01",
            "entrada": 50.0,
            "salida": 0.0,
            "saldo_estimado": 120.0,
            "origen": "SAP real",
            "nota": None,
            "sort_key": "2026-01-01",
        },
        {
            "fecha_periodo": "2026-02",
            "tipo_movimiento": "Salida proyectada",
            "documento_referencia": None,
            "almacen": "01",
            "entrada": 0.0,
            "salida": 30.0,
            "saldo_estimado": 90.0,
            "origen": "Proyección",
            "nota": "Movimiento proyectado, no registrado en SAP.",
            "sort_key": "2026-02-01",
        },
    ]


def _diagnosis_response(item_code: str = "A001") -> dict:
    audit = _audit()
    return {
        "item": {"item_code": item_code, "item_name": "Articulo A", "warehouse": "01"},
        "recomendacion_principal": {"item_code": item_code, "warehouse_code": "01", "priority_score": 80},
        "riesgo": "alto",
        "confianza": "media",
        "cantidad_sugerida": 20.0,
        "advertencias": ["Cantidad referencial", "Requiere validacion humana", "No genera documentos SAP"],
        "auditoria_disponibilidad": audit,
        "kardex_proyectado": _kardex(),
        "documentos_sap_relacionados": _related_documents(),
        "stock_por_almacen": [{"warehouse_code": "01", "stock_disponible": 100.0}],
        "trazabilidad": {
            "motivos_recomendacion": ["Riesgo alto"],
            "motivos_riesgo": ["Deficit proyectado"],
            "notas_calidad_datos": [],
            "advertencias": ["Cantidad referencial", "Requiere validacion humana", "No genera documentos SAP"],
            "formula_resumen": audit["formula_lines"],
            "mensaje_principal": "Comprar cantidad referencial",
            "siguiente_accion": "Validar compra antes de operar",
        },
    }


def test_item_diagnosis_endpoint_returns_200(monkeypatch) -> None:
    monkeypatch.setattr(item_diagnosis, "get_item_diagnosis", lambda item_code, warehouse=None: _diagnosis_response(item_code))

    response = client.get("/item-diagnosis/A001?warehouse=01")

    assert response.status_code == 200
    assert response.json()["item"]["item_code"] == "A001"
    assert response.json()["auditoria_disponibilidad"]["cantidad_sugerida"] == 20.0


def test_projected_kardex_endpoint_returns_rows(monkeypatch) -> None:
    monkeypatch.setattr(item_diagnosis, "get_item_projected_kardex", lambda item_code, warehouse=None: _kardex())

    response = client.get("/item-diagnosis/A001/projected-kardex")

    assert response.status_code == 200
    assert response.json()[1]["origen"] == "Proyección"


def test_availability_audit_endpoint_returns_explainable_formula(monkeypatch) -> None:
    monkeypatch.setattr(item_diagnosis, "get_item_availability_audit", lambda item_code, warehouse=None: _audit())

    response = client.get("/item-diagnosis/A001/availability-audit")

    assert response.status_code == 200
    assert response.json()["formula_lines"][-1]["label"] == "Necesidad o exceso estimado"


def test_related_documents_endpoint_returns_functional_groups(monkeypatch) -> None:
    monkeypatch.setattr(item_diagnosis, "get_item_related_documents", lambda item_code, warehouse=None: _related_documents())

    response = client.get("/item-diagnosis/A001/related-documents")

    assert response.status_code == 200
    assert response.json()["ingresos_esperados"][0]["tipo_funcional"] == "Ingreso esperado"
