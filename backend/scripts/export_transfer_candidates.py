from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendation_service import get_transfer_candidates  # noqa: E402


def _row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_code": record.get("item_code"),
        "item_name": record.get("item_name"),
        "source_warehouse": record.get("source_warehouse"),
        "target_warehouse": record.get("target_warehouse"),
        "transfer_candidate_quantity": record.get("transfer_candidate_quantity"),
        "source_stock_before": record.get("source_projected_stock_before_transfer"),
        "target_stock_before": record.get("target_projected_stock_before_transfer"),
        "source_remaining_stock_after_transfer": record.get("source_remaining_stock_after_transfer"),
        "target_projected_stock_after_transfer": record.get("target_projected_stock_after_transfer"),
        "priority_level": record.get("priority_level"),
        "transfer_reason": record.get("transfer_reason"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta candidatos de traslado referencial.")
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "transfer_candidates.csv"))
    args = parser.parse_args()

    rows = [_row(record) for record in get_transfer_candidates(limit=args.limit)]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["item_code"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print({"registros_exportados": len(rows), "archivo": str(output_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
