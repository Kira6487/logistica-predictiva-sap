from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.item_diagnosis_service import get_item_availability_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta auditoria de disponibilidad por articulo.")
    parser.add_argument("item_code")
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "auditoria_disponibilidad_articulo.csv"))
    args = parser.parse_args()

    audit = get_item_availability_audit(item_code=args.item_code, warehouse=args.warehouse)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flat = {key: value for key, value in audit.items() if key != "formula_lines"}
    flat["formula"] = " | ".join(f"{line['operator']} {line['label']}: {line['value']}" for line in audit["formula_lines"])
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(flat.keys()))
        writer.writeheader()
        writer.writerow(flat)
    print({"registros_exportados": 1, "archivo": str(output_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
