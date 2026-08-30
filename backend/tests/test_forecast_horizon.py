import numpy as np

from app.services.forecast_service import moving_average


def test_deterministic_demo_forecast_has_three_future_months() -> None:
    history = np.arange(1, 13, dtype=float)
    prediction = moving_average(history, horizon=3, window=3)

    assert len(prediction) == 3
    assert np.all(np.isfinite(prediction))
    assert np.all(prediction >= 0)
    assert prediction.tolist() == [11.0, 11.0, 11.0]
