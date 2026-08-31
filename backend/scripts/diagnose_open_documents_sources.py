from __future__ import annotations

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.open_documents_service import diagnose_open_document_sources  # noqa: E402


def main() -> int:
    print("Diagnostico de fuentes de partidas abiertas SAP - solo lectura")
    for source in diagnose_open_document_sources():
        print(f"\n== {source['source']} ==")
        print(f"existe: {source['exists']}")
        print(f"tipo: {source['type']}")
        print(f"registros: {source['record_count']}")
        print("columnas_clave_encontradas: " + ", ".join(source["key_columns_found"]))
        missing = source["missing_expected_columns"]
        print("columnas_esperadas_faltantes: " + (", ".join(missing) if missing else "ninguna"))
        print("columnas_disponibles:")
        for column in source["columns"]:
            print(f"- {column}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())