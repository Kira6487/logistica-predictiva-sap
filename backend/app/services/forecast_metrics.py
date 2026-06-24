from __future__ import annotations

import numpy as np


def _arrays(actual, predicted) -> tuple[np.ndarray, np.ndarray]:
    y_true = np.asarray(actual, dtype=float)
    y_pred = np.asarray(predicted, dtype=float)
    if y_true.shape != y_pred.shape:
        raise ValueError("actual y predicted deben tener la misma longitud.")
    return y_true, y_pred


def mae(actual, predicted) -> float:
    y_true, y_pred = _arrays(actual, predicted)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(actual, predicted) -> float:
    y_true, y_pred = _arrays(actual, predicted)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def wape(actual, predicted) -> float | None:
    y_true, y_pred = _arrays(actual, predicted)
    denominator = float(np.sum(np.abs(y_true)))
    if denominator == 0:
        return None
    return float(np.sum(np.abs(y_true - y_pred)) / denominator * 100)


def smape(actual, predicted) -> float:
    y_true, y_pred = _arrays(actual, predicted)
    denominator = np.abs(y_true) + np.abs(y_pred)
    terms = np.divide(
        2 * np.abs(y_true - y_pred),
        denominator,
        out=np.zeros_like(denominator, dtype=float),
        where=denominator != 0,
    )
    return float(np.mean(terms) * 100)


def bias(actual, predicted) -> float:
    y_true, y_pred = _arrays(actual, predicted)
    return float(np.mean(y_pred - y_true))


def calculate_metrics(actual, predicted) -> dict[str, float | int | None]:
    y_true, y_pred = _arrays(actual, predicted)
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "wape": wape(y_true, y_pred),
        "smape": smape(y_true, y_pred),
        "bias": bias(y_true, y_pred),
        "evaluated_months": len(y_true),
        "actual_test_total": float(y_true.sum()),
        "predicted_test_total": float(y_pred.sum()),
    }
