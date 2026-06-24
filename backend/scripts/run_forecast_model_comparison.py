import argparse
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.forecast_service import build_forecast  # noqa: E402


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Compara modelos de forecast.")
    value.add_argument("--date-from", type=parse_date)
    value.add_argument("--date-to", type=parse_date)
    value.add_argument("--item-group")
    value.add_argument("--warehouse-code")
    value.add_argument("--test-months", type=int, default=6)
    value.add_argument("--horizon", type=int, choices=(3, 6), default=3)
    return value


def main() -> int:
    args = parser().parse_args()
    result = build_forecast(
        args.date_from,
        args.date_to,
        args.item_group,
        args.warehouse_code,
        args.test_months,
        args.horizon,
    )
    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    result.comparison.to_csv(
        export_dir / "forecast_model_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result.best_models.to_csv(
        export_dir / "forecast_best_model_by_item.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"Comparaciones: {len(result.comparison):,}")
    print(f"Mejores modelos: {len(result.best_models):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
