from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.db.session import execute_read_query
from app.services.coverage_risk_service import get_coverage_reconciliation, get_coverage_risk_item_detail, get_coverage_risk_items
from app.services.consumption_history_service import get_monthly_consumption
from app.services.open_documents_service import get_open_documents
from app.services.stock_position_service import get_stock_item_detail, get_table_columns, get_table_type, table_exists


PURCHASE_ENRICHMENT_SOURCES: dict[str, dict[str, Any]] = {
    "OITM": {
        "description": "Maestro de articulos",
        "candidate_columns": ["ItemCode", "ItemName", "CardCode", "ItmsGrpCod", "MinLevel", "MaxLevel", "MinOrdrQty", "OrdrMulti", "LeadTime", "InvntItem", "validFor"],
    },
    "OCRD": {
        "description": "Socios de negocio/proveedores",
        "candidate_columns": ["CardCode", "CardName", "CardType"],
    },
    "OITB": {
        "description": "Grupos de articulos",
        "candidate_columns": ["ItmsGrpCod", "ItmsGrpNam"],
    },
    "OPOR": {
        "description": "Ordenes de compra",
        "candidate_columns": ["DocEntry", "DocDate", "DocDueDate", "CardCode", "CardName", "DocStatus"],
    },
    "POR1": {
        "description": "Lineas de ordenes de compra",
        "candidate_columns": ["DocEntry", "ItemCode", "Price", "Quantity", "OpenQty", "LineStatus"],
    },
    "OPDN": {
        "description": "Entradas de mercancia por compra",
        "candidate_columns": ["DocEntry", "DocDate", "CardCode", "CardName", "CANCELED"],
    },
    "PDN1": {
        "description": "Lineas de entradas de mercancia por compra",
        "candidate_columns": ["DocEntry", "ItemCode", "Price", "Quantity"],
    },
}

DEFAULT_ENRICHMENT: dict[str, Any] = {
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
}


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _first_existing(columns: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _none_sql(alias: str) -> str:
    return f"CAST(NULL AS nvarchar(100)) AS {alias}"


def _numeric_none_sql(alias: str) -> str:
    return f"CAST(NULL AS decimal(19, 6)) AS {alias}"


def diagnose_purchase_enrichment_sources() -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for table_name, config in PURCHASE_ENRICHMENT_SOURCES.items():
        source_type = get_table_type(table_name)
        columns = get_table_columns(table_name) if source_type else []
        diagnostics.append(
            {
                "source": table_name,
                "type": source_type,
                "exists": source_type is not None,
                "description": config["description"],
                "columns": columns,
                "candidate_columns_found": [column for column in config["candidate_columns"] if column in columns],
                "missing_candidate_columns": [column for column in config["candidate_columns"] if column not in columns],
            }
        )
    return diagnostics


def get_purchase_enrichment_for_item(item_code: str) -> dict[str, Any]:
    enrichment = DEFAULT_ENRICHMENT.copy()
    if not table_exists("OITM"):
        return enrichment
    item_columns = set(get_table_columns("OITM"))
    select_parts = ["I.ItemCode AS item_code"]
    vendor_column = _first_existing(item_columns, ["CardCode", "SuppCatNum"])
    group_column = _first_existing(item_columns, ["ItmsGrpCod"])
    min_stock_column = _first_existing(item_columns, ["MinLevel", "MinStock"])
    max_stock_column = _first_existing(item_columns, ["MaxLevel", "MaxStock"])
    min_purchase_column = _first_existing(item_columns, ["MinOrdrQty", "MinOrder", "MinPurQty"])
    multiple_column = _first_existing(item_columns, ["OrdrMulti", "OrderMultiple", "PurPackUn"])
    lead_time_column = _first_existing(item_columns, ["LeadTime", "AvgLeadTime"])

    select_parts.append(f"I.{vendor_column} AS preferred_vendor_code" if vendor_column else _none_sql("preferred_vendor_code"))
    select_parts.append(f"I.{group_column} AS item_group_code" if group_column else _none_sql("item_group_code"))
    select_parts.append(f"CAST(I.{min_stock_column} AS decimal(19, 6)) AS min_stock" if min_stock_column else _numeric_none_sql("min_stock"))
    select_parts.append(f"CAST(I.{max_stock_column} AS decimal(19, 6)) AS max_stock" if max_stock_column else _numeric_none_sql("max_stock"))
    select_parts.append(f"CAST(I.{min_purchase_column} AS decimal(19, 6)) AS min_purchase_qty" if min_purchase_column else _numeric_none_sql("min_purchase_qty"))
    select_parts.append(f"CAST(I.{multiple_column} AS decimal(19, 6)) AS purchase_multiple" if multiple_column else _numeric_none_sql("purchase_multiple"))
    select_parts.append(f"CAST(I.{lead_time_column} AS decimal(19, 6)) AS estimated_lead_time_days" if lead_time_column else _numeric_none_sql("estimated_lead_time_days"))

    joins = ""
    if vendor_column and table_exists("OCRD"):
        card_columns = set(get_table_columns("OCRD"))
        if {"CardCode", "CardName"}.issubset(card_columns):
            joins += f" LEFT JOIN OCRD V ON V.CardCode = I.{vendor_column}"
            select_parts.append("V.CardName AS preferred_vendor_name")
        else:
            select_parts.append(_none_sql("preferred_vendor_name"))
    else:
        select_parts.append(_none_sql("preferred_vendor_name"))

    if group_column and table_exists("OITB"):
        group_columns = set(get_table_columns("OITB"))
        if {"ItmsGrpCod", "ItmsGrpNam"}.issubset(group_columns):
            joins += f" LEFT JOIN OITB G ON G.ItmsGrpCod = I.{group_column}"
            select_parts.append("G.ItmsGrpNam AS item_group_name")
        else:
            select_parts.append(_none_sql("item_group_name"))
    else:
        select_parts.append(_none_sql("item_group_name"))

    rows = execute_read_query(
        f"""
        SELECT TOP 1 {", ".join(select_parts)}
        FROM OITM I
        {joins}
        WHERE I.ItemCode = :item_code
        """,
        {"item_code": item_code},
    )
    if rows:
        row = rows[0]
        enrichment.update(
            {
                "preferred_vendor_code": row.get("preferred_vendor_code"),
                "preferred_vendor_name": row.get("preferred_vendor_name"),
                "item_group_code": str(row.get("item_group_code")) if row.get("item_group_code") is not None else None,
                "item_group_name": row.get("item_group_name"),
                "estimated_lead_time_days": _to_float(row.get("estimated_lead_time_days")),
                "min_stock": _to_float(row.get("min_stock")),
                "max_stock": _to_float(row.get("max_stock")),
                "min_purchase_qty": _to_float(row.get("min_purchase_qty")),
                "purchase_multiple": _to_float(row.get("purchase_multiple")),
            }
        )
    enrichment.update(_get_last_purchase_data(item_code))
    return enrichment


def _get_last_purchase_data(item_code: str) -> dict[str, Any]:
    if table_exists("OPDN") and table_exists("PDN1"):
        rows = execute_read_query(
            """
            SELECT TOP 1
                H.DocDate AS last_purchase_date,
                H.CardName AS last_purchase_vendor,
                CAST(ISNULL(L.Price, 0) AS decimal(19, 6)) AS last_purchase_price
            FROM OPDN H
            INNER JOIN PDN1 L ON L.DocEntry = H.DocEntry
            WHERE ISNULL(H.CANCELED, 'N') = 'N'
              AND L.ItemCode = :item_code
            ORDER BY H.DocDate DESC, H.DocEntry DESC
            """,
            {"item_code": item_code},
        )
        if rows:
            row = rows[0]
            return {
                "last_purchase_date": _to_iso(row.get("last_purchase_date")),
                "last_purchase_vendor": row.get("last_purchase_vendor"),
                "last_purchase_price": _to_float(row.get("last_purchase_price")),
            }
    if table_exists("OPOR") and table_exists("POR1"):
        rows = execute_read_query(
            """
            SELECT TOP 1
                H.DocDate AS last_purchase_date,
                H.CardName AS last_purchase_vendor,
                CAST(ISNULL(L.Price, 0) AS decimal(19, 6)) AS last_purchase_price
            FROM OPOR H
            INNER JOIN POR1 L ON L.DocEntry = H.DocEntry
            WHERE ISNULL(H.CANCELED, 'N') = 'N'
              AND L.ItemCode = :item_code
            ORDER BY H.DocDate DESC, H.DocEntry DESC
            """,
            {"item_code": item_code},
        )
        if rows:
            row = rows[0]
            return {
                "last_purchase_date": _to_iso(row.get("last_purchase_date")),
                "last_purchase_vendor": row.get("last_purchase_vendor"),
                "last_purchase_price": _to_float(row.get("last_purchase_price")),
            }
    return {"last_purchase_date": None, "last_purchase_vendor": None, "last_purchase_price": None}


def calculate_suggested_quantities(diagnostic: dict[str, Any]) -> dict[str, Any]:
    quantities = {
        "suggested_quantity_30d": float(diagnostic.get("deficit_30_dias") or 0.0),
        "suggested_quantity_60d": float(diagnostic.get("deficit_60_dias") or 0.0),
        "suggested_quantity_90d": float(diagnostic.get("deficit_90_dias") or 0.0),
    }
    risk = diagnostic.get("nivel_riesgo")
    if risk == "critico":
        horizon = 30
        suggested = quantities["suggested_quantity_30d"]
    elif risk == "alto":
        horizon = 60
        suggested = quantities["suggested_quantity_60d"]
    elif risk == "medio":
        horizon = 90
        suggested = quantities["suggested_quantity_90d"]
    else:
        horizon = None
        suggested = 0.0
    return {**quantities, "suggested_horizon_days": horizon, "suggested_quantity": suggested}


def calculate_lead_time_indicators(diagnostic: dict[str, Any], enrichment: dict[str, Any]) -> dict[str, Any]:
    lead_time = enrichment.get("estimated_lead_time_days")
    daily = float(diagnostic.get("consumo_base_diario") or 0.0)
    if not lead_time or daily <= 0:
        return {
            "demand_during_lead_time": None,
            "coverage_after_lead_time": None,
            "lead_time_risk": "no_calculable",
        }
    demand = daily * float(lead_time)
    after_lead_time = float(diagnostic.get("stock_proyectado_con_partidas") or 0.0) - demand
    if after_lead_time <= 0:
        risk = "alto"
    elif after_lead_time <= demand:
        risk = "medio"
    else:
        risk = "bajo"
    return {
        "demand_during_lead_time": demand,
        "coverage_after_lead_time": after_lead_time,
        "lead_time_risk": risk,
    }


def calculate_priority(diagnostic: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 0.0
    reasons: list[str] = []
    risk = diagnostic.get("nivel_riesgo")
    if risk == "critico":
        score += 40
        reasons.append("Riesgo critico")
    elif risk == "alto":
        score += 30
        reasons.append("Riesgo alto")
    elif risk == "medio":
        score += 18
        reasons.append("Riesgo medio")
    elif risk == "bajo":
        score += 8
        reasons.append("Riesgo bajo")

    if diagnostic.get("deficit_30_dias", 0) > 0:
        score += 20
        reasons.append("Deficit proyectado a 30 dias")
    if diagnostic.get("deficit_60_dias", 0) > 0:
        score += 10
        reasons.append("Deficit proyectado a 60 dias")
    if diagnostic.get("deficit_90_dias", 0) > 0:
        score += 5
        reasons.append("Deficit proyectado a 90 dias")
    coverage = diagnostic.get("cobertura_dias_stock_proyectado")
    if coverage is not None and coverage <= 15:
        score += 15
        reasons.append("Cobertura menor a 15 dias")
    if diagnostic.get("stock_disponible", 0) < 0:
        score += 10
        reasons.append("Stock disponible negativo")
    if diagnostic.get("stock_comprometido_sap", 0) > diagnostic.get("stock_fisico", 0):
        score += 10
        reasons.append("Comprometido SAP mayor al stock fisico")
    if diagnostic.get("salidas_abiertas", 0) > diagnostic.get("stock_disponible", 0):
        score += 6
        reasons.append("OV abiertas superan stock disponible")
    if diagnostic.get("entradas_abiertas", 0) > 0:
        score -= 3
        reasons.append("OC abierta pendiente de recepcion")

    confidence = diagnostic.get("nivel_confianza")
    if confidence == "alta":
        score += 10
    elif confidence == "media":
        score += 6
    elif confidence == "baja":
        score -= 5
        reasons.append("Baja confianza por consumo intermitente")
    elif confidence == "sin_confianza":
        score -= 15

    if diagnostic.get("fecha_ultimo_consumo"):
        score += 5
        reasons.append("Consumo reciente detectado")
    if diagnostic.get("tipo_demanda") == "demanda_estable":
        score += 5
        reasons.append("Demanda estable con consumo reciente")
    elif diagnostic.get("tipo_demanda") == "demanda_intermitente":
        score -= 5
        reasons.append("Demanda intermitente")

    score = _clamp(score)
    if score >= 80:
        level = "urgente"
    elif score >= 60:
        level = "alta"
    elif score >= 40:
        level = "media"
    elif score >= 20:
        level = "baja"
    else:
        level = "informativa"
    return score, level, list(dict.fromkeys(reasons))


def _find_transfer_candidate(target: dict[str, Any], item_diagnostics: list[dict[str, Any]]) -> dict[str, Any] | None:
    target_deficit = max(float(target.get("deficit_30_dias") or 0.0), float(target.get("deficit_60_dias") or 0.0), float(target.get("deficit_90_dias") or 0.0))
    if target_deficit <= 0:
        return None
    candidates = []
    for source in item_diagnostics:
        if source.get("warehouse_code") == target.get("warehouse_code"):
            continue
        if source.get("nivel_riesgo") == "critico":
            continue
        excess = max(float(source.get("sobrante_90_dias") or 0.0), float(source.get("stock_proyectado_con_partidas") or 0.0) - float(source.get("consumo_base_mensual") or 0.0))
        if excess <= 0:
            continue
        quantity = min(target_deficit, excess)
        if quantity <= 0:
            continue
        remaining = float(source.get("stock_proyectado_con_partidas") or 0.0) - quantity
        if remaining <= 0:
            continue
        candidates.append((quantity, source, remaining))
    if not candidates:
        return None
    quantity, source, remaining = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {
        "source_warehouse": source.get("warehouse_code"),
        "target_warehouse": target.get("warehouse_code"),
        "transfer_candidate_quantity": quantity,
        "source_projected_stock_before_transfer": float(source.get("stock_proyectado_con_partidas") or 0.0),
        "target_projected_stock_before_transfer": float(target.get("stock_proyectado_con_partidas") or 0.0),
        "source_remaining_stock_after_transfer": remaining,
        "target_projected_stock_after_transfer": float(target.get("stock_proyectado_con_partidas") or 0.0) + quantity,
        "transfer_reason": "Otro almacen tiene stock proyectado excedente y no queda en riesgo critico.",
    }


def _classify_recommendation(
    diagnostic: dict[str, Any],
    transfer_candidate: dict[str, Any] | None,
    reconciliation: dict[str, Any],
) -> tuple[str, str]:
    item_code = str(diagnostic.get("item_code"))
    risk = diagnostic.get("nivel_riesgo")
    confidence = diagnostic.get("nivel_confianza")
    has_deficit = any(float(diagnostic.get(f"deficit_{days}_dias") or 0.0) > 0 for days in (30, 60, 90))
    has_open_purchase = float(diagnostic.get("entradas_abiertas") or 0.0) > 0
    has_consumption = int(diagnostic.get("meses_con_consumo") or 0) > 0
    has_stock = float(diagnostic.get("stock_fisico") or 0.0) > 0

    if item_code in set(reconciliation.get("articulos_stock_sin_consumo_historico", [])) and has_stock and not has_consumption:
        return "revisar_maestro_articulo", "requiere_validacion"
    if item_code in set(reconciliation.get("articulos_consumo_sin_stock_actual", [])) or item_code in set(reconciliation.get("articulos_partidas_abiertas_sin_stock_actual", [])):
        return "revisar_maestro_articulo", "requiere_validacion"
    if confidence == "sin_confianza" or risk == "sin_diagnostico":
        return "validar_datos", "datos_insuficientes"
    if diagnostic.get("stock_comprometido_sap", 0) > diagnostic.get("stock_fisico", 0) or (
        diagnostic.get("salidas_abiertas", 0) > diagnostic.get("stock_disponible", 0) and diagnostic.get("stock_proyectado_con_partidas", 0) < 0
    ):
        return "revisar_venta_comprometida", "requiere_validacion"
    if transfer_candidate and risk in {"critico", "alto"}:
        return "trasladar_stock", "requiere_validacion"
    if has_open_purchase and risk in {"critico", "alto"} and has_deficit:
        return "acelerar_compra_abierta", "requiere_validacion"
    if risk in {"critico", "alto"} and has_deficit and diagnostic.get("consumo_base_mensual", 0) > 0:
        if confidence in {"alta", "media"}:
            return "comprar", "accion_recomendada"
        if confidence == "baja" and risk == "critico":
            return "comprar", "requiere_validacion"
    if risk in {"medio", "bajo"}:
        return "monitorear", "solo_monitoreo"
    if risk == "sin_riesgo_aparente":
        return "no_comprar", "no_accion"
    return "sin_recomendacion", "datos_insuficientes"


def build_recommendation_record(
    diagnostic: dict[str, Any],
    item_diagnostics: list[dict[str, Any]] | None = None,
    enrichment: dict[str, Any] | None = None,
    reconciliation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item_diagnostics = item_diagnostics or [diagnostic]
    enrichment = enrichment or DEFAULT_ENRICHMENT.copy()
    reconciliation = reconciliation or {}
    suggested = calculate_suggested_quantities(diagnostic)
    lead_time = calculate_lead_time_indicators(diagnostic, enrichment)
    priority_score, priority_level, priority_reasons = calculate_priority(diagnostic)
    transfer_candidate = _find_transfer_candidate(diagnostic, item_diagnostics)
    recommendation_type, status = _classify_recommendation(diagnostic, transfer_candidate, reconciliation)

    warnings = [
        "Cantidad referencial basada en consumo historico",
        "No considera minimos de proveedor porque no fueron detectados" if not enrichment.get("min_purchase_qty") else "Minimo de compra detectado desde SAP",
        "No considera lead time real si no esta disponible" if not enrichment.get("estimated_lead_time_days") else "Lead time estimado detectado desde SAP",
        "Requiere validacion de logistica antes de comprar",
    ]
    data_quality_notes = list(diagnostic.get("motivos_riesgo", []))
    if lead_time["lead_time_risk"] == "no_calculable":
        data_quality_notes.append("Lead time no disponible en SAP o no detectado")
    if diagnostic.get("nivel_confianza") in {"baja", "sin_confianza"}:
        data_quality_notes.append(diagnostic.get("motivo_confianza"))

    actionable_quantity = suggested["suggested_quantity"] if recommendation_type == "comprar" else 0.0
    if recommendation_type == "comprar" and enrichment.get("min_purchase_qty"):
        actionable_quantity = max(actionable_quantity, float(enrichment["min_purchase_qty"]))
    if recommendation_type == "comprar" and enrichment.get("purchase_multiple") and enrichment["purchase_multiple"] > 0 and actionable_quantity > 0:
        multiple = float(enrichment["purchase_multiple"])
        actionable_quantity = ((int((actionable_quantity + multiple - 1) // multiple)) * multiple)

    if recommendation_type == "comprar":
        main_message = f"Comprar {actionable_quantity:.2f} unidades referenciales"
        next_label = "Validar compra"
        next_description = "Revisar proveedor, minimo de compra y fecha requerida antes de generar OC."
    elif recommendation_type == "trasladar_stock" and transfer_candidate:
        main_message = f"Trasladar {transfer_candidate['transfer_candidate_quantity']:.2f} unidades referenciales"
        next_label = "Validar traslado"
        next_description = "Confirmar disponibilidad fisica y aprobar traslado interno antes de crear solicitud SAP."
    elif recommendation_type == "acelerar_compra_abierta":
        main_message = "Acelerar OC abierta"
        next_label = "Contactar proveedor"
        next_description = "Validar fecha de recepcion de la OC abierta y priorizar entrega."
    elif recommendation_type == "revisar_venta_comprometida":
        main_message = "Revisar venta comprometida"
        next_label = "Revisar OV"
        next_description = "Validar compromisos de venta frente al stock disponible y fechas de entrega."
    elif recommendation_type == "validar_datos":
        main_message = "Validar datos antes de recomendar"
        next_label = "Validar datos"
        next_description = "Revisar consumo, stock y partidas abiertas antes de tomar accion."
    elif recommendation_type == "revisar_maestro_articulo":
        main_message = "Revisar maestro de articulo"
        next_label = "Revisar maestro"
        next_description = "Validar si el articulo sigue vigente, inventariable y correctamente asignado a almacenes."
    elif recommendation_type == "monitorear":
        main_message = "Monitorear cobertura"
        next_label = "Monitorear"
        next_description = "Revisar evolucion de consumo y stock en el siguiente ciclo operativo."
    elif recommendation_type == "no_comprar":
        main_message = "No comprar por ahora"
        next_label = "Sin accion"
        next_description = "Mantener observacion; la cobertura proyectada no muestra riesgo aparente."
    else:
        main_message = "Sin recomendacion accionable"
        next_label = "Revisar caso"
        next_description = "No hay suficiente informacion para sugerir una accion clara."

    technical_reason = (
        f"Riesgo {diagnostic.get('nivel_riesgo')}, cobertura proyectada "
        f"{diagnostic.get('cobertura_dias_stock_proyectado')} dias y deficit 30/60/90 de "
        f"{diagnostic.get('deficit_30_dias')}/{diagnostic.get('deficit_60_dias')}/{diagnostic.get('deficit_90_dias')}."
    )
    business_reason = "El diagnostico combina consumo historico, stock actual y partidas abiertas para priorizar la accion operativa."

    return {
        **diagnostic,
        **enrichment,
        **lead_time,
        **suggested,
        "suggested_quantity": actionable_quantity if recommendation_type == "comprar" else suggested["suggested_quantity"],
        "recommendation_type": recommendation_type,
        "recommendation_status": status,
        "priority_level": priority_level,
        "priority_score": priority_score,
        "priority_reasons": priority_reasons,
        "requires_human_approval": True,
        "recommendation_confidence": diagnostic.get("nivel_confianza"),
        "recommendation_warning": " | ".join(warnings),
        "main_message": main_message,
        "recommendation_detail": main_message,
        "business_reason": business_reason,
        "technical_reason": technical_reason,
        "data_quality_notes": list(dict.fromkeys(note for note in data_quality_notes if note)),
        "next_action_label": next_label,
        "next_action_description": next_description,
        "source_warehouse": transfer_candidate.get("source_warehouse") if transfer_candidate else None,
        "target_warehouse": transfer_candidate.get("target_warehouse") if transfer_candidate else None,
        "transfer_candidate_quantity": transfer_candidate.get("transfer_candidate_quantity") if transfer_candidate else 0.0,
        "source_projected_stock_before_transfer": transfer_candidate.get("source_projected_stock_before_transfer") if transfer_candidate else None,
        "target_projected_stock_before_transfer": transfer_candidate.get("target_projected_stock_before_transfer") if transfer_candidate else None,
        "source_remaining_stock_after_transfer": transfer_candidate.get("source_remaining_stock_after_transfer") if transfer_candidate else None,
        "target_projected_stock_after_transfer": transfer_candidate.get("target_projected_stock_after_transfer") if transfer_candidate else None,
        "transfer_reason": transfer_candidate.get("transfer_reason") if transfer_candidate else None,
    }


def _build_recommendations_from_diagnostics(
    diagnostics: list[dict[str, Any]],
    reconciliation: dict[str, Any] | None = None,
    include_enrichment: bool = False,
) -> list[dict[str, Any]]:
    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for diagnostic in diagnostics:
        by_item[str(diagnostic.get("item_code"))].append(diagnostic)
    reconciliation = reconciliation or get_coverage_reconciliation(limit=250000)
    enrichment_cache: dict[str, dict[str, Any]] = {}
    recommendations = []
    for diagnostic in diagnostics:
        item_code = str(diagnostic.get("item_code"))
        if include_enrichment and item_code not in enrichment_cache:
            enrichment_cache[item_code] = get_purchase_enrichment_for_item(item_code)
        recommendations.append(build_recommendation_record(diagnostic, by_item[item_code], enrichment_cache.get(item_code, DEFAULT_ENRICHMENT.copy()), reconciliation))
    return recommendations


def get_recommendation_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    recommendation_type: str | None = None,
    recommendation_status: str | None = None,
    priority_level: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    only_purchase_suggestions: bool = False,
    only_transfer_suggestions: bool = False,
    only_data_validation: bool = False,
    min_priority_score: float | None = None,
    max_priority_score: float | None = None,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    diagnostics = get_coverage_risk_items(item_code=item_code, warehouse=warehouse, risk_level=risk_level, confidence_level=confidence_level, limit=limit)
    reconciliation = get_coverage_reconciliation(item_code=item_code, warehouse=warehouse, limit=250000)
    recommendations = _build_recommendations_from_diagnostics(diagnostics, reconciliation)
    filtered = []
    for recommendation in recommendations:
        if recommendation_type and recommendation["recommendation_type"] != recommendation_type:
            continue
        if recommendation_status and recommendation["recommendation_status"] != recommendation_status:
            continue
        if priority_level and recommendation["priority_level"] != priority_level:
            continue
        if only_actionable and recommendation["recommendation_status"] not in {"accion_recomendada", "requiere_validacion"}:
            continue
        if only_purchase_suggestions and recommendation["recommendation_type"] != "comprar":
            continue
        if only_transfer_suggestions and recommendation["recommendation_type"] != "trasladar_stock":
            continue
        if only_data_validation and recommendation["recommendation_type"] != "validar_datos":
            continue
        if min_priority_score is not None and recommendation["priority_score"] < min_priority_score:
            continue
        if max_priority_score is not None and recommendation["priority_score"] > max_priority_score:
            continue
        filtered.append(recommendation)
    sorted_rows = sorted(filtered, key=lambda item: item["priority_score"], reverse=True)
    return sorted_rows if limit is None else sorted_rows[:limit]


def paginate_rows(rows: list[dict[str, Any]], limit: int = 50, offset: int = 0) -> dict[str, Any]:
    safe_limit = max(1, limit)
    safe_offset = max(0, offset)
    page = rows[safe_offset : safe_offset + safe_limit]
    has_next = len(rows) > safe_offset + safe_limit
    return {
        "items": page,
        "total": len(rows),
        "limit": safe_limit,
        "offset": safe_offset,
        "has_next": has_next,
        "has_previous": safe_offset > 0,
    }


def get_recommendation_items_page(
    item_code: str | None = None,
    warehouse: str | None = None,
    recommendation_type: str | None = None,
    recommendation_status: str | None = None,
    priority_level: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    only_purchase_suggestions: bool = False,
    only_transfer_suggestions: bool = False,
    only_data_validation: bool = False,
    min_priority_score: float | None = None,
    max_priority_score: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    rows = get_recommendation_items(
        item_code=item_code,
        warehouse=warehouse,
        recommendation_type=recommendation_type,
        recommendation_status=recommendation_status,
        priority_level=priority_level,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_purchase_suggestions=only_purchase_suggestions,
        only_transfer_suggestions=only_transfer_suggestions,
        only_data_validation=only_data_validation,
        min_priority_score=min_priority_score,
        max_priority_score=max_priority_score,
        limit=250000,
    )
    return paginate_rows(rows, limit=limit, offset=offset)


def get_recommendation_actions_page(
    item_code: str | None = None,
    warehouse: str | None = None,
    recommendation_type: str | None = None,
    recommendation_status: str | None = None,
    priority_level: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    only_actionable: bool = False,
    only_purchase_suggestions: bool = False,
    only_transfer_suggestions: bool = False,
    only_data_validation: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    recommendations = get_recommendation_items(
        item_code=item_code,
        warehouse=warehouse,
        recommendation_type=recommendation_type,
        recommendation_status=recommendation_status,
        priority_level=priority_level,
        risk_level=risk_level,
        confidence_level=confidence_level,
        only_actionable=only_actionable,
        only_purchase_suggestions=only_purchase_suggestions,
        only_transfer_suggestions=only_transfer_suggestions,
        only_data_validation=only_data_validation,
        limit=250000,
    )
    page = paginate_rows(recommendations, limit=limit, offset=offset)
    action_rows = page["items"]
    page["items"] = {
        "compras_sugeridas": [row for row in action_rows if row["recommendation_type"] == "comprar"],
        "traslados_sugeridos": [row for row in action_rows if row["recommendation_type"] == "trasladar_stock"],
        "oc_abiertas_a_acelerar": [row for row in action_rows if row["recommendation_type"] == "acelerar_compra_abierta"],
        "ov_a_revisar": [row for row in action_rows if row["recommendation_type"] == "revisar_venta_comprometida"],
        "articulos_para_validar_datos": [row for row in action_rows if row["recommendation_type"] == "validar_datos"],
        "articulos_para_revisar_maestro": [row for row in action_rows if row["recommendation_type"] == "revisar_maestro_articulo"],
    }
    return page


def summarize_recommendations(recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = Counter(row["recommendation_type"] for row in recommendations)
    by_priority = Counter(row["priority_level"] for row in recommendations)
    by_status = Counter(row["recommendation_status"] for row in recommendations)
    by_confidence = Counter(row["recommendation_confidence"] for row in recommendations)
    return {
        "total_recomendaciones_evaluadas": len(recommendations),
        "total_accion_recomendada": by_status.get("accion_recomendada", 0),
        "total_requiere_validacion": by_status.get("requiere_validacion", 0),
        "total_solo_monitoreo": by_status.get("solo_monitoreo", 0),
        "total_sin_accion": by_status.get("no_accion", 0),
        "total_datos_insuficientes": by_status.get("datos_insuficientes", 0),
        "cantidad_por_tipo": dict(by_type),
        "cantidad_por_prioridad": dict(by_priority),
        "cantidad_por_confianza": dict(by_confidence),
        "compras_sugeridas": by_type.get("comprar", 0),
        "traslados_sugeridos": by_type.get("trasladar_stock", 0),
        "validaciones_datos_sugeridas": by_type.get("validar_datos", 0),
        "revisiones_maestro_sugeridas": by_type.get("revisar_maestro_articulo", 0),
    }


def get_recommendations_summary(limit: int | None = 250000) -> dict[str, Any]:
    return summarize_recommendations(get_recommendation_items(limit=limit))


def get_recommendation_item_detail(item_code: str) -> dict[str, Any]:
    diagnostics = get_coverage_risk_items(item_code=item_code, limit=10000)
    recommendations = _build_recommendations_from_diagnostics(
        diagnostics,
        get_coverage_reconciliation(item_code=item_code, limit=250000),
        include_enrichment=True,
    )
    coverage_detail = get_coverage_risk_item_detail(item_code)
    stock_detail = get_stock_item_detail(item_code)
    open_documents = get_open_documents(item_code=item_code, limit=100000)
    monthly = get_monthly_consumption(item_code=item_code, limit=100000)
    enrichment = get_purchase_enrichment_for_item(item_code)
    return {
        "item_code": item_code,
        "item_name": stock_detail.get("item_name"),
        "recommendations_by_warehouse": recommendations,
        "coverage_diagnosis": coverage_detail,
        "stock_by_warehouse": stock_detail.get("stock_by_warehouse", []),
        "monthly_consumption": monthly,
        "open_documents": open_documents,
        "purchase_enrichment": enrichment,
        "summary": summarize_recommendations(recommendations),
    }


def get_recommendation_warehouses(limit: int | None = 250000) -> list[dict[str, Any]]:
    recommendations = get_recommendation_items(limit=limit)
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "warehouse_code": None,
            "warehouse_name": None,
            "recomendaciones_urgentes": 0,
            "recomendaciones_altas": 0,
            "compras_sugeridas": 0,
            "traslados_sugeridos": 0,
            "validaciones_datos": 0,
            "articulos_sin_accion": 0,
        }
    )
    for row in recommendations:
        key = str(row.get("warehouse_code"))
        item = grouped[key]
        item["warehouse_code"] = row.get("warehouse_code")
        item["warehouse_name"] = row.get("warehouse_name")
        if row["priority_level"] == "urgente":
            item["recomendaciones_urgentes"] += 1
        if row["priority_level"] == "alta":
            item["recomendaciones_altas"] += 1
        if row["recommendation_type"] == "comprar":
            item["compras_sugeridas"] += 1
        if row["recommendation_type"] == "trasladar_stock":
            item["traslados_sugeridos"] += 1
        if row["recommendation_type"] == "validar_datos":
            item["validaciones_datos"] += 1
        if row["recommendation_status"] == "no_accion":
            item["articulos_sin_accion"] += 1
    return sorted(grouped.values(), key=lambda item: str(item["warehouse_code"]))


def get_recommendation_actions(limit: int | None = 250000) -> dict[str, Any]:
    recommendations = get_recommendation_items(limit=limit)
    return {
        "compras_sugeridas": [row for row in recommendations if row["recommendation_type"] == "comprar"],
        "traslados_sugeridos": [row for row in recommendations if row["recommendation_type"] == "trasladar_stock"],
        "oc_abiertas_a_acelerar": [row for row in recommendations if row["recommendation_type"] == "acelerar_compra_abierta"],
        "ov_a_revisar": [row for row in recommendations if row["recommendation_type"] == "revisar_venta_comprometida"],
        "articulos_para_validar_datos": [row for row in recommendations if row["recommendation_type"] == "validar_datos"],
        "articulos_para_revisar_maestro": [row for row in recommendations if row["recommendation_type"] == "revisar_maestro_articulo"],
    }


def get_purchase_candidates(limit: int | None = 1000) -> list[dict[str, Any]]:
    return get_recommendation_items(only_purchase_suggestions=True, limit=limit)


def get_transfer_candidates(limit: int | None = 1000) -> list[dict[str, Any]]:
    return get_recommendation_items(only_transfer_suggestions=True, limit=limit)
