from sqlalchemy import create_engine

from app.services.sap_queries import build_monthly_demand_query


def test_demo_query_uses_only_available_optional_columns() -> None:
    schema = {
        "OINV": {"DocEntry", "DocDate", "CANCELED"},
        "INV1": {"DocEntry", "ItemCode", "Quantity", "WhsCode"},
        "OITM": {"ItemCode", "ItemName"},
    }
    query = str(
        build_monthly_demand_query(schema).compile(
            dialect=create_engine("sqlite://").dialect
        )
    )

    assert "LineTotal" not in query
    assert "OITB" not in query
    assert "ItemName" in query
