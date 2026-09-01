"""Safe preflight for Azure SQL demo (DNS/TCP, login, and read permissions)."""

from __future__ import annotations

from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseConnectionError, _error_category, test_connection  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not settings.db_password:
        print("[BLOQUEADO] Configure DB_PASSWORD localmente antes del preflight.")
        return 2

    print("=== Preflight Azure SQL demo (solo lectura) ===")
    try:
        addresses = socket.getaddrinfo(settings.db_server, settings.db_port or 1433)
        print(f"[OK] DNS: {len(addresses)} dirección(es) resuelta(s)")
        with socket.create_connection(
            (settings.db_server, settings.db_port or 1433),
            timeout=settings.db_connection_timeout,
        ):
            print(f"[OK] TCP: puerto {settings.db_port or 1433} accesible")
        result = test_connection()
        print(f"[OK] DB_NAME(): {result['database']}")
        print(f"[OK] SUSER_SNAME(): {result['login_name']}")
        print(f"[OK] SELECT: {'sí' if result['permissions']['select'] else 'no'}")
        print(
            "[OK] INSERT/UPDATE/DELETE: "
            f"{result['permissions']['insert']}/"
            f"{result['permissions']['update']}/"
            f"{result['permissions']['delete']}"
        )
        if not result["read_only"]:
            print("[BLOQUEADO] El usuario no cumple el perfil de solo lectura.")
            return 3
        print("Preflight finalizado sin modificaciones en la base.")
        return 0
    except (OSError, DatabaseConnectionError, ValueError, ImportError) as exc:
        print(
            f"[ERROR] Preflight no disponible: {_error_category(exc)} "
            f"({type(exc).__name__})"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
