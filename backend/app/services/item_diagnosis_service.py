from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.services.inventory_movements_service import get_inventory_movements_by_item
from app.services.open_documents_service import get_open_documents
from app.services.recommendation_service import get_recommendation_item_detail
from app.services.stock_position_service import get_stock_item_detail


PROJECTED_NOTE = "Movimiento proyectado, no registrado en SAP."


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        return date.fromisoformat(str(value)[:10])
    return date.today()


def _period_label(base_date: date, offset_days: int) -> str:
    target = base_date + timedelta(days=offset_days)
    return target.strftime("%Y-%m")


def _document_number(document: dict[str, Any]) -> str | None:
    value = document.get("doc_num") or document.get("doc_entry")
    return str(value) if value is not None else None


def _functional_document_type(document: dict[str, Any]) -> str:
    mapping = {
        "orden_compra": "Ingreso esperado",
        "orden_venta": "Salida comprometida",
        "orden_fabricacion": "Produccion pendiente",
        "solicitud_traslado": "Traslado pendiente",
    }
    return mapping.get(str(document.get("tipo_documento")), "Documento SAP relacionado")


def _functional_movement_type(category: Any, in_qty: float, out_qty: float) -> str:
    if in_qty > 0:
        return "Ingreso registrado"
    if out_qty > 0:
        return "Salida registrada"
    mapping = {
        "transferencia": "Movimiento entre almacenes",
        "ajuste_revisable": "Ajuste de inventario",
        "consumo_candidato": "Salida de inventario",
        "entrada_devolucion_o_revisable": "Movimiento de inventario",
    }
    return mapping.get(str(category), "Movimiento de inventario")


def select_main_recommendation(recommendations: list[dict[str, Any]], warehouse: str | None = None) -> dict[str, Any] | None:
    candidates = [item for item in recommendations if not warehouse or item.get("warehouse_code") == warehouse]
    if not candidates:
        candidates = recommendations
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: float(item.get("priority_score") or 0.0), reverse=True)[0]


def build_availability_audit(recommendation: dict[str, Any] | None) -> dict[str, Any]:
    recommendation = recommendation or {}
    stock_disponible = _to_float(recommendation.get("stock_disponible"))
    ingresos = _to_float(recommendation.get("entradas_abiertas"))
    salidas_comprometidas = _to_float(recommendation.get("salidas_abiertas"))
    horizon = int(recommendation.get("suggested_horizon_days") or 90)
    daily_consumption = _to_float(recommendation.get("consumo_base_diario"))
    salidas_proyectadas = daily_consumption * horizon if daily_consumption > 0 else 0.0
    stock_seguridad = _to_float(recommendation.get("min_stock")) or 0.0
    stock_final = stock_disponible + ingresos - salidas_comprometidas - salidas_proyectadas - stock_seguridad
    necesidad = max(0.0, -stock_final)
    exceso = max(0.0, stock_final)
    suggested = _to_float(recommendation.get("suggested_quantity")) or necesidad
    return {
        "stock_disponible": stock_disponible,
        "ingresos_esperados": ingresos,
        "salidas_comprometidas": salidas_comprometidas,
        "salidas_proyectadas": salidas_proyectadas,
        "stock_seguridad": stock_seguridad,
        "stock_final_estimado": stock_final,
        "necesidad_estimada": necesidad,
        "exceso_estimado": exceso,
        "cantidad_sugerida": suggested,
        "accion_recomendada": recommendation.get("recommendation_type") or "sin_recomendacion",
        "confianza": recommendation.get("recommendation_confidence") or recommendation.get("nivel_confianza") or "sin_confianza",
        "riesgo": recommendation.get("nivel_riesgo") or "sin_diagnostico",
        "formula_lines": [
            {"label": "Stock disponible", "operator": "+", "value": stock_disponible},
            {"label": "Ingresos esperados", "operator": "+", "value": ingresos},
            {"label": "Salidas comprometidas", "operator": "-", "value": salidas_comprometidas},
            {"label": "Salidas proyectadas", "operator": "-", "value": salidas_proyectadas},
            {"label": "Stock de seguridad", "operator": "-", "value": stock_seguridad},
            {"label": "Necesidad o exceso estimado", "operator": "=", "value": stock_final},
        ],
    }


def group_related_documents(documents: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped = {
        "ingresos_esperados": [],
        "salidas_comprometidas": [],
        "produccion_pendiente": [],
        "traslados_pendientes": [],
    }
    for document in documents:
        tipo = str(document.get("tipo_documento"))
        row = {
            "tipo_funcional": _functional_document_type(document),
            "numero_documento": _document_number(document),
            "fecha": document.get("fecha_documento"),
            "fecha_esperada": document.get("fecha_entrega"),
            "socio_negocio": document.get("card_name") or document.get("card_code"),
            "almacen": document.get("warehouse_code"),
            "cantidad_abierta": _to_float(document.get("cantidad_abierta")),
            "estado": document.get("estado_linea") or document.get("estado_documento") or "Abierto",
        }
        if tipo == "orden_compra":
            grouped["ingresos_esperados"].append(row)
        elif tipo == "orden_venta":
            grouped["salidas_comprometidas"].append(row)
        elif tipo == "orden_fabricacion":
            grouped["produccion_pendiente"].append(row)
        elif tipo == "solicitud_traslado":
            grouped["traslados_pendientes"].append(row)
    return grouped


def build_projected_kardex(
    item_code: str,
    recommendation: dict[str, Any] | None,
    movements: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    warehouse: str | None = None,
    limit_real_movements: int = 12,
) -> list[dict[str, Any]]:
    recommendation = recommendation or {}
    selected_warehouse = warehouse or recommendation.get("warehouse_code")
    filtered_movements = [
        movement
        for movement in movements
        if not selected_warehouse or movement.get("warehouse") == selected_warehouse
    ][:limit_real_movements]
    filtered_movements = sorted(filtered_movements, key=lambda row: _parse_date(row.get("doc_date")))
    net_recent = sum(_to_float(row.get("in_qty")) - _to_float(row.get("out_qty")) for row in filtered_movements)
    saldo = _to_float(recommendation.get("stock_disponible")) - net_recent
    rows: list[dict[str, Any]] = []

    for movement in filtered_movements:
        entrada = _to_float(movement.get("in_qty"))
        salida = _to_float(movement.get("out_qty"))
        saldo += entrada - salida
        rows.append(
            {
                "fecha_periodo": movement.get("doc_date"),
                "tipo_movimiento": _functional_movement_type(movement.get("movement_category"), entrada, salida),
                "documento_referencia": movement.get("base_ref"),
                "almacen": movement.get("warehouse"),
                "entrada": entrada,
                "salida": salida,
                "saldo_estimado": saldo,
                "origen": "SAP real",
                "nota": None,
                "sort_key": movement.get("doc_date") or "1900-01-01",
            }
        )

    open_documents = [
        document
        for document in documents
        if not selected_warehouse or document.get("warehouse_code") == selected_warehouse
    ]
    for document in sorted(open_documents, key=lambda row: row.get("fecha_entrega") or row.get("fecha_documento") or ""):
        qty = _to_float(document.get("cantidad_abierta"))
        entrada = qty if document.get("direction") == "entrada" else 0.0
        salida = qty if document.get("direction") == "salida" else 0.0
        saldo += entrada - salida
        rows.append(
            {
                "fecha_periodo": document.get("fecha_entrega") or document.get("fecha_documento"),
                "tipo_movimiento": _functional_document_type(document),
                "documento_referencia": _document_number(document),
                "almacen": document.get("warehouse_code"),
                "entrada": entrada,
                "salida": salida,
                "saldo_estimado": saldo,
                "origen": "SAP abierto",
                "nota": None,
                "sort_key": document.get("fecha_entrega") or document.get("fecha_documento") or "2999-12-31",
            }
        )

    base_date = date.today()
    daily = _to_float(recommendation.get("consumo_base_diario"))
    if daily > 0:
        for offset in (30, 60, 90):
            salida = daily * 30
            saldo -= salida
            rows.append(
                {
                    "fecha_periodo": _period_label(base_date, offset),
                    "tipo_movimiento": "Salida proyectada",
                    "documento_referencia": None,
                    "almacen": selected_warehouse,
                    "entrada": 0.0,
                    "salida": salida,
                    "saldo_estimado": saldo,
                    "origen": "Proyección",
                    "nota": PROJECTED_NOTE,
                    "sort_key": (base_date + timedelta(days=offset)).isoformat(),
                }
            )

    suggested = _to_float(recommendation.get("suggested_quantity"))
    if suggested > 0:
        saldo += suggested
        rows.append(
            {
                "fecha_periodo": "Recomendación",
                "tipo_movimiento": "Cantidad referencial sugerida",
                "documento_referencia": "Recomendación",
                "almacen": selected_warehouse,
                "entrada": suggested,
                "salida": 0.0,
                "saldo_estimado": saldo,
                "origen": "Recomendación",
                "nota": "Cantidad referencial. Requiere validacion humana. No genera documentos SAP.",
                "sort_key": "9999-12-30",
            }
        )

    audit = build_availability_audit(recommendation)
    rows.append(
        {
            "fecha_periodo": "Diagnóstico",
            "tipo_movimiento": "Resultado de auditoria",
            "documento_referencia": "Auditoria de disponibilidad",
            "almacen": selected_warehouse,
            "entrada": 0.0,
            "salida": 0.0,
            "saldo_estimado": audit["stock_final_estimado"],
            "origen": "Diagnóstico",
            "nota": "Resultado estimado para apoyar la decision.",
            "sort_key": "9999-12-31",
        }
    )

    return sorted(rows, key=lambda row: str(row["sort_key"]))


def build_traceability(recommendation: dict[str, Any] | None, audit: dict[str, Any]) -> dict[str, Any]:
    recommendation = recommendation or {}
    warnings = [
        "Cantidad referencial",
        "Requiere validacion humana",
        "No genera documentos SAP",
        recommendation.get("recommendation_warning"),
    ]
    return {
        "motivos_recomendacion": recommendation.get("priority_reasons", []),
        "motivos_riesgo": recommendation.get("motivos_riesgo", []),
        "notas_calidad_datos": recommendation.get("data_quality_notes", []),
        "advertencias": [warning for warning in warnings if warning],
        "formula_resumen": audit["formula_lines"],
        "mensaje_principal": recommendation.get("main_message") or "Sin recomendacion accionable",
        "siguiente_accion": recommendation.get("next_action_description") or "Revisar diagnostico del articulo.",
    }


def get_item_availability_audit(item_code: str, warehouse: str | None = None) -> dict[str, Any]:
    detail = get_recommendation_item_detail(item_code)
    recommendation = select_main_recommendation(detail.get("recommendations_by_warehouse", []), warehouse)
    return build_availability_audit(recommendation)


def get_item_related_documents(item_code: str, warehouse: str | None = None) -> dict[str, Any]:
    documents = get_open_documents(item_code=item_code, warehouse=warehouse, limit=100000)
    return group_related_documents(documents)


def get_item_projected_kardex(item_code: str, warehouse: str | None = None) -> list[dict[str, Any]]:
    detail = get_recommendation_item_detail(item_code)
    recommendation = select_main_recommendation(detail.get("recommendations_by_warehouse", []), warehouse)
    movements = get_inventory_movements_by_item(item_code, limit=50)
    documents = get_open_documents(item_code=item_code, warehouse=warehouse, limit=100000)
    return build_projected_kardex(item_code, recommendation, movements, documents, warehouse=warehouse)


def get_item_diagnosis(item_code: str, warehouse: str | None = None) -> dict[str, Any]:
    detail = get_recommendation_item_detail(item_code)
    recommendation = select_main_recommendation(detail.get("recommendations_by_warehouse", []), warehouse)
    stock_detail = get_stock_item_detail(item_code)
    documents = get_open_documents(item_code=item_code, warehouse=warehouse, limit=100000)
    movements = get_inventory_movements_by_item(item_code, limit=50)
    audit = build_availability_audit(recommendation)
    kardex = build_projected_kardex(item_code, recommendation, movements, documents, warehouse=warehouse)
    related_documents = group_related_documents(documents)
    return {
        "item": {
            "item_code": item_code,
            "item_name": detail.get("item_name"),
            "warehouse": warehouse or (recommendation or {}).get("warehouse_code"),
        },
        "recomendacion_principal": recommendation,
        "riesgo": (recommendation or {}).get("nivel_riesgo") or "sin_diagnostico",
        "confianza": (recommendation or {}).get("recommendation_confidence") or (recommendation or {}).get("nivel_confianza") or "sin_confianza",
        "cantidad_sugerida": _to_float((recommendation or {}).get("suggested_quantity")),
        "advertencias": [
            "Cantidad referencial",
            "Requiere validacion humana",
            "No genera documentos SAP",
        ],
        "auditoria_disponibilidad": audit,
        "kardex_proyectado": kardex,
        "documentos_sap_relacionados": related_documents,
        "stock_por_almacen": stock_detail.get("stock_by_warehouse", []),
        "trazabilidad": build_traceability(recommendation, audit),
    }
