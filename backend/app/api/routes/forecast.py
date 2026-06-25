from datetime import date

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import DatabaseConnectionError
from app.services.eda_service import dataframe_records
from app.services.demand_service import get_monthly_demand
from app.services.forecast_service import (
    MODEL_DESCRIPTIONS,
    build_forecast,
    load_forecast_artifacts,
    load_monthly_demand_artifact,
)

router = APIRouter(prefix="/forecast", tags=["forecast"])


def _result(
    date_from: date | None,
    date_to: date | None,
    item_group: str | None,
    warehouse_code: str | None,
    test_months: int,
    horizon: int,
):
    try:
        if (
            date_from is None
            and date_to is None
            and item_group is None
            and warehouse_code is None
            and test_months == 6
        ):
            artifact = load_forecast_artifacts(horizon)
            if artifact is not None:
                return artifact
        return build_forecast(
            date_from,
            date_to,
            item_group,
            warehouse_code,
            test_months,
            horizon,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except DatabaseConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def _params(
    date_from: date | None,
    date_to: date | None,
    item_group: str | None,
    warehouse_code: str | None,
    test_months: int,
    horizon: int,
):
    return _result(
        date_from,
        date_to,
        item_group,
        warehouse_code,
        test_months,
        horizon,
    )


@router.get("/models")
def models() -> list[dict]:
    return MODEL_DESCRIPTIONS


@router.get("/candidates")
def candidates(
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    test_months: int = Query(default=6, ge=3, le=12),
    horizon: int = Query(default=3),
) -> list[dict]:
    frame = _params(
        date_from, date_to, item_group, warehouse_code, test_months, horizon
    )
    candidates_frame = frame.candidates.merge(
        frame.best_models,
        on="item_code",
        how="left",
    )
    if item_code:
        candidates_frame = candidates_frame[
            candidates_frame["item_code"] == item_code
        ]
    return dataframe_records(candidates_frame)


@router.get("/summary")
def summary(
    date_from: date | None = None,
    date_to: date | None = None,
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    test_months: int = Query(default=6, ge=3, le=12),
    horizon: int = Query(default=3),
) -> dict:
    return _params(
        date_from, date_to, item_group, warehouse_code, test_months, horizon
    ).summary


@router.get("/results")
def results(
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    test_months: int = Query(default=6, ge=3, le=12),
    horizon: int = Query(default=3),
) -> list[dict]:
    frame = _params(
        date_from, date_to, item_group, warehouse_code, test_months, horizon
    ).future
    if item_code:
        frame = frame[frame["item_code"] == item_code]
    return dataframe_records(frame)


@router.get("/comparison")
def comparison(
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = Query(default=None),
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    test_months: int = Query(default=6, ge=3, le=12),
    horizon: int = Query(default=3),
) -> list[dict]:
    frame = _params(
        date_from, date_to, item_group, warehouse_code, test_months, horizon
    ).comparison
    if item_code:
        frame = frame[frame["item_code"] == item_code]
    return dataframe_records(frame)


@router.get("/item/{item_code}")
def item_detail(
    item_code: str,
    date_from: date | None = None,
    date_to: date | None = None,
    item_group: str | None = Query(default=None),
    warehouse_code: str | None = Query(default=None),
    test_months: int = Query(default=6, ge=3, le=12),
    horizon: int = Query(default=3),
) -> dict:
    result = _params(
        date_from, date_to, item_group, warehouse_code, test_months, horizon
    )
    candidate = result.candidates[result.candidates["item_code"] == item_code]
    if candidate.empty:
        excluded = result.excluded[result.excluded["item_code"] == item_code]
        if not excluded.empty:
            return {
                "item_code": item_code,
                "status": "excluded",
                "reason": dataframe_records(excluded)[0],
            }
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    dataset = (
        result.dataset[result.dataset["item_code"] == item_code]
        if "item_code" in result.dataset.columns
        else pd.DataFrame()
    )
    if dataset.empty:
        range_from = date.fromisoformat(str(result.summary["date_from"]))
        range_to = date.fromisoformat(str(result.summary["date_to"]))
        try:
            rows = get_monthly_demand(range_from, range_to, item_code=item_code)
        except DatabaseConnectionError:
            rows = load_monthly_demand_artifact(item_code)
        if rows:
            observed = (
                pd.DataFrame(rows)
                .groupby("period", as_index=False)
                .agg(net_quantity=("net_quantity", "sum"))
            )
            periods = pd.period_range(range_from, range_to, freq="M").astype(str)
            dataset = (
                observed.set_index("period")
                .reindex(periods, fill_value=0.0)
                .rename_axis("period")
                .reset_index()
            )
            dataset["item_code"] = item_code
    comparison_frame = result.comparison[
        result.comparison["item_code"] == item_code
    ]
    best = result.best_models[result.best_models["item_code"] == item_code]
    future = result.future[result.future["item_code"] == item_code]
    test_size = min(test_months, len(dataset))
    history = dataset.iloc[:-test_size]
    test = dataset.iloc[-test_size:]
    return {
        "item": dataframe_records(candidate)[0],
        "historical": dataframe_records(history),
        "test": dataframe_records(test),
        "model_comparison": dataframe_records(comparison_frame),
        "best_model": dataframe_records(best)[0] if not best.empty else None,
        "future_forecast": dataframe_records(future),
    }
