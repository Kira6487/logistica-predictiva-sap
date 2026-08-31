from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendation_service import diagnose_purchase_enrichment_sources  # noqa: E402


def main() -> int:
    diagnostics = diagnose_purchase_enrichment_sources()
    output_path = BACKEND_DIR / "exports" / "purchase_enrichment_sources.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
