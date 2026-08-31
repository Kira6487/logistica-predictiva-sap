from __future__ import annotations

from collections import Counter, defaultdict
from math import sqrt
from statistics import median
from typing import Any

from app.services.consumption_history_service import get_monthly_consumption
from app.services.inventory_position_service import build_inventory_position_record
from app.services.open_documents_service import aggregate_open_documents_by_item_warehouse, get_open_documents
from app.services.stock_position_service import get_stock_item_detail, get_stock_items


MIN_MONTHS_FOR_3M = 3
MIN_MONTHS_FOR_6M = 3
MIN_MONTHS_FOR_12M = 6
INTERMITTENT_RATIO_THRESHOLD = 0.35
VARIABLE_CV_THRESHOLD = 0.8
LOW_COVERAGE_DAYS = 15
MEDIUM_COVERAGE_DAYS = 45
HIGH_COVERAGE_DAYS = 90
DAYS_PER_MONTH = 30


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    average = _avg(values)
    return sqrt(sum((value - average) ** 2 for value in values) / len(values))


def _period_sort_key(period: str) -> tuple[int, int]:
    return int(period[:4]), int(period[5:7])


def group_monthly_consumption(monthly_records: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in monthly_records:
        item_code = record.get("item_code")
        warehouse = record.get("warehouse")
        if item_code is None or warehouse is None:
            continue
        grouped[(str(item_code), str(warehouse))].append(record)
    for records in grouped.values():
        records.sort(key=lambda item: _period_sort_key(str(item["period"])))
    return grouped


def calculate_consumption_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "consumo_total_historico": 0.0,
            "periodos_historicos_detectados": 0,
            "meses_con_consumo": 0,
            "meses_sin_consumo": 0,
            "fecha_ultimo_consumo": None,
            "consumo_promedio_mensual_3m": 0.0,
            "consumo_promedio_mensual_6m": 0.0,
            "consumo_promedio_mensual_12m": 0.0,
            "consumo_promedio_mensual_general": 0.0,
            "consumo_mediano_mensual": 0.0,
            "consumo_maximo_mensual": 0.0,
            "consumo_minimo_mensual": 0.0,
            "desviacion_consumo_mensual": 0.0,
            "coeficiente_variacion": 0.0,
            "ratio_meses_con_consumo": 0.0,
        }

    sorted_records = sorted(records, key=lambda item: _period_sort_key(str(item["period"])))
    quantities = [_to_float(record.get("consumed_quantity")) for record in sorted_records]
    positive_quantities = [quantity for quantity in quantities if quantity > 0]
    total_periods = len(sorted_records)
    months_with_consumption = len(positive_quantities)
    total = sum(positive_quantities)
    general_average = _avg(positive_quantities)
    deviation = _stddev(positive_quantities)
    return {
        "consumo_total_historico": total,
        "periodos_historicos_detectados": total_periods,
        "meses_con_consumo": months_with_consumption,
        "meses_sin_consumo": max(0, total_periods - months_with_consumption),
        "fecha_ultimo_consumo": max((record.get("last_date") for record in sorted_records if record.get("last_date")), default=None),
        "consumo_promedio_mensual_3m": _avg(quantities[-3:]),
        "consumo_promedio_mensual_6m": _avg(quantities[-6:]),
        "consumo_promedio_mensual_12m": _avg(quantities[-12:]),
        "consumo_promedio_mensual_general": general_average,
        "consumo_mediano_mensual": float(median(positive_quantities)) if positive_quantities else 0.0,
        "consumo_maximo_mensual": max(positive_quantities, default=0.0),
        "consumo_minimo_mensual": min(positive_quantities, default=0.0),
        "desviacion_consumo_mensual": deviation,
        "coeficiente_variacion": deviation / general_average if general_average > 0 else 0.0,
        "ratio_meses_con_consumo": months_with_consumption / total_periods if total_periods else 0.0,
    }


def classify_demand(metrics: dict[str, Any]) -> str:
    months_with_consumption = int(metrics["meses_con_consumo"])
    if months_with_consumption == 0:
        return "sin_consumo"
    if months_with_consumption < 3:
        return "demanda_insuficiente"
    if float(metrics["ratio_meses_con_consumo"]) <= INTERMITTENT_RATIO_THRESHOLD:
        return "demanda_intermitente"
    if float(metrics["coeficiente_variacion"]) >= VARIABLE_CV_THRESHOLD:
        return "demanda_variable"
    return "demanda_estable"


def select_base_consumption(metrics: dict[str, Any], demand_type: str) -> tuple[float, str, list[str]]:
    reasons: list[str] = []
    months_with_consumption = int(metrics["meses_con_consumo"])
    periods = int(metrics["periodos_historicos_detectados"])
    if months_with_consumption == 0:
        return 0.0, "sin_consumo", ["Sin consumo historico"]
    if periods >= 12 and months_with_consumption >= MIN_MONTHS_FOR_12M and metrics["consumo_promedio_mensual_12m"] > 0:
        return float(metrics["consumo_promedio_mensual_12m"]), "promedio_12m", reasons
    if periods >= 6 and months_with_consumption >= MIN_MONTHS_FOR_6M and metrics["consumo_promedio_mensual_6m"] > 0:
        return float(metrics["consumo_promedio_mensual_6m"]), "promedio_6m", reasons
    if periods >= 3 and months_with_consumption >= MIN_MONTHS_FOR_3M and metrics["consumo_promedio_mensual_3m"] > 0:
        return float(metrics["consumo_promedio_mensual_3m"]), "promedio_3m", reasons
    if demand_type in {"demanda_intermitente", "demanda_insuficiente"}:
        reasons.append("Demanda intermitente" if demand_type == "demanda_intermitente" else "Menos de 3 meses con consumo")
        conservative = max(float(metrics["consumo_mediano_mensual"]), float(metrics["consumo_promedio_mensual_general"]))
        return conservative, "conservador_mediana_promedio", reasons
    return float(metrics["consumo_promedio_mensual_general"]), "promedio_general", reasons


def classify_confidence(metrics: dict[str, Any], demand_type: str) -> tuple[str, str]:
    periods = int(metrics["periodos_historicos_detectados"])
    months = int(metrics["meses_con_consumo"])
    ratio = float(metrics["ratio_meses_con_consumo"])
    coefficient = float(metrics["coeficiente_variacion"])
    if months == 0:
        return "sin_confianza", "Sin consumo historico"
    if months < 3:
        return "sin_confianza", "Menos de 3 meses con consumo"
    if periods >= 12 and months >= 6 and ratio > INTERMITTENT_RATIO_THRESHOLD and coefficient < VARIABLE_CV_THRESHOLD:
        return "alta", "Historial amplio con consumo suficiente"
    if periods >= 6 and months >= 3 and demand_type not in {"demanda_intermitente", "demanda_variable"}:
        return "media", "Historial medio con consumo suficiente"
    return "baja", "Demanda intermitente o variable"


def calculate_coverage(stock_projected: float, stock_available: float, monthly_consumption: float) -> dict[str, Any]:
    if monthly_consumption <= 0:
        return {
            "consumo_base_diario": 0.0,
            "cobertura_dias_stock_disponible": None,
            "cobertura_dias_stock_proyectado": None,
            "cobertura_meses_stock_disponible": None,
            "cobertura_meses_stock_proyectado": None,
        }
    daily = monthly_consumption / DAYS_PER_MONTH
    available_days = stock_available / daily if daily > 0 else None
    projected_days = stock_projected / daily if daily > 0 else None
    return {
        "consumo_base_diario": daily,
        "cobertura_dias_stock_disponible": available_days,
        "cobertura_dias_stock_proyectado": projected_days,
        "cobertura_meses_stock_disponible": available_days / DAYS_PER_MONTH if available_days is not None else None,
        "cobertura_meses_stock_proyectado": projected_days / DAYS_PER_MONTH if projected_days is not None else None,
    }


def calculate_deficits(stock_projected: float, daily_consumption: float) -> dict[str, float]:
    result: dict[str, float] = {}
    for days in (30, 60, 90):
        demand = daily_consumption * days
        result[f"deficit_{days}_dias"] = max(0.0, demand - stock_projected)
        result[f"sobrante_{days}_dias"] = max(0.0, stock_projected - demand)
    return result


def classify_risk(record: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    projected_days = record.get("cobertura_dias_stock_proyectado")
    has_consumption = record["consumo_base_mensual"] > 0
    if record["nivel_confianza"] == "sin_confianza" and not has_consumption:
        return "sin_diagnostico", ["Sin consumo historico"]
    if record["stock_disponible"] <= 0 and has_consumption:
        reasons.append("Stock disponible negativo o cero")
    if record["stock_proyectado_con_partidas"] <= 0 and has_consumption:
        reasons.append("Stock proyectado con partidas negativo o cero")
    if record["stock_comprometido_sap"] > record["stock_fisico"]:
        reasons.append("Comprometido SAP mayor al stock fisico")
    if reasons:
        return "critico", reasons
    if projected_days is None:
        return "sin_diagnostico", ["Cobertura no calculable"]
    if projected_days <= LOW_COVERAGE_DAYS:
        return "alto", ["Cobertura menor o igual a 15 dias"]
    if record["deficit_30_dias"] > 0:
        return "alto", ["Deficit a 30 dias"]
    if projected_days <= MEDIUM_COVERAGE_DAYS:
        return "medio", ["Cobertura entre 16 y 45 dias"]
    if record["deficit_60_dias"] > 0:
        return "medio", ["Deficit a 60 dias"]
    if projected_days <= HIGH_COVERAGE_DAYS:
        return "bajo", ["Cobertura entre 46 y 90 dias"]
    return "sin_riesgo_aparente", ["Cobertura mayor a 90 dias"]


def build_coverage_risk_record(
    inventory_record: dict[str, Any],
    monthly_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metrics = calculate_consumption_metrics(monthly_records or [])
    demand_type = classify_demand(metrics)
    monthly_base, base_source, base_reasons = select_base_consumption(metrics, demand_type)
    confidence, confidence_reason = classify_confidence(metrics, demand_type)
    coverage = calculate_coverage(
        float(inventory_record["stock_proyectado_con_partidas"]),
        float(inventory_record["stock_disponible"]),
        monthly_base,
    )
    deficits = calculate_deficits(float(inventory_record["stock_proyectado_con_partidas"]), coverage["consumo_base_diario"])
    record = {
        **inventory_record,
        **metrics,
        **coverage,
        **deficits,
        "consumo_base_mensual": monthly_base,
        "fuente_consumo_base": base_source,
        "tipo_demanda": demand_type,
        "nivel_confianza": confidence,
        "motivo_confianza": confidence_reason,
        "motivos_riesgo": base_reasons[:],
    }
    risk_level, risk_reasons = classify_risk(record)
    record["nivel_riesgo"] = risk_level
    record["motivos_riesgo"].extend(risk_reasons)
    if record["entradas_abiertas"] > 0:
        record["motivos_riesgo"].append("Tiene OC abiertas que reducen el riesgo")
    if record["salidas_abiertas"] > 0:
        record["motivos_riesgo"].append("Tiene OV abiertas que aumentan el riesgo")
    record["motivos_riesgo"] = list(dict.fromkeys(record["motivos_riesgo"]))
    return record


def _load_base_data(
    item_code: str | None = None,
    warehouse: str | None = None,
    limit: int | None = 1000,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    stock_records = get_stock_items(item_code=item_code, warehouse=warehouse, limit=limit)
    open_documents = get_open_documents(item_code=item_code, warehouse=warehouse, limit=100000)
    open_totals = aggregate_open_documents_by_item_warehouse(open_documents)
    monthly = get_monthly_consumption(item_code=item_code, warehouse=warehouse, limit=100000)
    consumption_by_key = group_monthly_consumption(monthly)

    inventory_records = [
        build_inventory_position_record(
            stock_record,
            open_totals.get((str(stock_record["item_code"]), str(stock_record["warehouse_code"]))),
        )
        for stock_record in stock_records
    ]

    stock_keys = {(str(record["item_code"]), str(record["warehouse_code"])) for record in inventory_records}
    for key, records in consumption_by_key.items():
        if key in stock_keys:
            continue
        item, whs = key
        inventory_records.append(
            {
                "item_code": item,
                "item_name": records[-1].get("item_description"),
                "warehouse_code": whs,
                "warehouse_name": None,
                "stock_fisico": 0.0,
                "stock_comprometido": 0.0,
                "stock_pedido": 0.0,
                "stock_disponible": 0.0,
                "stock_proyectado_base": 0.0,
                "sin_stock": True,
                "stock_negativo": False,
                "comprometido_mayor_stock": False,
                "tiene_stock": False,
                "tiene_pedido_abierto": False,
                "tiene_compromiso_abierto": False,
                "item_inventory": True,
                "item_active": True,
                "warehouse_locked": False,
                "warehouse_inactive": False,
                "stock_comprometido_sap": 0.0,
                "stock_pedido_sap": 0.0,
                "entradas_abiertas": open_totals.get(key, {}).get("entradas_abiertas", 0.0),
                "salidas_abiertas": open_totals.get(key, {}).get("salidas_abiertas", 0.0),
                "stock_proyectado_con_partidas": open_totals.get(key, {}).get("entradas_abiertas", 0.0)
                - open_totals.get(key, {}).get("salidas_abiertas", 0.0),
            }
        )
    return inventory_records, open_documents, consumption_by_key


def get_coverage_risk_items(
    item_code: str | None = None,
    warehouse: str | None = None,
    risk_level: str | None = None,
    confidence_level: str | None = None,
    demand_type: str | None = None,
    only_critical: bool = False,
    only_with_deficit: bool = False,
    only_without_diagnosis: bool = False,
    min_coverage_days: float | None = None,
    max_coverage_days: float | None = None,
    limit: int | None = 1000,
) -> list[dict[str, Any]]:
    inventory_records, _, consumption_by_key = _load_base_data(item_code=item_code, warehouse=warehouse, limit=limit)
    diagnostics = [
        build_coverage_risk_record(
            record,
            consumption_by_key.get((str(record["item_code"]), str(record["warehouse_code"]))),
        )
        for record in inventory_records
    ]
    filtered = []
    for diagnostic in diagnostics:
        coverage_days = diagnostic.get("cobertura_dias_stock_proyectado")
        if risk_level and diagnostic["nivel_riesgo"] != risk_level:
            continue
        if confidence_level and diagnostic["nivel_confianza"] != confidence_level:
            continue
        if demand_type and diagnostic["tipo_demanda"] != demand_type:
            continue
        if only_critical and diagnostic["nivel_riesgo"] != "critico":
            continue
        if only_with_deficit and not any(diagnostic[f"deficit_{days}_dias"] > 0 for days in (30, 60, 90)):
            continue
        if only_without_diagnosis and diagnostic["nivel_riesgo"] != "sin_diagnostico":
            continue
        if min_coverage_days is not None and (coverage_days is None or coverage_days < min_coverage_days):
            continue
        if max_coverage_days is not None and (coverage_days is None or coverage_days > max_coverage_days):
            continue
        filtered.append(diagnostic)
    return filtered[: limit or 1000]


def summarize_coverage_risk(items: list[dict[str, Any]], reconciliation: dict[str, Any]) -> dict[str, Any]:
    risk_counts = Counter(item["nivel_riesgo"] for item in items)
    confidence_counts = Counter(item["nivel_confianza"] for item in items)
    return {
        "total_articulos_evaluados": len({item["item_code"] for item in items if item.get("item_code")}),
        "total_combinaciones_evaluadas": len(items),
        "riesgo_critico": risk_counts.get("critico", 0),
        "riesgo_alto": risk_counts.get("alto", 0),
        "riesgo_medio": risk_counts.get("medio", 0),
        "riesgo_bajo": risk_counts.get("bajo", 0),
        "sin_diagnostico": risk_counts.get("sin_diagnostico", 0),
        "sin_riesgo_aparente": risk_counts.get("sin_riesgo_aparente", 0),
        "confianza_alta": confidence_counts.get("alta", 0),
        "confianza_media": confidence_counts.get("media", 0),
        "confianza_baja": confidence_counts.get("baja", 0),
        "sin_confianza": confidence_counts.get("sin_confianza", 0),
        "articulos_stock_disponible_negativo": sum(1 for item in items if item["stock_disponible"] < 0),
        "articulos_comprometido_mayor_stock": sum(1 for item in items if item["stock_comprometido_sap"] > item["stock_fisico"]),
        "articulos_deficit_30_dias": sum(1 for item in items if item["deficit_30_dias"] > 0),
        "articulos_deficit_60_dias": sum(1 for item in items if item["deficit_60_dias"] > 0),
        "articulos_deficit_90_dias": sum(1 for item in items if item["deficit_90_dias"] > 0),
        "almacenes_consumo_sin_stock_actual": len(reconciliation["almacenes_consumo_sin_stock_actual"]),
        "almacenes_stock_sin_consumo_historico": len(reconciliation["almacenes_stock_sin_consumo_historico"]),
    }


def get_coverage_risk_summary(limit: int | None = 250000) -> dict[str, Any]:
    items = get_coverage_risk_items(limit=limit)
    reconciliation = get_coverage_reconciliation(limit=limit)
    return summarize_coverage_risk(items, reconciliation)


def get_coverage_risk_item_detail(item_code: str) -> dict[str, Any]:
    diagnostics = get_coverage_risk_items(item_code=item_code, limit=10000)
    stock_detail = get_stock_item_detail(item_code)
    open_documents = get_open_documents(item_code=item_code, limit=100000)
    monthly = get_monthly_consumption(item_code=item_code, limit=100000)
    return {
        "item_code": item_code,
        "item_name": stock_detail.get("item_name"),
        "diagnostics_by_warehouse": diagnostics,
        "stock_by_warehouse": stock_detail.get("stock_by_warehouse", []),
        "monthly_consumption": monthly,
        "open_documents": open_documents,
        "summary": summarize_coverage_risk(diagnostics, get_coverage_reconciliation(item_code=item_code, limit=10000)),
    }


def get_coverage_risk_warehouses(limit: int | None = 250000) -> list[dict[str, Any]]:
    items = get_coverage_risk_items(limit=limit)
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "warehouse_code": None,
            "warehouse_name": None,
            "articulos_evaluados": 0,
            "criticos": 0,
            "altos": 0,
            "medios": 0,
            "bajos": 0,
            "sin_diagnostico": 0,
            "deficit_total_30_dias": 0.0,
            "deficit_total_60_dias": 0.0,
            "deficit_total_90_dias": 0.0,
            "articulos_sin_stock_con_consumo": 0,
        }
    )
    for item in items:
        whs = str(item.get("warehouse_code"))
        row = grouped[whs]
        row["warehouse_code"] = item.get("warehouse_code")
        row["warehouse_name"] = item.get("warehouse_name")
        row["articulos_evaluados"] += 1
        if item["nivel_riesgo"] == "critico":
            row["criticos"] += 1
        elif item["nivel_riesgo"] == "alto":
            row["altos"] += 1
        elif item["nivel_riesgo"] == "medio":
            row["medios"] += 1
        elif item["nivel_riesgo"] == "bajo":
            row["bajos"] += 1
        elif item["nivel_riesgo"] == "sin_diagnostico":
            row["sin_diagnostico"] += 1
        row["deficit_total_30_dias"] += item["deficit_30_dias"]
        row["deficit_total_60_dias"] += item["deficit_60_dias"]
        row["deficit_total_90_dias"] += item["deficit_90_dias"]
        if item["stock_fisico"] <= 0 and item["meses_con_consumo"] > 0:
            row["articulos_sin_stock_con_consumo"] += 1
    return sorted(grouped.values(), key=lambda row: str(row["warehouse_code"]))


def get_coverage_reconciliation(
    item_code: str | None = None,
    warehouse: str | None = None,
    limit: int | None = 250000,
) -> dict[str, Any]:
    stock_records = get_stock_items(item_code=item_code, warehouse=warehouse, limit=limit)
    monthly = get_monthly_consumption(item_code=item_code, warehouse=warehouse, limit=100000)
    documents = get_open_documents(item_code=item_code, warehouse=warehouse, limit=100000)
    stock_keys = {(str(row["item_code"]), str(row["warehouse_code"])) for row in stock_records}
    consumption_keys = {(str(row["item_code"]), str(row["warehouse"])) for row in monthly}
    document_keys = {(str(row["item_code"]), str(row["warehouse_code"])) for row in documents}
    stock_warehouses = {key[1] for key in stock_keys}
    consumption_warehouses = {key[1] for key in consumption_keys}
    stock_items = {key[0] for key in stock_keys}
    consumption_items = {key[0] for key in consumption_keys}
    document_items = {key[0] for key in document_keys}
    return {
        "almacenes_consumo_sin_stock_actual": sorted(consumption_warehouses - stock_warehouses),
        "almacenes_stock_sin_consumo_historico": sorted(stock_warehouses - consumption_warehouses),
        "articulos_consumo_sin_stock_actual": sorted(consumption_items - stock_items),
        "articulos_stock_sin_consumo_historico": sorted(stock_items - consumption_items),
        "articulos_partidas_abiertas_sin_consumo_historico": sorted(document_items - consumption_items),
        "articulos_partidas_abiertas_sin_stock_actual": sorted(document_items - stock_items),
        "total_combinaciones_consumo": len(consumption_keys),
        "total_combinaciones_stock": len(stock_keys),
        "total_combinaciones_partidas_abiertas": len(document_keys),
    }
