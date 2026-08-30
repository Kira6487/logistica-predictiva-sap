"""Print the read-only schema and data diagnostics for the demo provider."""

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseConnectionError, test_connection  # noqa: E402
from app.services.diagnostics_service import inspect_demo_database  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not settings.db_password:
        print("[BLOQUEADO] Configure DB_PASSWORD localmente antes del diagnóstico.")
        return 2
    try:
        connection = test_connection()
        report = inspect_demo_database()
        print("=== Diagnóstico Azure SQL demo (solo lectura) ===")
        print(json.dumps({"connection": connection, **report}, indent=2, default=str, ensure_ascii=False))
        return 0
    except (DatabaseConnectionError, ValueError) as exc:
        print(f"[ERROR] Diagnóstico no disponible: {type(exc).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
