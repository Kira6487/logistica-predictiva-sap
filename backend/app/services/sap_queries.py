from sqlalchemy import text


MAX_SALES_DATE_QUERY = text(
    """
    SELECT MAX(DocDate) AS max_doc_date
    FROM OINV
    WHERE CANCELED = 'N'
    """
)


MONTHLY_DEMAND_QUERY = text(
    """
    WITH document_lines AS (
        SELECT
            T0.DocDate,
            T1.ItemCode,
            T1.WhsCode,
            CAST(T1.Quantity AS decimal(19, 6)) AS quantity,
            CAST(T1.LineTotal AS decimal(19, 6)) AS line_total
        FROM OINV AS T0
        INNER JOIN INV1 AS T1 ON T1.DocEntry = T0.DocEntry
        WHERE T0.CANCELED = 'N'
          AND T0.DocDate >= :date_from
          AND T0.DocDate < DATEADD(day, 1, CAST(:date_to AS date))
          AND T1.ItemCode IS NOT NULL
          AND (:item_code IS NULL OR T1.ItemCode = :item_code)
          AND (:warehouse_code IS NULL OR T1.WhsCode = :warehouse_code)

        UNION ALL

        SELECT
            T0.DocDate,
            T1.ItemCode,
            T1.WhsCode,
            -CAST(T1.Quantity AS decimal(19, 6)) AS quantity,
            -CAST(T1.LineTotal AS decimal(19, 6)) AS line_total
        FROM ORIN AS T0
        INNER JOIN RIN1 AS T1 ON T1.DocEntry = T0.DocEntry
        WHERE T0.CANCELED = 'N'
          AND T0.DocDate >= :date_from
          AND T0.DocDate < DATEADD(day, 1, CAST(:date_to AS date))
          AND T1.ItemCode IS NOT NULL
          AND (:item_code IS NULL OR T1.ItemCode = :item_code)
          AND (:warehouse_code IS NULL OR T1.WhsCode = :warehouse_code)
    )
    SELECT
        YEAR(D.DocDate) AS year,
        MONTH(D.DocDate) AS month,
        CONVERT(char(7), D.DocDate, 120) AS period,
        D.ItemCode AS item_code,
        MAX(I.ItemName) AS item_name,
        D.WhsCode AS warehouse_code,
        SUM(D.quantity) AS net_quantity,
        SUM(D.line_total) AS net_sales_total,
        MAX(G.ItmsGrpNam) AS item_group
    FROM document_lines AS D
    LEFT JOIN OITM AS I ON I.ItemCode = D.ItemCode
    LEFT JOIN OITB AS G ON G.ItmsGrpCod = I.ItmsGrpCod
    GROUP BY
        YEAR(D.DocDate),
        MONTH(D.DocDate),
        CONVERT(char(7), D.DocDate, 120),
        D.ItemCode,
        D.WhsCode
    ORDER BY period, item_code, warehouse_code
    """
)


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
