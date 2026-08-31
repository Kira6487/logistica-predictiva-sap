from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.inventory_movements_service import diagnose_inventory_sources  # noqa: E402


def _print_source(source: dict[str, Any]) -> None:
    print(f"\n== {source['source']} ==")
    print(f"tipo: {source['type']}")
    print(f"descripcion: {source['description']}")
    print(f"registros: {source['record_count']}")
    print(f"rango_fechas: {source['date_range']}")
    print("columnas_clave_encontradas: " + ", ".join(source["key_columns_found"]))
    missing = source["missing_expected_columns"]
    print("columnas_esperadas_faltantes: " + (", ".join(missing) if missing else "ninguna"))
    print("columnas_disponibles:")
    for column in source["columns"]:
        print(f"- {column}")


def main() -> int:
    print("Diagnostico de fuentes de inventario SAP - solo lectura")
    diagnostics = diagnose_inventory_sources()
    for source in diagnostics:
        _print_source(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())