from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any
import warnings

import numpy as np
import pandas as pd

from app.services.demand_service import get_monthly_demand
from app.services.eda_service import build_analytics
from app.services.forecast_metrics import calculate_metrics
from app.services.model_selection_service import select_best_model


MODEL_DESCRIPTIONS = [
    {"model": "naive_last_value", "type": "baseline", "description": "Último valor observado."},
    {"model": "seasonal_naive_12", "type": "baseline", "description": "Mismo mes del año anterior."},
    {"model": "moving_average_3", "type": "baseline", "description": "Promedio de los últimos 3 meses."},
    {"model": "moving_average_6", "type": "baseline", "description": "Promedio de los últimos 6 meses."},
    {"model": "moving_average_12", "type": "baseline", "description": "Promedio de los últimos 12 meses."},
    {"model": "exponential_smoothing", "type": "statistical", "description": "Suavizamiento exponencial simple."},
    {"model": "holt_winters", "type": "statistical", "description": "Tendencia y estacionalidad aditivas."},
    {"model": "croston", "type": "intermittent", "description": "Croston clásico para demanda intermitente."},
    {"model": "random_forest_global", "type": "machine_learning", "description": "Modelo global con rezagos y variables calendario."},
]


@dataclass(frozen=True)
class ForecastResult:
    candidates: pd.DataFrame
    excluded: pd.DataFrame
    dataset: pd.DataFrame
    comparison: pd.DataFrame
    best_models: pd.DataFrame
    future: pd.DataFrame
    summary: dict[str, Any]


def naive_last_value(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) < 1:
        raise ValueError("naive_last_value requiere al menos un dato.")
    return np.repeat(float(train[-1]), horizon)


def moving_average(train: np.ndarray, horizon: int, window: int) -> np.ndarray:
    if len(train) < window:
        raise ValueError(f"moving_average_{window} requiere {window} meses.")
    return np.repeat(float(np.mean(train[-window:])), horizon)


def seasonal_naive_12(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) < 12:
        raise ValueError("seasonal_naive_12 requiere al menos 12 meses.")
    values = [float(train[len(train) - 12 + (step % 12)]) for step in range(horizon)]
    return np.asarray(values)


def croston_forecast(train: np.ndarray, horizon: int, alpha: float = 0.1) -> np.ndarray:
    nonzero = np.flatnonzero(train > 0)
    if len(nonzero) < 2:
        positive = train[train > 0]
        value = float(positive.mean()) if len(positive) else 0.0
        return np.repeat(value, horizon)
    first = int(nonzero[0])
    demand = float(train[first])
    interval = 1.0
    last_nonzero = first
    for index in nonzero[1:]:
        gap = int(index - last_nonzero)
        demand = alpha * float(train[index]) + (1 - alpha) * demand
        interval = alpha * gap + (1 - alpha) * interval
        last_nonzero = int(index)
    return np.repeat(max(0.0, demand / max(interval, 1e-9)), horizon)


def _statistical_forecast(
    train: np.ndarray,
    horizon: int,
    model: str,
) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if model == "exponential_smoothing":
            if len(train) < 6:
                raise ValueError("exponential_smoothing requiere 6 meses.")
            fit = SimpleExpSmoothing(train, initialization_method="estimated").fit(
                optimized=True
            )
        elif model == "holt_winters":
            if len(train) < 24:
                raise ValueError("holt_winters requiere al menos 24 meses.")
            fit = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=12,
                initialization_method="estimated",
            ).fit(optimized=True, remove_bias=False)
        else:
            raise ValueError(f"Modelo estadístico desconocido: {model}")
    return np.maximum(0.0, np.asarray(fit.forecast(horizon), dtype=float))


def _predict_model(
    model: str,
    train: np.ndarray,
    horizon: int,
    intermittent: bool,
) -> np.ndarray:
    if model == "naive_last_value":
        return naive_last_value(train, horizon)
    if model == "seasonal_naive_12":
        return seasonal_naive_12(train, horizon)
    if model.startswith("moving_average_"):
        return moving_average(train, horizon, int(model.rsplit("_", 1)[1]))
    if model in {"exponential_smoothing", "holt_winters"}:
        return _statistical_forecast(train, horizon, model)
    if model == "croston":
        if not intermittent:
            raise ValueError("Croston solo aplica a demanda intermitente.")
        return croston_forecast(train, horizon)
    raise ValueError(f"Modelo desconocido: {model}")


def _complete_dataset(
    rows: list[dict[str, Any]],
    candidates: pd.DataFrame,
    date_from: date,
    date_to: date,
    warehouse_code: str | None,
) -> pd.DataFrame:
    raw = pd.DataFrame(rows)
    raw["period"] = pd.PeriodIndex(raw["period"], freq="M")
    monthly = (
        raw.groupby(["item_code", "period"], as_index=False)
        .agg(
            item_name=("item_name", "first"),
            net_quantity=("net_quantity", "sum"),
            net_amount=("net_sales_total", "sum"),
        )
    )
    periods = pd.period_range(date_from, date_to, freq="M")
    index = pd.MultiIndex.from_product(
        [candidates["item_code"].astype(str), periods],
        names=["item_code", "period"],
    )
    complete = monthly.set_index(["item_code", "period"]).reindex(index)
    metadata = candidates.set_index("item_code")
    complete["item_name"] = complete.index.get_level_values("item_code").map(
        metadata["item_name"]
    )
    complete["net_quantity"] = complete["net_quantity"].fillna(0.0)
    complete["net_amount"] = complete["net_amount"].fillna(0.0)
    complete = complete.reset_index()
    complete["year"] = complete["period"].dt.year
    complete["month"] = complete["period"].dt.month
    complete["warehouse_code"] = warehouse_code or "ALL"
    for source, target in (
        ("abc_quantity_class", "abc_class"),
        ("xyz_class", "xyz_class"),
        ("abc_xyz_class", "abc_xyz_class"),
        ("data_quality_status", "data_quality_status"),
    ):
        complete[target] = complete["item_code"].map(metadata[source])
    complete["period"] = complete["period"].astype(str)
    return complete[
        [
            "period",
            "year",
            "month",
            "item_code",
            "item_name",
            "warehouse_code",
            "net_quantity",
            "net_amount",
            "abc_class",
            "xyz_class",
            "abc_xyz_class",
            "data_quality_status",
        ]
    ]


def _comparison_without_rf(
    dataset: pd.DataFrame,
    candidates: pd.DataFrame,
    test_months: int,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    candidate_index = candidates.set_index("item_code")
    models = [
        "naive_last_value",
        "seasonal_naive_12",
        "moving_average_3",
        "moving_average_6",
        "moving_average_12",
        "exponential_smoothing",
        "holt_winters",
    ]
    for item_code, group in dataset.groupby("item_code", sort=True):
        series = group.sort_values("period")["net_quantity"].to_numpy(dtype=float)
        effective_test = test_months if len(series) >= test_months + 12 else 3
        train, actual = series[:-effective_test], series[-effective_test:]
        intermittent = bool(candidate_index.loc[item_code, "is_intermittent"])
        item_models = models + (["croston"] if intermittent else [])
        for model in item_models:
            base = {
                "item_code": item_code,
                "model": model,
                "is_intermittent": intermittent,
            }
            try:
                predicted = _predict_model(model, train, effective_test, intermittent)
                metrics = calculate_metrics(actual, predicted)
                records.append({**base, **metrics, "status": "ok", "error": None})
            except Exception as exc:
                records.append(
                    {
                        **base,
                        "mae": None,
                        "rmse": None,
                        "wape": None,
                        "smape": None,
                        "bias": None,
                        "evaluated_months": effective_test,
                        "actual_test_total": float(actual.sum()),
                        "predicted_test_total": None,
                        "status": "error",
                        "error": str(exc)[:250],
                    }
                )
    return pd.DataFrame(records)


def _encode_class(value: str, mapping: dict[str, int]) -> int:
    return mapping.get(str(value), -1)


def _rf_training_frame(
    dataset: pd.DataFrame,
    candidates: pd.DataFrame,
    test_months: int,
) -> tuple[pd.DataFrame, dict[str, list[float]], list[str]]:
    metadata = candidates.set_index("item_code")
    rows: list[dict[str, Any]] = []
    histories: dict[str, list[float]] = {}
    test_periods: list[str] = []
    for item_code, group in dataset.groupby("item_code", sort=True):
        ordered = group.sort_values("period")
        values = ordered["net_quantity"].astype(float).tolist()
        periods = ordered["period"].tolist()
        cutoff = len(values) - test_months
        histories[item_code] = values[:cutoff]
        test_periods = periods[cutoff:]
        for index in range(12, cutoff):
            history = values[:index]
            rows.append(
                _rf_features(
                    item_code,
                    periods[index],
                    history,
                    metadata.loc[item_code],
                    target=values[index],
                )
            )
    return pd.DataFrame(rows), histories, test_periods


def _rf_features(
    item_code: str,
    period: str,
    history: list[float],
    metadata: pd.Series,
    target: float | None = None,
) -> dict[str, Any]:
    value = pd.Period(period, freq="M")
    abc_map = {"A": 3, "B": 2, "C": 1}
    xyz_map = {"X": 3, "Y": 2, "Z": 1, "INTERMITTENT": 0}
    row = {
        "item_code": item_code,
        "period": period,
        "year": value.year,
        "month": value.month,
        "period_number": value.ordinal,
        "lag_1": history[-1],
        "lag_2": history[-2],
        "lag_3": history[-3],
        "lag_6": history[-6],
        "rolling_mean_3": float(np.mean(history[-3:])),
        "rolling_mean_6": float(np.mean(history[-6:])),
        "rolling_std_3": float(np.std(history[-3:])),
        "abc_encoded": _encode_class(metadata["abc_quantity_class"], abc_map),
        "xyz_encoded": _encode_class(metadata["xyz_class"], xyz_map),
    }
    if target is not None:
        row["target"] = target
    return row


RF_FEATURES = [
    "year",
    "month",
    "period_number",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_std_3",
    "abc_encoded",
    "xyz_encoded",
]


def _random_forest_comparison(
    dataset: pd.DataFrame,
    candidates: pd.DataFrame,
    test_months: int,
) -> tuple[pd.DataFrame, Any | None]:
    try:
        from sklearn.ensemble import RandomForestRegressor

        training, histories, test_periods = _rf_training_frame(
            dataset, candidates, test_months
        )
        if len(training) < 100:
            return pd.DataFrame(), None
        model = RandomForestRegressor(
            n_estimators=120,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(training[RF_FEATURES], training["target"])
        metadata = candidates.set_index("item_code")
        actual_lookup = dataset.set_index(["item_code", "period"])["net_quantity"]
        records = []
        for item_code, history in histories.items():
            predicted = []
            rolling = list(history)
            for period in test_periods:
                features = _rf_features(
                    item_code, period, rolling, metadata.loc[item_code]
                )
                value = max(0.0, float(model.predict(pd.DataFrame([features])[RF_FEATURES])[0]))
                predicted.append(value)
                rolling.append(value)
            actual = [
                float(actual_lookup.loc[(item_code, period)]) for period in test_periods
            ]
            records.append(
                {
                    "item_code": item_code,
                    "model": "random_forest_global",
                    "is_intermittent": bool(
                        metadata.loc[item_code, "is_intermittent"]
                    ),
                    **calculate_metrics(actual, predicted),
                    "status": "ok",
                    "error": None,
                }
            )
        return pd.DataFrame(records), model
    except Exception as exc:
        failure = pd.DataFrame(
            [
                {
                    "item_code": code,
                    "model": "random_forest_global",
                    "status": "error",
                    "error": str(exc)[:250],
                }
                for code in candidates["item_code"]
            ]
        )
        return failure, None


def _future_for_model(
    model_name: str,
    values: np.ndarray,
    horizon: int,
    intermittent: bool,
) -> np.ndarray:
    return _predict_model(model_name, values, horizon, intermittent)


def _future_forecasts(
    dataset: pd.DataFrame,
    candidates: pd.DataFrame,
    best_models: pd.DataFrame,
    comparison: pd.DataFrame,
    horizon: int,
    rf_model: Any | None,
) -> pd.DataFrame:
    candidate_index = candidates.set_index("item_code")
    comparison_ok = comparison[comparison["status"] == "ok"]
    records = []
    for row in best_models.itertuples():
        if not row.best_model:
            continue
        group = dataset[dataset["item_code"] == row.item_code].sort_values("period")
        values = group["net_quantity"].to_numpy(dtype=float)
        last_period = pd.Period(group["period"].iloc[-1], freq="M")
        future_periods = [
            str(last_period + step) for step in range(1, horizon + 1)
        ]
        intermittent = bool(candidate_index.loc[row.item_code, "is_intermittent"])
        try:
            if row.best_model == "random_forest_global":
                if rf_model is None:
                    raise ValueError("Random Forest global no disponible.")
                history = values.tolist()
                predicted = []
                for period in future_periods:
                    features = _rf_features(
                        row.item_code,
                        period,
                        history,
                        candidate_index.loc[row.item_code],
                    )
                    value = max(
                        0.0,
                        float(
                            rf_model.predict(
                                pd.DataFrame([features])[RF_FEATURES]
                            )[0]
                        ),
                    )
                    predicted.append(value)
                    history.append(value)
                predicted = np.asarray(predicted)
            else:
                predicted = _future_for_model(
                    row.best_model, values, horizon, intermittent
                )
            model_metrics = comparison_ok[
                (comparison_ok["item_code"] == row.item_code)
                & (comparison_ok["model"] == row.best_model)
            ]
            error_scale = (
                float(model_metrics["rmse"].iloc[0])
                if not model_metrics.empty
                else float(np.std(values))
            )
            for period, value in zip(future_periods, predicted):
                records.append(
                    {
                        "item_code": row.item_code,
                        "item_name": candidate_index.loc[row.item_code, "item_name"],
                        "warehouse_code": group["warehouse_code"].iloc[0],
                        "forecast_period": period,
                        "forecast_quantity": max(0.0, float(value)),
                        "lower_bound": max(0.0, float(value) - 1.96 * error_scale),
                        "upper_bound": max(0.0, float(value) + 1.96 * error_scale),
                        "model_used": row.best_model,
                        "forecast_confidence": row.forecast_confidence,
                    }
                )
        except Exception:
            continue
    return pd.DataFrame(records)


def _exclusion_reason(row: pd.Series) -> str:
    if bool(row["is_negative_demand"]):
        return "NEGATIVE_DEMAND"
    if row["xyz_class"] == "INSUFFICIENT_HISTORY":
        return "INSUFFICIENT_HISTORY"
    if row["abc_xyz_class"] == "REVIEW_REQUIRED":
        return "REVIEW_REQUIRED"
    return str(row["data_quality_status"])


@lru_cache(maxsize=8)
def build_forecast(
    date_from: date | None = None,
    date_to: date | None = None,
    item_group: str | None = None,
    warehouse_code: str | None = None,
    test_months: int = 6,
    horizon: int = 3,
) -> ForecastResult:
    if test_months not in range(3, 13):
        raise ValueError("test_months debe estar entre 3 y 12.")
    if horizon not in {3, 6}:
        raise ValueError("horizon debe ser 3 o 6.")

    analytics = build_analytics(
        date_from=date_from,
        date_to=date_to,
        item_group=item_group,
        warehouse_code=warehouse_code,
    )
    all_items = analytics.combined.copy()
    candidates = all_items[all_items["recommended_for_forecast"]].copy()
    excluded = all_items[~all_items["recommended_for_forecast"]].copy()
    excluded["exclusion_reason"] = excluded.apply(_exclusion_reason, axis=1)
    if candidates.empty:
        empty = pd.DataFrame()
        return ForecastResult(
            candidates, excluded, empty, empty, empty, empty,
            {
                "candidates": 0,
                "modeled_items": 0,
                "excluded_items": len(excluded),
                "forecast_horizon": horizon,
            },
        )

    rows = get_monthly_demand(
        analytics.date_from,
        analytics.date_to,
        warehouse_code=warehouse_code,
        item_group=item_group,
    )
    candidate_codes = set(candidates["item_code"].astype(str))
    rows = [row for row in rows if str(row["item_code"]) in candidate_codes]
    dataset = _complete_dataset(
        rows,
        candidates,
        analytics.date_from,
        analytics.date_to,
        warehouse_code,
    )
    comparison = _comparison_without_rf(dataset, candidates, test_months)
    rf_comparison, rf_model = _random_forest_comparison(
        dataset, candidates, test_months
    )
    comparison = pd.concat([comparison, rf_comparison], ignore_index=True)
    best_models = select_best_model(comparison)
    future = _future_forecasts(
        dataset,
        candidates,
        best_models,
        comparison,
        horizon,
        rf_model,
    )

    valid = comparison[comparison["status"] == "ok"]
    summary = {
        "candidates": len(candidates),
        "modeled_items": int(best_models["best_model"].notna().sum()),
        "excluded_items": len(excluded),
        "average_wape": float(best_models["best_wape"].dropna().mean()),
        "average_mae": float(best_models["best_mae"].dropna().mean()),
        "average_rmse": float(best_models["best_rmse"].dropna().mean()),
        "average_bias": float(best_models["best_bias"].dropna().mean()),
        "high_confidence": int(
            (best_models["forecast_confidence"] == "HIGH").sum()
        ),
        "medium_confidence": int(
            (best_models["forecast_confidence"] == "MEDIUM").sum()
        ),
        "low_confidence": int(
            (best_models["forecast_confidence"] == "LOW").sum()
        ),
        "not_recommended": int(
            (best_models["forecast_confidence"] == "NOT_RECOMMENDED").sum()
        ),
        "most_frequent_best_model": (
            best_models["best_model"].value_counts().index[0]
            if best_models["best_model"].notna().any()
            else None
        ),
        "best_average_model": (
            valid.groupby("model")["wape"].mean().sort_values().index[0]
            if not valid.empty and valid["wape"].notna().any()
            else None
        ),
        "forecast_horizon": horizon,
        "forecast_records": len(future),
        "first_forecast_period": (
            future["forecast_period"].min() if not future.empty else None
        ),
        "last_forecast_period": (
            future["forecast_period"].max() if not future.empty else None
        ),
        "test_months": test_months,
        "date_from": analytics.date_from.isoformat(),
        "date_to": analytics.date_to.isoformat(),
    }
    return ForecastResult(
        candidates,
        excluded,
        dataset,
        comparison,
        best_models,
        future,
        summary,
    )
