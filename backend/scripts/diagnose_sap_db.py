from pathlib import Path
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseConnectionError, get_engine  # noqa: E402
from app.services.sap_queries import (  # noqa: E402
    CRITICAL_COLUMNS,
    OPTIONAL_SAP_TABLES,
    SAP_TABLES,
)


def main() -> int:
    settings = get_settings()
    print("=== Diagnóstico SAP Business One ===")
    print(f"Base configurada: {settings.db_name}")
    print("Modo: solo lectura\n")

    try:
        with get_engine().connect() as connection:
            server = connection.execute(
                text(
                    """
                    SELECT
                        DB_NAME() AS database_name,
                        SYSDATETIME() AS server_datetime,
                        CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128))
                            AS product_version,
                        CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) AS edition
                    """
                )
            ).mappings().one()
            print(f"[OK] Base conectada: {server['database_name']}")
            print(f"Fecha/hora SQL: {server['server_datetime']}")
            print(
                "SQL Server: "
                f"{server['product_version']} / {server['edition']}"
            )

            table_status: dict[str, bool] = {}
            print("\nTablas principales y opcionales:")
            for table_name in SAP_TABLES + OPTIONAL_SAP_TABLES:
                object_type = connection.execute(
                    text(
                        """
                        SELECT type_desc
                        FROM sys.objects
                        WHERE object_id = OBJECT_ID(:table_name)
                        """
                    ),
                    {"table_name": table_name},
                ).scalar_one_or_none()
                exists = object_type is not None
                table_status[table_name] = exists
                if not exists:
                    print(f"[FALTA] {table_name}")
                    continue
                count = connection.execute(
                    text(f"SELECT COUNT_BIG(*) FROM [{table_name}]")
                ).scalar_one()
                print(
                    f"[OK] {table_name}: {count:,} registros "
                    f"({object_type})"
                )

            print("\nColumnas críticas:")
            print(f"{'Tabla':<8} {'Columna':<16} {'Estado':<10} Observación")
            for table_name, columns in CRITICAL_COLUMNS.items():
                for column_name in columns:
                    exists = bool(
                        connection.execute(
                            text(
                                """
                                SELECT CASE WHEN COL_LENGTH(:table_name, :column_name)
                                    IS NULL THEN 0 ELSE 1 END
                                """
                            ),
                            {
                                "table_name": table_name,
                                "column_name": column_name,
                            },
                        ).scalar_one()
                    )
                    state = "EXISTE" if exists else "NO EXISTE"
                    observation = "Compatible" if exists else "Requiere ajuste"
                    print(
                        f"{table_name:<8} {column_name:<16} "
                        f"{state:<10} {observation}"
                    )

            print("\nRangos documentales activos:")
            ranges = {}
            for table_name, label in (("OINV", "Facturas"), ("ORIN", "Notas crédito")):
                if not table_status.get(table_name):
                    continue
                ranges[table_name] = connection.execute(
                    text(
                        f"""
                        SELECT MIN(DocDate) AS min_date, MAX(DocDate) AS max_date
                        FROM [{table_name}]
                        WHERE CANCELED = 'N'
                        """
                    )
                ).mappings().one()
                row = ranges[table_name]
                print(f"{label}: {row['min_date']} a {row['max_date']}")

            available_dates = [
                value
                for row in ranges.values()
                for value in (row["min_date"], row["max_date"])
                if value is not None
            ]
            if available_dates:
                print(
                    f"Rango total: {min(available_dates)} a "
                    f"{max(available_dates)}"
                )

        print("\nDiagnóstico finalizado.")
        return 0
    except (SQLAlchemyError, DatabaseConnectionError, ValueError) as exc:
        print(f"\n[ERROR] {exc}")
        print(
            "Revise servidor/instancia, servicio SQL Server, TCP/puerto, "
            "credenciales, driver ODBC y permisos."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
