from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.stock_position_service import get_stock_items  # noqa: E402

EXPORT_PATH = BACKEND_DIR / "exports" / "stock_position.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exporta stock actual por articulo y almacen.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--only-with-stock", action="store_true")
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--limit", type=int, default=100000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = get_stock_items(
        item_code=args.item_code,
        warehouse=args.warehouse,
        only_with_stock=args.only_with_stock,
        include_inactive=args.include_inactive,
        limit=args.limit,
    )
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["item_code"]
    with EXPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Exportacion de stock actual - solo lectura")
    print(f"registros_exportados: {len(rows)}")
    print(f"archivo_exportado: {EXPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())