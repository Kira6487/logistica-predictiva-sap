from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.open_documents_service import get_open_documents  # noqa: E402

EXPORT_PATH = BACKEND_DIR / "exports" / "open_documents.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exporta partidas abiertas SAP.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--limit", type=int, default=100000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = get_open_documents(
        item_code=args.item_code,
        warehouse=args.warehouse,
        document_type=args.document_type,
        limit=args.limit,
    )
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["tipo_documento"]
    with EXPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Exportacion de partidas abiertas SAP - solo lectura")
    print(f"registros_exportados: {len(rows)}")
    print(f"archivo_exportado: {EXPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())