import numpy as np
import pandas as pd

from app.services.forecast_metrics import mae, rmse, smape, wape
from app.services.forecast_service import moving_average, naive_last_value
from app.services.model_selection_service import select_best_model


def test_forecast_metrics() -> None:
    actual = [10, 20, 30]
    predicted = [12, 18, 33]

    assert mae(actual, predicted) == 7 / 3
    assert np.isclose(rmse(actual, predicted), np.sqrt(17 / 3))
    assert np.isclose(wape(actual, predicted), 7 / 60 * 100)
    assert 0 < smape(actual, predicted) < 20


def test_wape_returns_none_when_actual_total_is_zero() -> None:
    assert wape([0, 0], [1, 2]) is None


def test_naive_last_value_forecast() -> None:
    result = naive_last_value(np.array([1.0, 2.0, 4.0]), 3)
    assert result.tolist() == [4.0, 4.0, 4.0]


def test_moving_average_forecast() -> None:
    result = moving_average(np.array([1.0, 2.0, 3.0, 7.0]), 2, 3)
    assert np.allclose(result, [4.0, 4.0])


def test_best_model_selection_prefers_wape_then_mae() -> None:
    comparison = pd.DataFrame(
        [
            {
                "item_code": "A",
                "model": "m1",
                "wape": 20.0,
                "mae": 2.0,
                "rmse": 3.0,
                "bias": 0.1,
                "evaluated_months": 6,
                "status": "ok",
                "is_intermittent": False,
            },
            {
                "item_code": "A",
                "model": "m2",
                "wape": 10.0,
                "mae": 3.0,
                "rmse": 4.0,
                "bias": 0.2,
                "evaluated_months": 6,
                "status": "ok",
                "is_intermittent": False,
            },
        ]
    )

    result = select_best_model(comparison).iloc[0]

    assert result["best_model"] == "m2"
    assert result["forecast_confidence"] == "HIGH"
