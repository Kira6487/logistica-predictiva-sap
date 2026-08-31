from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendation_service import get_purchase_candidates  # noqa: E402


def _row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_code": record.get("item_code"),
        "item_name": record.get("item_name"),
        "warehouse_code": record.get("warehouse_code"),
        "suggested_quantity": record.get("suggested_quantity"),
        "suggested_horizon_days": record.get("suggested_horizon_days"),
        "priority_level": record.get("priority_level"),
        "priority_score": record.get("priority_score"),
        "recommendation_confidence": record.get("recommendation_confidence"),
        "preferred_vendor_code": record.get("preferred_vendor_code"),
        "preferred_vendor_name": record.get("preferred_vendor_name"),
        "estimated_lead_time_days": record.get("estimated_lead_time_days"),
        "main_message": record.get("main_message"),
        "recommendation_warning": record.get("recommendation_warning"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta candidatos de compra referencial.")
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "purchase_candidates.csv"))
    args = parser.parse_args()

    rows = [_row(record) for record in get_purchase_candidates(limit=args.limit)]
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
