from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseConnectionError, get_engine
from app.services.sap_queries import MAX_SALES_DATE_QUERY, MONTHLY_DEMAND_QUERY
from app.utils.dates import default_24_month_range


def resolve_date_range(
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    if date_from is not None and date_to is not None:
        return date_from, date_to

    try:
        with get_engine().connect() as connection:
            max_doc_date = connection.execute(MAX_SALES_DATE_QUERY).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "No se pudo consultar la fecha máxima de facturas en SAP."
        ) from exc

    if max_doc_date is None:
        raise DatabaseConnectionError(
            "OINV no contiene facturas de venta activas para calcular el rango."
        )

    default_from, default_to = default_24_month_range(max_doc_date)
    return date_from or default_from, date_to or default_to


def get_monthly_demand(
    date_from: date | None = None,
    date_to: date | None = None,
    item_code: str | None = None,
    warehouse_code: str | None = None,
    item_group: str | None = None,
) -> list[dict[str, Any]]:
    resolved_from, resolved_to = resolve_date_range(date_from, date_to)
    if resolved_from > resolved_to:
        raise ValueError("date_from no puede ser posterior a date_to.")

    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                MONTHLY_DEMAND_QUERY,
                {
                    "date_from": resolved_from,
                    "date_to": resolved_to,
                    "item_code": item_code,
                    "warehouse_code": warehouse_code,
                    "item_group": item_group,
                },
            )
            rows = [dict(row) for row in result.mappings()]
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "No se pudo extraer la demanda mensual. Verifique la estructura "
            "OINV/INV1/ORIN/RIN1/OITM/OITB y los permisos de lectura."
        ) from exc

    for row in rows:
        for field in ("net_quantity", "net_sales_total"):
            if isinstance(row.get(field), Decimal):
                row[field] = float(row[field])
    return rows
