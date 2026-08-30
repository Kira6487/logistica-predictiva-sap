from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseConnectionError, read_rows
from app.services.demand_service import get_monthly_demand
from app.services.sap_queries import build_document_date_range_query
from app.services.schema_service import get_available_schema


AbcBasis = Literal["quantity", "amount"]


@dataclass(frozen=True)
class AnalyticsResult:
    date_from: date
    date_to: date
    metrics: pd.DataFrame
    abc_quantity: pd.DataFrame
    abc_amount: pd.DataFrame
    xyz: pd.DataFrame
    combined: pd.DataFrame
    summary: dict[str, Any]


def load_analytics_artifacts() -> AnalyticsResult | None:
    export_dir = Path(__file__).resolve().parents[2] / "exports"
    paths = {
        "metrics": export_dir / "eda_item_metrics.csv",
        "abc_quantity": export_dir / "abc_quantity_classification.csv",
        "abc_amount": export_dir / "abc_amount_classification.csv",
        "xyz": export_dir / "xyz_classification.csv",
        "combined": export_dir / "abc_xyz_classification.csv",
        "summary": export_dir / "analytics_summary.csv",
    }
    if not all(path.exists() for path in paths.values()):
        return None
    summary = pd.read_csv(paths["summary"]).iloc[0].to_dict()
    return AnalyticsResult(
        date_from=date.fromisoformat(str(summary["date_from"])),
        date_to=date.fromisoformat(str(summary["date_to"])),
        metrics=pd.read_csv(paths["metrics"], dtype={"item_code": str}),
        abc_quantity=pd.read_csv(
            paths["abc_quantity"], dtype={"item_code": str}
        ),
        abc_amount=pd.read_csv(paths["abc_amount"], dtype={"item_code": str}),
        xyz=pd.read_csv(paths["xyz"], dtype={"item_code": str}),
        combined=pd.read_csv(paths["combined"], dtype={"item_code": str}),
        summary=summary,
    )


def resolve_analysis_date_range(
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    if date_from is not None and date_to is not None:
        if date_from > date_to:
            raise ValueError("date_from no puede ser posterior a date_to.")
        return date_from, date_to

    try:
        row = read_rows(
            build_document_date_range_query(get_available_schema())
        )[0]
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "No se pudo resolver el rango de fechas para analytics."
        ) from exc

    if row["min_date"] is None or row["max_date"] is None:
        raise DatabaseConnectionError(
            "No existen documentos activos para ejecutar analytics."
        )

    min_date = _as_date(row["min_date"])
    max_date = _as_date(row["max_date"])
    resolved_from = date_from or min_date
    resolved_to = date_to or max_date
    if resolved_from > resolved_to:
        raise ValueError("date_from no puede ser posterior a date_to.")
    return resolved_from, resolved_to


def _as_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def assign_abc_classes(
    frame: pd.DataFrame,
    value_column: str,
    class_column: str,
) -> pd.DataFrame:
    result = frame.copy()
    result[class_column] = "UNCLASSIFIED"
    result[f"{value_column}_participation_pct"] = 0.0
    result[f"{value_column}_cumulative_pct"] = 0.0

    eligible = result[value_column].fillna(0) > 0
    ranked = result.loc[eligible].sort_values(
        [value_column, "item_code"],
        ascending=[False, True],
    )
    total = ranked[value_column].sum()
    if ranked.empty or total <= 0:
        return result

    participation = ranked[value_column] / total
    cumulative = participation.cumsum()
    tolerance = 1e-12
    classes = np.select(
        [cumulative <= 0.80 + tolerance, cumulative <= 0.95 + tolerance],
        ["A", "B"],
        default="C",
    )

    result.loc[ranked.index, class_column] = classes
    result.loc[ranked.index, f"{value_column}_participation_pct"] = (
        participation * 100
    )
    result.loc[ranked.index, f"{value_column}_cumulative_pct"] = cumulative * 100
    return result


def classify_xyz_value(
    *,
    coefficient_of_variation: float | None,
    months_with_sales: int,
    min_months: int,
    is_intermittent: bool,
    is_negative_demand: bool,
) -> str:
    if is_negative_demand:
        return "REVIEW_REQUIRED"
    if months_with_sales < min_months:
        return "INSUFFICIENT_HISTORY"
    if is_intermittent:
        return "INTERMITTENT"
    if coefficient_of_variation is None or not np.isfinite(coefficient_of_variation):
        return "REVIEW_REQUIRED"
    if coefficient_of_variation <= 0.50:
        return "X"
    if coefficient_of_variation <= 1.00:
        return "Y"
    return "Z"


def combine_abc_xyz(abc_class: str, xyz_class: str) -> str:
    if abc_class not in {"A", "B", "C"}:
        return "REVIEW_REQUIRED"
    if xyz_class in {"X", "Y", "Z"}:
        return f"{abc_class}{xyz_class}"
    return f"{abc_class}-{xyz_class}"


def forecast_recommendation(
    combined_class: str,
    data_quality_status: str,
) -> tuple[str, bool]:
    if combined_class == "REVIEW_REQUIRED" or data_quality_status in {
        "NEGATIVE_DEMAND",
        "REVIEW_REQUIRED",
        "ZERO_OR_NULL_VALUES",
    }:
        return "Excluir temporalmente del forecast y revisar datos.", False
    if combined_class.endswith("INSUFFICIENT_HISTORY"):
        return "No entrenar todavía; acumular más historial.", False
    if combined_class.endswith("INTERMITTENT"):
        return "Usar método específico para demanda intermitente.", True
    if combined_class in {"AX", "AY"}:
        return "Candidato fuerte para forecast.", True
    if combined_class == "AZ":
        return "Forecast con cautela y revisión de estacionalidad.", True
    if combined_class in {"BX", "BY"}:
        return "Candidato para forecast estándar.", True
    if combined_class in {"BZ", "CX", "CY", "CZ"}:
        return "Usar baseline simple o promedio móvil.", True
    return "Revisar antes de seleccionar estrategia de forecast.", False


def _quality_status(row: pd.Series, min_months: int) -> str:
    if bool(row["is_negative_demand"]):
        return "NEGATIVE_DEMAND"
    if bool(row["has_zero_or_null_values"]):
        return "ZERO_OR_NULL_VALUES"
    if int(row["months_with_sales"]) < min_months:
        return "INSUFFICIENT_HISTORY"
    if bool(row["is_intermittent"]):
        return "INTERMITTENT_DEMAND"
    if bool(row["has_amount_anomaly"]):
        return "AMOUNT_ANOMALY"
    if pd.isna(row["coefficient_of_variation"]):
        return "REVIEW_REQUIRED"
    return "OK"


def calculate_item_metrics(
    demand_rows: list[dict[str, Any]],
    date_from: date,
    date_to: date,
    min_months: int = 12,
) -> pd.DataFrame:
    columns = [
        "item_code",
        "item_name",
        "item_group",
        "first_sale_period",
        "last_sale_period",
        "months_with_sales",
        "total_months_available",
        "months_without_sales",
        "net_quantity_total",
        "net_amount_total",
        "avg_monthly_quantity",
        "std_monthly_quantity",
        "coefficient_of_variation",
        "max_monthly_quantity",
        "min_monthly_quantity",
        "last_3_months_quantity",
        "last_6_months_quantity",
        "last_12_months_quantity",
        "is_negative_demand",
        "has_amount_anomaly",
        "is_intermittent",
        "has_zero_or_null_values",
        "data_quality_status",
    ]
    if not demand_rows:
        return pd.DataFrame(columns=columns)

    raw = pd.DataFrame(demand_rows)
    raw["period"] = pd.PeriodIndex(raw["period"], freq="M")
    raw["net_quantity"] = pd.to_numeric(raw["net_quantity"], errors="coerce")
    raw["net_sales_total"] = pd.to_numeric(
        raw["net_sales_total"], errors="coerce"
    )

    monthly = (
        raw.groupby(["item_code", "period"], as_index=False)
        .agg(
            item_name=("item_name", "first"),
            item_group=("item_group", "first"),
            net_quantity=("net_quantity", "sum"),
            net_sales_total=("net_sales_total", "sum"),
        )
        .sort_values(["item_code", "period"])
    )
    monthly["observed"] = True

    periods = pd.period_range(date_from, date_to, freq="M")
    item_codes = monthly["item_code"].drop_duplicates().sort_values()
    grid = pd.MultiIndex.from_product(
        [item_codes, periods],
        names=["item_code", "period"],
    )
    complete = monthly.set_index(["item_code", "period"]).reindex(grid)
    metadata = (
        monthly.groupby("item_code", as_index=True)
        .agg(item_name=("item_name", "first"), item_group=("item_group", "first"))
    )
    complete["item_name"] = complete.index.get_level_values("item_code").map(
        metadata["item_name"]
    )
    complete["item_group"] = complete.index.get_level_values("item_code").map(
        metadata["item_group"]
    )
    complete["observed"] = (
        complete["observed"].astype("boolean").fillna(False).astype(bool)
    )
    complete["net_quantity"] = complete["net_quantity"].fillna(0.0)
    complete["net_sales_total"] = complete["net_sales_total"].fillna(0.0)
    complete = complete.reset_index()

    positive = complete[complete["net_quantity"] > 0]
    sales_periods = positive.groupby("item_code")["period"].agg(["min", "max", "count"])
    grouped = complete.groupby("item_code", sort=True)
    metrics = grouped.agg(
        item_name=("item_name", "first"),
        item_group=("item_group", "first"),
        net_quantity_total=("net_quantity", "sum"),
        net_amount_total=("net_sales_total", "sum"),
        avg_monthly_quantity=("net_quantity", "mean"),
        std_monthly_quantity=("net_quantity", lambda values: values.std(ddof=0)),
        max_monthly_quantity=("net_quantity", "max"),
        min_monthly_quantity=("net_quantity", "min"),
    )
    aligned_sales = sales_periods.reindex(metrics.index)
    metrics["first_sale_period"] = aligned_sales["min"].astype("string")
    metrics["last_sale_period"] = aligned_sales["max"].astype("string")
    metrics["months_with_sales"] = aligned_sales["count"].fillna(0).astype(int)
    metrics["total_months_available"] = len(periods)
    metrics["months_without_sales"] = (
        metrics["total_months_available"] - metrics["months_with_sales"]
    )

    mean = metrics["avg_monthly_quantity"]
    metrics["coefficient_of_variation"] = np.where(
        mean > 0,
        metrics["std_monthly_quantity"] / mean,
        np.nan,
    )

    for window in (3, 6, 12):
        window_periods = set(periods[-window:])
        values = (
            complete[complete["period"].isin(window_periods)]
            .groupby("item_code")["net_quantity"]
            .sum()
        )
        metrics[f"last_{window}_months_quantity"] = values

    observed = complete[complete["observed"]]
    amount_flags = observed.assign(
        anomaly=(
            (observed["net_sales_total"] < 0)
            | (
                (observed["net_quantity"] > 0)
                & (observed["net_sales_total"] <= 0)
            )
            | (
                (observed["net_quantity"] < 0)
                & (observed["net_sales_total"] >= 0)
            )
        ),
        zero_or_null=(
            observed["net_quantity"].isna()
            | observed["net_sales_total"].isna()
            | (observed["net_quantity"] == 0)
            | (
                (observed["net_quantity"] != 0)
                & (observed["net_sales_total"] == 0)
            )
        ),
    ).groupby("item_code")[["anomaly", "zero_or_null"]].max()

    metrics["is_negative_demand"] = metrics["net_quantity_total"] < 0
    metrics["has_amount_anomaly"] = (
        metrics.index.map(amount_flags["anomaly"]).fillna(False).astype(bool)
        | (metrics["net_amount_total"] < 0)
    )
    metrics["has_zero_or_null_values"] = (
        metrics.index.map(amount_flags["zero_or_null"]).fillna(False).astype(bool)
    )
    active_ratio = metrics["months_with_sales"] / metrics["total_months_available"]
    metrics["is_intermittent"] = active_ratio < 0.50
    metrics["data_quality_status"] = metrics.apply(
        _quality_status,
        axis=1,
        min_months=min_months,
    )

    metrics = metrics.reset_index()
    return metrics[columns].sort_values("item_code").reset_index(drop=True)


def build_analytics(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = None,
    item_group: str | None = None,
    warehouse_code: str | None = None,
    min_months: int = 12,
) -> AnalyticsResult:
    if min_months < 1:
        raise ValueError("min_months debe ser mayor o igual a 1.")
    resolved_from, resolved_to = resolve_analysis_date_range(date_from, date_to)
    rows = get_monthly_demand(
        resolved_from,
        resolved_to,
        item_code,
        warehouse_code,
        item_group,
    )
    metrics = calculate_item_metrics(
        rows,
        resolved_from,
        resolved_to,
        min_months,
    )

    abc_quantity = assign_abc_classes(
        metrics,
        "net_quantity_total",
        "abc_quantity_class",
    )
    abc_amount = assign_abc_classes(
        metrics,
        "net_amount_total",
        "abc_amount_class",
    )
    abc_amount["amount_warning"] = np.where(
        abc_amount["has_amount_anomaly"]
        | (abc_amount["net_amount_total"] <= 0)
        | (
            (abc_amount["net_quantity_total"] > 0)
            & (abc_amount["net_amount_total"] == 0)
        ),
        "AMOUNT_REVIEW_REQUIRED",
        None,
    )

    xyz = metrics.copy()
    xyz["xyz_class"] = xyz.apply(
        lambda row: classify_xyz_value(
            coefficient_of_variation=(
                None
                if pd.isna(row["coefficient_of_variation"])
                else float(row["coefficient_of_variation"])
            ),
            months_with_sales=int(row["months_with_sales"]),
            min_months=min_months,
            is_intermittent=bool(row["is_intermittent"]),
            is_negative_demand=bool(row["is_negative_demand"]),
        ),
        axis=1,
    )

    combined = abc_quantity.merge(
        xyz[["item_code", "xyz_class"]],
        on="item_code",
        how="left",
    ).merge(
        abc_amount[["item_code", "abc_amount_class", "amount_warning"]],
        on="item_code",
        how="left",
    )
    combined["abc_xyz_class"] = combined.apply(
        lambda row: combine_abc_xyz(
            row["abc_quantity_class"],
            row["xyz_class"],
        ),
        axis=1,
    )
    recommendations = combined.apply(
        lambda row: forecast_recommendation(
            row["abc_xyz_class"],
            row["data_quality_status"],
        ),
        axis=1,
    )
    combined["forecast_recommendation"] = [
        value[0] for value in recommendations
    ]
    combined["recommended_for_forecast"] = [
        value[1] for value in recommendations
    ]

    summary = build_summary(
        combined,
        resolved_from,
        resolved_to,
        min_months,
    )
    return AnalyticsResult(
        date_from=resolved_from,
        date_to=resolved_to,
        metrics=metrics,
        abc_quantity=abc_quantity,
        abc_amount=abc_amount,
        xyz=xyz,
        combined=combined,
        summary=summary,
    )


def build_summary(
    combined: pd.DataFrame,
    date_from: date,
    date_to: date,
    min_months: int,
) -> dict[str, Any]:
    def count(column: str, value: str) -> int:
        if combined.empty:
            return 0
        return int((combined[column] == value).sum())

    return {
        "total_items_analyzed": len(combined),
        "items_a": count("abc_quantity_class", "A"),
        "items_b": count("abc_quantity_class", "B"),
        "items_c": count("abc_quantity_class", "C"),
        "items_x": count("xyz_class", "X"),
        "items_y": count("xyz_class", "Y"),
        "items_z": count("xyz_class", "Z"),
        "intermittent_items": count("xyz_class", "INTERMITTENT"),
        "insufficient_history_items": count(
            "xyz_class",
            "INSUFFICIENT_HISTORY",
        ),
        "negative_demand_items": int(
            combined["is_negative_demand"].sum()
        ) if not combined.empty else 0,
        "amount_anomaly_items": int(
            combined["has_amount_anomaly"].sum()
        ) if not combined.empty else 0,
        "forecast_recommended_items": int(
            combined["recommended_for_forecast"].sum()
        ) if not combined.empty else 0,
        "forecast_not_recommended_items": int(
            (~combined["recommended_for_forecast"]).sum()
        ) if not combined.empty else 0,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_months_available": len(pd.period_range(date_from, date_to, freq="M")),
        "min_months": min_months,
    }


def dataframe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        clean: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, np.generic):
                value = value.item()
            clean[key] = None if pd.isna(value) else value
        records.append(clean)
    return records
