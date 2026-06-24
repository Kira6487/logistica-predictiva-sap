from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings


class DatabaseConnectionError(RuntimeError):
    """Error de conexión presentado sin exponer datos sensibles."""


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    try:
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"timeout": 10},
        )
    except (SQLAlchemyError, ValueError, ModuleNotFoundError) as exc:
        raise DatabaseConnectionError(
            "No se pudo configurar la conexión a SQL Server. Revise .env.local, "
            "pyodbc y el ODBC Driver instalado."
        ) from exc


def test_connection() -> dict[str, Any]:
    query = text(
        """
        SELECT
            DB_NAME() AS database_name,
            SYSDATETIME() AS server_datetime
        """
    )
    try:
        with get_engine().connect() as connection:
            row = connection.execute(query).mappings().one()
        return {
            "status": "ok",
            "database": row["database_name"],
            "server_datetime": row["server_datetime"],
        }
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        raise DatabaseConnectionError(
            "No fue posible conectar con SQL Server. Verifique que el servicio "
            "esté activo, que la base exista y que las credenciales sean válidas."
        ) from exc
