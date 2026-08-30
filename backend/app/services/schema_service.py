from __future__ import annotations

from functools import lru_cache

from sqlalchemy import text

from app.core.database import DatabaseConnectionError, read_rows


DEMO_TABLES = (
    "OITB", "OITM", "OWHS", "OITW", "OINM", "OCRD", "OSLP", "OINV",
    "INV1", "ORIN", "RIN1", "OPOR", "POR1", "OPDN", "PDN1",
)


@lru_cache(maxsize=1)
def get_available_schema() -> dict[str, set[str]]:
    """Return only columns exposed by the demo database.

    Queries are intentionally limited to INFORMATION_SCHEMA and never interpolate
    user input. The result is cached for the process lifetime because the schema
    does not change during a request batch.
    """
    query = text(
        "SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME IN (" + ",".join(f":table_{i}" for i in range(len(DEMO_TABLES))) + ")"
    )
    params = {f"table_{i}": table for i, table in enumerate(DEMO_TABLES)}
    try:
        rows = read_rows(query, params)
    except DatabaseConnectionError:
        raise
    schema: dict[str, set[str]] = {table: set() for table in DEMO_TABLES}
    for row in rows:
        schema.setdefault(str(row["TABLE_NAME"]).upper(), set()).add(
            str(row["COLUMN_NAME"])
        )
    return schema


def clear_schema_cache() -> None:
    get_available_schema.cache_clear()
