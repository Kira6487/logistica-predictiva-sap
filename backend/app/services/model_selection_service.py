from __future__ import annotations

import pandas as pd


def select_best_model(comparison: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "item_code",
        "best_model",
        "best_wape",
        "best_mae",
        "best_rmse",
        "best_bias",
        "forecast_confidence",
        "selection_reason",
    ]
    if comparison.empty:
        return pd.DataFrame(columns=columns)

    selected: list[dict] = []
    valid = comparison[comparison["status"] == "ok"].copy()
    for item_code, group in comparison.groupby("item_code", sort=True):
        candidates = valid[valid["item_code"] == item_code].copy()
        if candidates.empty:
            selected.append(
                {
                    "item_code": item_code,
                    "best_model": None,
                    "best_wape": None,
                    "best_mae": None,
                    "best_rmse": None,
                    "best_bias": None,
                    "forecast_confidence": "NOT_RECOMMENDED",
                    "selection_reason": "Ningún modelo pudo evaluarse.",
                }
            )
            continue

        candidates["wape_sort"] = candidates["wape"].fillna(float("inf"))
        if candidates["wape"].notna().any():
            winner = candidates.sort_values(
                ["wape_sort", "mae", "model"],
                ascending=[True, True, True],
            ).iloc[0]
            reason = "Menor WAPE; MAE usado como desempate."
        else:
            winner = candidates.sort_values(
                ["mae", "rmse", "model"],
                ascending=[True, True, True],
            ).iloc[0]
            reason = "WAPE no calculable; selección por menor MAE."

        wape_value = winner["wape"]
        intermittent = bool(winner.get("is_intermittent", False))
        evaluated = int(winner["evaluated_months"])
        if pd.isna(wape_value):
            confidence = "LOW"
        elif wape_value <= 20 and evaluated >= 6 and not intermittent:
            confidence = "HIGH"
        elif wape_value <= 50:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        selected.append(
            {
                "item_code": item_code,
                "best_model": winner["model"],
                "best_wape": None if pd.isna(wape_value) else float(wape_value),
                "best_mae": float(winner["mae"]),
                "best_rmse": float(winner["rmse"]),
                "best_bias": float(winner["bias"]),
                "forecast_confidence": confidence,
                "selection_reason": reason,
            }
        )
    return pd.DataFrame(selected, columns=columns)
