"""Generate a schema-aware, read-only validation report for the demo dataset."""

from pathlib import Path
import json
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseConnectionError  # noqa: E402
from app.services.diagnostics_service import inspect_demo_database  # noqa: E402


EXPORT_DIR = Path(__file__).resolve().parents[1] / "exports"


def main() -> int:
    settings = get_settings()
    if not settings.db_password:
        print("[BLOQUEADO] Configure DB_PASSWORD localmente antes de validar.")
        return 2
    try:
        report = inspect_demo_database()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        (EXPORT_DIR / "phase1_validation_report.json").write_text(
            json.dumps(report, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        pd.DataFrame(report["monthly_summary"]).to_csv(
            EXPORT_DIR / "phase1_monthly_summary.csv", index=False
        )
        issues = [
            {"check": name, "issue_count": count}
            for name, count in report["validation"]["checks"].items()
            if isinstance(count, int) and count > 0 and ("negative" in name or "orphan" in name or "null" in name)
        ]
        pd.DataFrame(issues).to_csv(
            EXPORT_DIR / "phase1_data_issues.csv", index=False
        )
        print("Validación demo finalizada en modo solo lectura.")
        print(f"Rango: {report['date_range']['min_date']} a {report['date_range']['max_date']}")
        print(f"Meses distintos: {report['date_range']['distinct_months']}")
        print(f"Artículos con al menos 12 meses: {report['validation']['checks'].get('items_with_at_least_12_months', 0)}")
        return 0
    except (DatabaseConnectionError, ValueError) as exc:
        print(f"[ERROR] Validación no disponible: {type(exc).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
