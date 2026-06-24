import argparse
from datetime import date, datetime
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import DatabaseConnectionError  # noqa: E402
from app.services.demand_service import get_monthly_demand  # noqa: E402


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use formato YYYY-MM-DD.") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exporta demanda mensual neta de SAP a CSV."
    )
    parser.add_argument("--date-from", type=parse_date)
    parser.add_argument("--date-to", type=parse_date)
    parser.add_argument("--item-code")
    parser.add_argument("--warehouse-code")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.date_from and args.date_to and args.date_from > args.date_to:
        print("[ERROR] --date-from no puede ser posterior a --date-to.")
        return 2

    try:
        rows = get_monthly_demand(
            date_from=args.date_from,
            date_to=args.date_to,
            item_code=args.item_code,
            warehouse_code=args.warehouse_code,
        )
    except (DatabaseConnectionError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = export_dir / f"monthly_demand_{timestamp}.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Registros exportados: {len(rows):,}")
    print(f"Archivo: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
