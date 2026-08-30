from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from math import ceil
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.eda_service import build_analytics
from app.services.forecast_service import ForecastResult, build_forecast
from app.services.inventory_service import get_current_inventory
from app.services.stock_status_service import (
    calculate_coverage_days,
    classify_stock_status,
)


@dataclass(frozen=True)
class ReplenishmentResult:
    inventory: pd.DataFrame
    suggestions: pd.DataFrame
    summary: dict[str, Any]
    forecast: ForecastResult | None


def load_replenishment_artifacts() -> ReplenishmentResult | None:
    export_dir = Path(__file__).resolve().parents[2] / "exports"
    paths = {
        "inventory": export_dir / "current_inventory_snapshot.csv",
        "suggestions": export_dir / "replenishment_suggestions.csv",
        "summary": export_dir / "replenishment_summary.csv",
    }
    if not all(path.exists() for path in paths.values()):
        return None
    return ReplenishmentResult(
        inventory=pd.read_csv(
            paths["inventory"],
            dtype={"item_code": str, "warehouse_code": str},
            low_memory=False,
        ),
        suggestions=pd.read_csv(
            paths["suggestions"],
            dtype={"item_code": str, "warehouse_code": str},
            low_memory=False,
        ),
        summary=pd.read_csv(paths["summary"]).iloc[0].to_dict(),
        forecast=_artifact_forecast(3),
    )


def calculate_safety_stock(
    projected_demand: float,
    confidence: str,
    abc_class: str,
    intermittent: bool,
) -> tuple[float, float]:
    if projected_demand <= 0 or confidence == "NOT_RECOMMENDED":
        return 0.0, 0.0
    if intermittent:
        factor = 0.40
    elif confidence == "LOW":
        factor = 0.35
    elif confidence == "MEDIUM":
        factor = 0.20
    elif confidence == "HIGH":
        factor = 0.15
    else:
        factor = 0.0
    factor += {"A": 0.10, "B": 0.05, "C": 0.0}.get(abc_class, 0.0)
    factor = round(factor, 4)
    return max(0.0, projected_demand * factor), factor


def calculate_suggested_purchase(
    projected_demand: float,
    safety_stock: float,
    available_stock: float,
    on_order_stock: float,
) -> tuple[float, int]:
    raw = (
        projected_demand
        + safety_stock
        - available_stock
        - on_order_stock
    )
    return raw, max(0, ceil(raw))


def classify_recommendation(
    *,
    suggested_purchase: int,
    confidence: str,
    stock_status: str,
    forecast_recommended: bool,
) -> str:
    if not forecast_recommended or stock_status == "NOT_RECOMMENDED":
        return "EXCLUDED"
    if suggested_purchase > 0 and confidence in {"HIGH", "MEDIUM"}:
        return "PURCHASE_SUGGESTED"
    if suggested_purchase > 0 and confidence == "LOW":
        return "REFERENTIAL_PURCHASE"
    if stock_status in {"OVERSTOCK", "NO_DEMAND"}:
        return "NO_PURCHASE"
    if stock_status in {"NO_STOCK_WITH_DEMAND", "CRITICAL"}:
        return "MANUAL_REVIEW"
    return "MONITOR"


def recommendation_reason(
    stock_status: str,
    recommendation_type: str,
) -> str:
    if stock_status == "NOT_RECOMMENDED":
        return "Artículo excluido o forecast no apto para una recomendación automática."
    if stock_status == "NO_STOCK_WITH_DEMAND":
        return "Producto crítico: stock disponible cero con demanda proyectada positiva."
    if recommendation_type == "REFERENTIAL_PURCHASE":
        return "Forecast de confianza baja; revisar manualmente antes de comprar."
    if recommendation_type == "PURCHASE_SUGGESTED":
        return "Stock disponible no cubre la demanda proyectada y el stock de seguridad."
    if stock_status == "OVERSTOCK":
        return "Cobertura mayor a 180 días; posible sobrestock."
    if stock_status == "NO_DEMAND":
        return "Producto sin demanda proyectada; no se recomienda compra."
    if stock_status == "CRITICAL":
        return "Cobertura menor a 30 días con demanda proyectada positiva."
    if stock_status == "REVIEW":
        return "Cobertura entre 30 y 60 días; monitorear y revisar reposición."
    return "Cobertura operativa sin necesidad inmediata de compra."


def calculate_priority_score(
    *,
    stock_status: str,
    abc_class: str,
    confidence: str,
    coverage_days: float | None,
    suggested_purchase: int,
    projected_demand: float,
    requires_review: bool,
) -> tuple[int, str]:
    score = 0
    if stock_status in {"CRITICAL", "NO_STOCK_WITH_DEMAND"}:
        score += 40
    score += {"A": 25, "B": 15}.get(abc_class, 0)
    score += {"HIGH": 25, "MEDIUM": 20, "LOW": 5}.get(confidence, 0)
    if coverage_days is not None and coverage_days < 30:
        score += 20
    if suggested_purchase >= max(10, ceil(max(projected_demand, 0))):
        score += 10
    if requires_review:
        score -= 30
    score = max(0, min(100, score))
    level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return score, level


def _artifact_forecast(horizon: int) -> ForecastResult | None:
    if horizon != 3:
        return None
    export_dir = Path(__file__).resolve().parents[2] / "exports"
    paths = {
        "candidates": export_dir / "forecast_candidates.csv",
        "excluded": export_dir / "forecast_excluded_items.csv",
        "comparison": export_dir / "forecast_model_comparison.csv",
        "best": export_dir / "forecast_best_model_by_item.csv",
        "future": export_dir / "forecast_future_results.csv",
        "summary": export_dir / "forecast_summary.csv",
    }
    if not all(path.exists() for path in paths.values()):
        return None
    summary = pd.read_csv(paths["summary"]).iloc[0].to_dict()
    return ForecastResult(
        candidates=pd.read_csv(paths["candidates"], dtype={"item_code": str}),
        excluded=pd.read_csv(paths["excluded"], dtype={"item_code": str}),
        dataset=pd.DataFrame(),
        comparison=pd.read_csv(paths["comparison"], dtype={"item_code": str}),
        best_models=pd.read_csv(paths["best"], dtype={"item_code": str}),
        future=pd.read_csv(paths["future"], dtype={"item_code": str}),
        summary=summary,
    )


def _forecast_result(
    date_from: date | None,
    date_to: date | None,
    item_group: str | None,
    warehouse_code: str | None,
    horizon: int,
) -> ForecastResult:
    if (
        date_from is None
        and date_to is None
        and item_group is None
        and warehouse_code is None
    ):
        artifact = _artifact_forecast(horizon)
        if artifact is not None:
            return artifact
    return build_forecast(
        date_from,
        date_to,
        item_group,
        warehouse_code,
        6,
        horizon,
    )


@lru_cache(maxsize=8)
def build_replenishment(
    date_from: date | None = None,
    date_to: date | None = None,
    item_group: str | None = None,
    warehouse_code: str | None = None,
    horizon_months: int = 3,
    include_low_confidence: bool = True,
) -> ReplenishmentResult:
    if horizon_months not in {3, 6}:
        raise ValueError("horizon_months debe ser 3 o 6.")
    analytics = build_analytics(
        date_from=date_from,
        date_to=date_to,
        item_group=item_group,
        warehouse_code=warehouse_code,
    )
    forecast = _forecast_result(
        date_from,
        date_to,
        item_group,
        warehouse_code,
        horizon_months,
    )
    inventory = get_current_inventory(
        warehouse_code=warehouse_code,
        item_group=item_group,
        aggregate=True,
    )

    metadata = analytics.combined.copy()
    metadata["item_code"] = metadata["item_code"].astype(str)
    stock = inventory.copy()
    stock["item_code"] = stock["item_code"].astype(str)
    result = metadata.merge(
        stock[
            [
                "item_code",
                "warehouse_code",
                "warehouse_name",
                "physical_stock",
                "committed_stock",
                "on_order_stock",
                "available_stock",
                "projected_stock",
            ]
        ],
        on="item_code",
        how="left",
    )
    stock_columns = [
        "physical_stock",
        "committed_stock",
        "on_order_stock",
        "available_stock",
        "projected_stock",
    ]
    result[stock_columns] = result[stock_columns].fillna(0.0)
    result["warehouse_code"] = result["warehouse_code"].fillna(
        warehouse_code or "ALL"
    )
    result["warehouse_name"] = result["warehouse_name"].fillna(
        warehouse_code or "Todos los almacenes"
    )

    future = forecast.future.copy()
    future["item_code"] = future["item_code"].astype(str)
    projected = (
        future.groupby("item_code", as_index=False)
        .agg(
            projected_demand_horizon=("forecast_quantity", "sum"),
            forecast_lower_total=("lower_bound", "sum"),
            forecast_upper_total=("upper_bound", "sum"),
            forecast_confidence=("forecast_confidence", "first"),
            model_used=("model_used", "first"),
        )
    )
    result = result.merge(projected, on="item_code", how="left")
    result["projected_demand_horizon"] = result[
        "projected_demand_horizon"
    ].fillna(0.0)
    result["forecast_lower_total"] = result["forecast_lower_total"].fillna(0.0)
    result["forecast_upper_total"] = result["forecast_upper_total"].fillna(0.0)
    result["forecast_confidence"] = result["forecast_confidence"].fillna(
        "NOT_RECOMMENDED"
    )
    result["model_used"] = result["model_used"].fillna("NONE")
    result["forecast_recommended"] = result["recommended_for_forecast"].astype(
        bool
    )
    if not include_low_confidence:
        result.loc[
            result["forecast_confidence"] == "LOW", "forecast_recommended"
        ] = False

    result["average_monthly_projected_demand"] = (
        result["projected_demand_horizon"] / horizon_months
    )
    result["average_daily_projected_demand"] = (
        result["average_monthly_projected_demand"] / 30
    )
    result["coverage_days"] = result.apply(
        lambda row: calculate_coverage_days(
            float(row["available_stock"]),
            float(row["average_daily_projected_demand"]),
        ),
        axis=1,
    )

    safety = result.apply(
        lambda row: calculate_safety_stock(
            float(row["projected_demand_horizon"]),
            str(row["forecast_confidence"]),
            str(row["abc_quantity_class"]),
            bool(row["is_intermittent"]),
        ),
        axis=1,
    )
    result["safety_stock"] = [value[0] for value in safety]
    result["safety_stock_factor"] = [value[1] for value in safety]

    purchase = result.apply(
        lambda row: calculate_suggested_purchase(
            float(row["projected_demand_horizon"]),
            float(row["safety_stock"]),
            float(row["available_stock"]),
            float(row["on_order_stock"]),
        ),
        axis=1,
    )
    result["suggested_purchase_raw"] = [value[0] for value in purchase]
    result["suggested_purchase_quantity"] = [value[1] for value in purchase]
    result.loc[
        ~result["forecast_recommended"],
        "suggested_purchase_quantity",
    ] = 0

    result["stock_status"] = result.apply(
        lambda row: classify_stock_status(
            coverage_days=(
                None if pd.isna(row["coverage_days"]) else row["coverage_days"]
            ),
            forecast_quantity=float(row["projected_demand_horizon"]),
            available_stock=float(row["available_stock"]),
            forecast_recommended=bool(row["forecast_recommended"]),
        ),
        axis=1,
    )
    result["recommendation_type"] = result.apply(
        lambda row: classify_recommendation(
            suggested_purchase=int(row["suggested_purchase_quantity"]),
            confidence=str(row["forecast_confidence"]),
            stock_status=str(row["stock_status"]),
            forecast_recommended=bool(row["forecast_recommended"]),
        ),
        axis=1,
    )
    result["recommendation_reason"] = result.apply(
        lambda row: recommendation_reason(
            str(row["stock_status"]),
            str(row["recommendation_type"]),
        ),
        axis=1,
    )
    result["requires_manual_review"] = result["forecast_recommended"] & (
        result["recommendation_type"].isin(
            ["REFERENTIAL_PURCHASE", "MANUAL_REVIEW"]
        )
        | result["has_amount_anomaly"].astype(bool)
        | result["xyz_class"].isin(["Z", "INTERMITTENT", "REVIEW_REQUIRED"])
    )
    priority = result.apply(
        lambda row: calculate_priority_score(
            stock_status=str(row["stock_status"]),
            abc_class=str(row["abc_quantity_class"]),
            confidence=str(row["forecast_confidence"]),
            coverage_days=(
                None if pd.isna(row["coverage_days"]) else row["coverage_days"]
            ),
            suggested_purchase=int(row["suggested_purchase_quantity"]),
            projected_demand=float(row["projected_demand_horizon"]),
            requires_review=bool(row["requires_manual_review"]),
        ),
        axis=1,
    )
    result["priority_score"] = [value[0] for value in priority]
    result["priority_level"] = [value[1] for value in priority]

    result = result.rename(
        columns={
            "abc_quantity_class": "abc_class_quantity",
            "abc_amount_class": "abc_class_amount",
        }
    )
    result = result.sort_values(
        ["priority_score", "suggested_purchase_quantity", "item_code"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    summary = _build_summary(result, inventory, horizon_months)
    return ReplenishmentResult(inventory, result, summary, forecast)


def _build_summary(
    frame: pd.DataFrame,
    inventory: pd.DataFrame,
    horizon_months: int,
) -> dict[str, Any]:
    def count(column: str, value: str) -> int:
        return int((frame[column] == value).sum())

    return {
        "total_items_evaluated": len(frame),
        "items_with_purchase": int(
            (frame["suggested_purchase_quantity"] > 0).sum()
        ),
        "active_purchase_suggestions": count(
            "recommendation_type", "PURCHASE_SUGGESTED"
        ),
        "referential_purchases": count(
            "recommendation_type", "REFERENTIAL_PURCHASE"
        ),
        "critical_items": int(
            frame["stock_status"].isin(
                ["CRITICAL", "NO_STOCK_WITH_DEMAND"]
            ).sum()
        ),
        "review_items": count("stock_status", "REVIEW"),
        "healthy_items": count("stock_status", "HEALTHY"),
        "overstock_items": count("stock_status", "OVERSTOCK"),
        "no_demand_items": count("stock_status", "NO_DEMAND"),
        "not_recommended_items": count("stock_status", "NOT_RECOMMENDED"),
        "total_suggested_quantity": int(
            frame["suggested_purchase_quantity"].sum()
        ),
        "medium_confidence_items": count("forecast_confidence", "MEDIUM"),
        "low_confidence_items": count("forecast_confidence", "LOW"),
        "high_confidence_items": count("forecast_confidence", "HIGH"),
        "manual_review_items": int(frame["requires_manual_review"].sum()),
        "high_priority_items": count("priority_level", "HIGH"),
        "medium_priority_items": count("priority_level", "MEDIUM"),
        "low_priority_items": count("priority_level", "LOW"),
        "horizon_months": horizon_months,
        "inventory_items": int(inventory["item_code"].nunique()),
        "warehouses_detected": int(
            get_current_inventory()["warehouse_code"].nunique()
        ),
        "physical_stock_total": float(inventory["physical_stock"].sum()),
        "committed_stock_total": float(inventory["committed_stock"].sum()),
        "on_order_stock_total": float(inventory["on_order_stock"].sum()),
        "available_stock_total": float(inventory["available_stock"].sum()),
    }


def filter_replenishment(
    frame: pd.DataFrame,
    *,
    item_code: str | None = None,
    confidence: str | None = None,
    stock_status: str | None = None,
    recommendation_type: str | None = None,
    priority_level: str | None = None,
    only_purchase_suggested: bool = False,
) -> pd.DataFrame:
    result = frame
    filters = {
        "item_code": item_code,
        "forecast_confidence": confidence,
        "stock_status": stock_status,
        "recommendation_type": recommendation_type,
        "priority_level": priority_level,
    }
    for column, value in filters.items():
        if value:
            result = result[result[column] == value]
    if only_purchase_suggested:
        result = result[result["suggested_purchase_quantity"] > 0]
    return result.reset_index(drop=True)
