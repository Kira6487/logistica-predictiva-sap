from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.consumption_history_service import get_monthly_consumption  # noqa: E402


EXPORT_PATH = BACKEND_DIR / "exports" / "monthly_consumption.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exporta consumo historico mensual desde movimientos de inventario SAP.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--include-transfers", action="store_true")
    parser.add_argument("--include-adjustments", action="store_true")
    parser.add_argument("--limit", type=int, default=100000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = get_monthly_consumption(
        item_code=args.item_code,
        warehouse=args.warehouse,
        start_date=args.start_date,
        end_date=args.end_date,
        include_transfers=args.include_transfers,
        include_adjustments=args.include_adjustments,
        limit=args.limit,
    )
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "item_code",
        "item_description",
        "warehouse",
        "year",
        "month",
        "period",
        "consumed_quantity",
        "movement_count",
        "first_date",
        "last_date",
        "quality_flags",
    ]
    with EXPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["quality_flags"] = ";".join(csv_row.get("quality_flags", []))
            writer.writerow(csv_row)

    print("Exportacion de consumo historico mensual - solo lectura")
    print(f"registros_exportados: {len(rows)}")
    print(f"cantidad_total_consumida: {sum(row['consumed_quantity'] for row in rows)}")
    print(f"archivo_exportado: {EXPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())