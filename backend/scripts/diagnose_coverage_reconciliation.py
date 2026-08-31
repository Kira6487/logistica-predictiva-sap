from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.coverage_risk_service import get_coverage_reconciliation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostica conciliacion entre consumo historico, stock y partidas abiertas.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "coverage_reconciliation.json"))
    args = parser.parse_args()

    diagnostics = get_coverage_reconciliation(item_code=args.item_code, warehouse=args.warehouse, limit=args.limit)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
