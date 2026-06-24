import argparse
from datetime import date
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.eda_service import build_analytics  # noqa: E402


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use formato YYYY-MM-DD.") from exc


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Ejecuta métricas EDA y calidad por artículo."
    )
    value.add_argument("--date-from", type=parse_date)
    value.add_argument("--date-to", type=parse_date)
    value.add_argument("--item-code")
    value.add_argument("--item-group")
    value.add_argument("--warehouse-code")
    value.add_argument("--min-months", type=int, default=12)
    return value


def main() -> int:
    args = parser().parse_args()
    result = build_analytics(
        date_from=args.date_from,
        date_to=args.date_to,
        item_code=args.item_code,
        item_group=args.item_group,
        warehouse_code=args.warehouse_code,
        min_months=args.min_months,
    )
    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = export_dir / "eda_item_metrics.csv"
    quality_path = export_dir / "data_quality_report.csv"
    summary_path = export_dir / "analytics_summary.csv"

    result.metrics.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    quality_columns = [
        "item_code",
        "item_name",
        "item_group",
        "months_with_sales",
        "months_without_sales",
        "is_negative_demand",
        "has_amount_anomaly",
        "is_intermittent",
        "has_zero_or_null_values",
        "data_quality_status",
    ]
    result.metrics[quality_columns].to_csv(
        quality_path,
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame([result.summary]).to_csv(
        summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Artículos analizados: {len(result.metrics):,}")
    print(f"Métricas: {metrics_path}")
    print(f"Calidad: {quality_path}")
    print(f"Resumen: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
