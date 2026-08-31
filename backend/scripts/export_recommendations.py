from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendation_service import get_recommendation_items  # noqa: E402


def _flatten(record: dict[str, Any]) -> dict[str, Any]:
    return {key: "; ".join(value) if isinstance(value, list) else value for key, value in record.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta recomendaciones accionables de logistica.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--recommendation-type", default=None)
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "recommendations.csv"))
    args = parser.parse_args()

    rows = get_recommendation_items(
        item_code=args.item_code,
        warehouse=args.warehouse,
        recommendation_type=args.recommendation_type,
        limit=args.limit,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(_flatten(rows[0]).keys()) if rows else ["item_code"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_flatten(row) for row in rows)
    print({"registros_exportados": len(rows), "archivo": str(output_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
