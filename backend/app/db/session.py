"""Compatibility layer for operational queries using the current Azure SQL setup."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text

from app.core.database import DatabaseConnectionError, read_rows


class ReadOnlyQueryError(ValueError):
    """Raised when a query is not a single read-only SQL statement."""


FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|merge|drop|truncate|alter|create|exec|execute|grant|revoke)\b",
    re.IGNORECASE,
)


def _strip_sql_comments(sql: str) -> str:
    without_line_comments = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return re.sub(r"/\*.*?\*/", "", without_line_comments, flags=re.DOTALL).strip()


def ensure_read_only_query(sql: str) -> None:
    normalized = _strip_sql_comments(sql).lower()
    if not normalized.startswith(("select", "with")):
        raise ReadOnlyQueryError("Solo se permiten consultas SELECT en SAP.")
    if ";" in normalized.rstrip(";"):
        raise ReadOnlyQueryError("No se permiten múltiples sentencias SQL.")
    if FORBIDDEN_SQL_PATTERN.search(normalized):
        raise ReadOnlyQueryError("La consulta contiene una operación no permitida.")


def execute_read_query(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a guarded SELECT through the existing pooled Azure SQL connection."""
    ensure_read_only_query(sql)
    try:
        return read_rows(text(sql), params)
    except DatabaseConnectionError:
        raise
