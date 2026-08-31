from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.coverage_risk_service import get_coverage_risk_items  # noqa: E402


def _flatten(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: "; ".join(value) if isinstance(value, list) else value
        for key, value in record.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta diagnostico de cobertura y riesgo de quiebre.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--risk-level", default=None)
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "coverage_risk.csv"))
    args = parser.parse_args()

    records = get_coverage_risk_items(
        item_code=args.item_code,
        warehouse=args.warehouse,
        risk_level=args.risk_level,
        limit=args.limit,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        output_path.write_text("", encoding="utf-8")
        print({"registros_exportados": 0, "archivo": str(output_path)})
        return

    flattened = [_flatten(record) for record in records]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(flattened[0].keys()))
        writer.writeheader()
        writer.writerows(flattened)
    print({"registros_exportados": len(records), "archivo": str(output_path)})


if __name__ == "__main__":
    main()
