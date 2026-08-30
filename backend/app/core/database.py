from contextlib import contextmanager
from functools import lru_cache
import time
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError

from app.core.config import get_settings


class DatabaseConnectionError(RuntimeError):
    """Error de conexión presentado sin exponer datos sensibles."""


TRANSIENT_ERROR_CODES = {"40613", "08S01", "HYT00", "HYT01", "08001", "08003"}


def _is_transient(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(code.lower() in message for code in TRANSIENT_ERROR_CODES) or any(
        phrase in message
        for phrase in ("timeout", "temporarily unavailable", "connection reset", "closed")
    )


def _retry(operation, attempts: int = 4):
    delay = 1.0
    for attempt in range(attempts):
        try:
            return operation()
        except (OperationalError, DBAPIError) as exc:
            if attempt == attempts - 1 or not _is_transient(exc):
                raise
            time.sleep(delay)
            delay = min(delay * 2, 8.0)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    try:
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=5,
            pool_timeout=settings.db_connection_timeout,
            connect_args={"timeout": settings.db_connection_timeout},
        )
    except (SQLAlchemyError, ValueError, ImportError) as exc:
        raise DatabaseConnectionError(
            "No se pudo configurar la conexión a SQL Server. Revise .env.local, "
            "pyodbc y el ODBC Driver instalado."
        ) from exc


@contextmanager
def connection():
    """Open a pooled connection, retrying transient Azure SQL wake-up errors."""
    engine = get_engine()
    active = _retry(engine.connect)
    try:
        yield active
    finally:
        active.close()


def read_rows(query, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    def operation():
        with connection() as active:
            return [dict(row) for row in active.execute(query, params or {}).mappings()]

    try:
        return _retry(operation)
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        raise DatabaseConnectionError(
            "Azure SQL no está disponible temporalmente o la consulta no pudo ejecutarse."
        ) from exc


def read_frame(query, params: dict[str, Any] | None = None) -> pd.DataFrame:
    def operation():
        with connection() as active:
            return pd.read_sql_query(query, active, params=params or {})

    try:
        return _retry(operation)
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        raise DatabaseConnectionError(
            "Azure SQL no está disponible temporalmente o la consulta no pudo ejecutarse."
        ) from exc


def test_connection() -> dict[str, Any]:
    query = text(
        """
        SELECT
            DB_NAME() AS database_name,
            SUSER_SNAME() AS login_name,
            SYSDATETIME() AS server_datetime,
            HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'SELECT') AS can_select,
            HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'INSERT') AS can_insert,
            HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'UPDATE') AS can_update,
            HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'DELETE') AS can_delete
        """
    )
    try:
        row = read_rows(query)[0]
        return {
            "status": "ok",
            "database": row["database_name"],
            "login_name": row["login_name"],
            "server_datetime": row["server_datetime"],
            "read_only": bool(row["can_select"] and not row["can_insert"] and not row["can_update"] and not row["can_delete"]),
            "permissions": {
                "select": bool(row["can_select"]),
                "insert": bool(row["can_insert"]),
                "update": bool(row["can_update"]),
                "delete": bool(row["can_delete"]),
            },
        }
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        raise DatabaseConnectionError(
            "No fue posible conectar con SQL Server. Verifique que el servicio "
            "esté activo, que la base exista y que las credenciales sean válidas."
        ) from exc
