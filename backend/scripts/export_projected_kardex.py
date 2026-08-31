from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.item_diagnosis_service import get_item_projected_kardex  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta Kardex proyectado por articulo.")
    parser.add_argument("item_code")
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "kardex_proyectado_articulo.csv"))
    args = parser.parse_args()

    rows = get_item_projected_kardex(item_code=args.item_code, warehouse=args.warehouse)
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
