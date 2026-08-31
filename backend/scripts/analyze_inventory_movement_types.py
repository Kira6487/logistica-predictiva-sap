from __future__ import annotations

import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.inventory_movements_service import get_inventory_movement_types  # noqa: E402


EXPORT_PATH = BACKEND_DIR / "exports" / "inventory_movement_types.csv"


def main() -> int:
    rows = get_inventory_movement_types()
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "trans_type",
        "movement_count",
        "total_in_qty",
        "total_out_qty",
        "first_date",
        "last_date",
        "sample_base_ref",
        "category",
        "is_transfer",
        "is_adjustment",
        "is_revisable",
        "interpretation",
    ]
    with EXPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Analisis de tipos de movimiento SAP - solo lectura")
    print(f"tipos_detectados: {len(rows)}")
    print(f"archivo_exportado: {EXPORT_PATH}")
    for row in rows[:15]:
        print(
            f"TransType={row['trans_type']} registros={row['movement_count']} "
            f"out={row['total_out_qty']} categoria={row['category']} interpretacion={row['interpretation']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())