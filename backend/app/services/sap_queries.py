from collections.abc import Mapping

from sqlalchemy import text


SAP_TABLES = (
    "OINV",
    "INV1",
    "ORIN",
    "RIN1",
    "OITM",
    "OITW",
    "OWHS",
    "OCRD",
    "OSLP",
)

OPTIONAL_SAP_TABLES = (
    "OITB",
    "OBTN",
    "OBTQ",
    "IBT1",
    "OPOR",
    "POR1",
    "OPDN",
    "PDN1",
    "OINM",
)

CRITICAL_COLUMNS = {
    "OINV": (
        "DocEntry",
        "DocDate",
        "CANCELED",
        "DocTotal",
        "DocCur",
        "CardCode",
        "SlpCode",
    ),
    "INV1": (
        "DocEntry",
        "ItemCode",
        "Dscription",
        "Quantity",
        "LineTotal",
        "WhsCode",
    ),
    "ORIN": (
        "DocEntry",
        "DocDate",
        "CANCELED",
        "DocTotal",
        "DocCur",
        "CardCode",
        "SlpCode",
    ),
    "RIN1": (
        "DocEntry",
        "ItemCode",
        "Dscription",
        "Quantity",
        "LineTotal",
        "WhsCode",
    ),
    "OITM": ("ItemCode", "ItemName", "ItmsGrpCod"),
    "OITW": ("ItemCode", "WhsCode", "OnHand", "IsCommited", "OnOrder"),
}


def quote_identifier(identifier: str) -> str:
    """Quote an identifier returned by INFORMATION_SCHEMA, never user input."""
    return f"[{identifier.replace(']', ']]')}]"


def table_columns(schema: Mapping[str, set[str]], table: str) -> set[str]:
    return {column.lower() for column in schema.get(table.upper(), set())}


def has_table(schema: Mapping[str, set[str]], table: str) -> bool:
    return bool(table_columns(schema, table))


def pick_column(columns: set[str], *names: str) -> str | None:
    for name in names:
        if name.lower() in columns:
            return name
    return None


def build_max_sales_date_query(schema: Mapping[str, set[str]]):
    if not has_table(schema, "OINV"):
        raise ValueError("La tabla OINV no existe en la demo.")
    cols = table_columns(schema, "OINV")
    date_column = pick_column(cols, "DocDate", "TaxDate", "CreateDate")
    if not date_column:
        raise ValueError("OINV no contiene una columna de fecha compatible.")
    active = "AND CANCELED = 'N'" if "canceled" in cols else ""
    return text(
        f"SELECT MAX({quote_identifier(date_column)}) AS max_doc_date "
        f"FROM {quote_identifier('OINV')} WHERE 1 = 1 {active}"
    )


def build_document_date_range_query(schema: Mapping[str, set[str]]):
    parts = []
    for table in ("OINV", "ORIN"):
        if not has_table(schema, table):
            continue
        cols = table_columns(schema, table)
        date_column = pick_column(cols, "DocDate", "TaxDate", "CreateDate")
        if not date_column:
            continue
        active = "AND CANCELED = 'N'" if "canceled" in cols else ""
        parts.append(
            f"SELECT {quote_identifier(date_column)} AS doc_date FROM "
            f"{quote_identifier(table)} WHERE 1 = 1 {active}"
        )
    if not parts:
        raise ValueError("No existen documentos con fecha compatible en la demo.")
    return text(
        "SELECT MIN(doc_date) AS min_date, MAX(doc_date) AS max_date FROM ("
        + " UNION ALL ".join(parts)
        + ") AS document_dates"
    )


def build_monthly_demand_query(schema: Mapping[str, set[str]]):
    """Build demand SQL from the columns actually exposed by the demo schema."""
    if not (has_table(schema, "OINV") and has_table(schema, "INV1")):
        raise ValueError("La demo requiere OINV e INV1 para calcular ventas.")

    document_parts = []
    for header, lines, sign in (("OINV", "INV1", 1), ("ORIN", "RIN1", -1)):
        if not (has_table(schema, header) and has_table(schema, lines)):
            continue
        hcols, lcols = table_columns(schema, header), table_columns(schema, lines)
        if "docentry" not in hcols or "docentry" not in lcols:
            continue
        date_column = pick_column(hcols, "DocDate", "TaxDate", "CreateDate")
        item_column = pick_column(lcols, "ItemCode", "Item", "SKU")
        quantity_column = pick_column(lcols, "Quantity", "Qty", "QuantityBase")
        if not (date_column and item_column and quantity_column):
            continue
        whs_column = pick_column(lcols, "WhsCode", "WarehouseCode", "Warehouse")
        amount_column = pick_column(lcols, "LineTotal", "LineTotalSy", "GrossTotal", "Amount")
        cancelled = "AND H.[CANCELED] = 'N'" if "canceled" in hcols else ""
        warehouse = f"L.{quote_identifier(whs_column)}" if whs_column else "'ALL'"
        amount = (
            f"CAST(L.{quote_identifier(amount_column)} AS decimal(19, 6))"
            if amount_column
            else "CAST(0 AS decimal(19, 6))"
        )
        document_parts.append(
            f"SELECT H.{quote_identifier(date_column)} AS doc_date, "
            f"L.{quote_identifier(item_column)} AS item_code, {warehouse} AS warehouse_code, "
            f"{sign} * CAST(L.{quote_identifier(quantity_column)} AS decimal(19, 6)) AS quantity, "
            f"{sign} * {amount} AS line_total FROM {quote_identifier(header)} H "
            f"INNER JOIN {quote_identifier(lines)} L ON L.[DocEntry] = H.[DocEntry] "
            f"WHERE H.{quote_identifier(date_column)} >= :date_from "
            f"AND H.{quote_identifier(date_column)} < DATEADD(day, 1, CAST(:date_to AS date)) "
            f"AND L.{quote_identifier(item_column)} IS NOT NULL {cancelled}"
        )
    if not document_parts:
        raise ValueError("No hay un par de tablas de ventas compatible en la demo.")

    joins = ""
    item_name = "NULL"
    item_group = "NULL"
    group_filter = ""
    if has_table(schema, "OITM"):
        icols = table_columns(schema, "OITM")
        item_key = pick_column(icols, "ItemCode", "Item", "SKU")
        name_key = pick_column(icols, "ItemName", "Dscription", "Description")
        group_key = pick_column(icols, "ItmsGrpCod", "ItemGroupCode", "ItemGroup")
        if item_key:
            joins += f" LEFT JOIN [OITM] I ON I.{quote_identifier(item_key)} = D.item_code"
            if name_key:
                item_name = f"MAX(I.{quote_identifier(name_key)})"
            if group_key and has_table(schema, "OITB"):
                gcols = table_columns(schema, "OITB")
                gkey = pick_column(gcols, "ItmsGrpCod", "ItemGroupCode", "GroupCode")
                gname = pick_column(gcols, "ItmsGrpNam", "GroupName", "ItemGroup")
                if gkey and gname:
                    joins += f" LEFT JOIN [OITB] G ON G.{quote_identifier(gkey)} = I.{quote_identifier(group_key)}"
                    item_group = f"MAX(G.{quote_identifier(gname)})"
                    group_filter = "AND (:item_group IS NULL OR EXISTS (SELECT 1 FROM [OITM] I0 INNER JOIN [OITB] G0 ON G0." + quote_identifier(gkey) + " = I0." + quote_identifier(group_key) + " WHERE I0." + quote_identifier(item_key) + " = D.item_code AND G0." + quote_identifier(gname) + " = :item_group))"
    return text(
        "WITH document_lines AS (" + " UNION ALL ".join(document_parts) + ") "
        "SELECT YEAR(D.doc_date) AS year, MONTH(D.doc_date) AS month, "
        "CONVERT(char(7), D.doc_date, 120) AS period, D.item_code, "
        f"{item_name} AS item_name, D.warehouse_code, SUM(D.quantity) AS net_quantity, "
        f"SUM(D.line_total) AS net_sales_total, {item_group} AS item_group FROM document_lines D"
        + joins
        + " WHERE (:item_code IS NULL OR D.item_code = :item_code) "
        "AND (:warehouse_code IS NULL OR D.warehouse_code = :warehouse_code) "
        + group_filter
        + " GROUP BY YEAR(D.doc_date), MONTH(D.doc_date), CONVERT(char(7), D.doc_date, 120), D.item_code, D.warehouse_code "
        "ORDER BY period, item_code, warehouse_code"
    )
