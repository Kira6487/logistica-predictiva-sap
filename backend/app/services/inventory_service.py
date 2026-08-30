from __future__ import annotations

from typing import Any
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.core.database import DatabaseConnectionError, read_frame
from app.services.schema_service import get_available_schema
from app.services.sap_queries import (
    has_table,
    pick_column,
    quote_identifier,
    table_columns,
)


def build_inventory_query(schema):
    if not has_table(schema, "OITW"):
        raise ValueError("La tabla OITW no existe en la demo.")
    wcols = table_columns(schema, "OITW")
    item = pick_column(wcols, "ItemCode", "Item", "SKU")
    warehouse = pick_column(wcols, "WhsCode", "WarehouseCode", "Warehouse")
    physical = pick_column(wcols, "OnHand", "PhysicalStock", "Stock")
    committed = pick_column(wcols, "IsCommited", "IsCommitted", "Committed", "CommittedStock")
    on_order = pick_column(wcols, "OnOrder", "OnOrderStock", "Ordered")
    if not (item and warehouse and physical):
        raise ValueError("OITW no contiene las columnas mínimas de inventario.")
    committed_expr = f"W.{quote_identifier(committed)}" if committed else "0"
    order_expr = f"W.{quote_identifier(on_order)}" if on_order else "0"
    item_name, item_group, item_join = "NULL", "NULL", ""
    if has_table(schema, "OITM"):
        icols = table_columns(schema, "OITM")
        ikey = pick_column(icols, "ItemCode", "Item", "SKU")
        nkey = pick_column(icols, "ItemName", "Dscription", "Description")
        gkey = pick_column(icols, "ItmsGrpCod", "ItemGroupCode", "ItemGroup")
        if ikey:
            item_join = f"LEFT JOIN [OITM] I ON I.{quote_identifier(ikey)} = W.{quote_identifier(item)}"
            if nkey:
                item_name = f"I.{quote_identifier(nkey)}"
            if gkey and has_table(schema, "OITB"):
                gcols = table_columns(schema, "OITB")
                gcode = pick_column(gcols, "ItmsGrpCod", "ItemGroupCode", "GroupCode")
                gname = pick_column(gcols, "ItmsGrpNam", "GroupName", "ItemGroup")
                if gcode and gname:
                    item_join += f"LEFT JOIN [OITB] G ON G.{quote_identifier(gcode)} = I.{quote_identifier(gkey)}"
                    item_group = f"G.{quote_identifier(gname)}"
    warehouse_name, warehouse_join = "W." + quote_identifier(warehouse), ""
    if has_table(schema, "OWHS"):
        hcols = table_columns(schema, "OWHS")
        hkey = pick_column(hcols, "WhsCode", "WarehouseCode", "Warehouse")
        hname = pick_column(hcols, "WhsName", "WarehouseName", "Name")
        if hkey and hname:
            warehouse_join = f"LEFT JOIN [OWHS] H ON H.{quote_identifier(hkey)} = W.{quote_identifier(warehouse)}"
            warehouse_name = f"H.{quote_identifier(hname)}"
    return text(
        f"SELECT W.{quote_identifier(item)} AS item_code, {item_name} AS item_name, "
        f"{item_group} AS item_group, W.{quote_identifier(warehouse)} AS warehouse_code, "
        f"{warehouse_name} AS warehouse_name, CAST(W.{quote_identifier(physical)} AS decimal(19, 6)) AS physical_stock, "
        f"CAST({committed_expr} AS decimal(19, 6)) AS committed_stock, "
        f"CAST({order_expr} AS decimal(19, 6)) AS on_order_stock FROM [OITW] W "
        f"{item_join} {warehouse_join} WHERE (:item_code IS NULL OR W.{quote_identifier(item)} = :item_code) "
        f"AND (:warehouse_code IS NULL OR W.{quote_identifier(warehouse)} = :warehouse_code) "
        "AND (:item_group IS NULL OR " + item_group + " = :item_group) "
        f"ORDER BY W.{quote_identifier(item)}, W.{quote_identifier(warehouse)}"
    )


def calculate_stock_values(
    physical_stock: float,
    committed_stock: float,
    on_order_stock: float,
) -> tuple[float, float]:
    available = physical_stock - committed_stock
    projected = available + on_order_stock
    return available, projected


def get_current_inventory(
    item_code: str | None = None,
    warehouse_code: str | None = None,
    item_group: str | None = None,
    only_with_stock: bool = False,
    aggregate: bool = False,
) -> pd.DataFrame:
    try:
        frame = read_frame(
            build_inventory_query(get_available_schema()),
            {
                "item_code": item_code,
                "warehouse_code": warehouse_code,
                "item_group": item_group,
            },
        )
    except (DatabaseConnectionError, ValueError) as exc:
        raise DatabaseConnectionError(
            "No se pudo consultar el inventario actual desde OITW."
        ) from exc

    numeric = ["physical_stock", "committed_stock", "on_order_stock"]
    frame[numeric] = frame[numeric].fillna(0.0).astype(float)
    if aggregate:
        frame = (
            frame.groupby("item_code", as_index=False)
            .agg(
                item_name=("item_name", "first"),
                item_group=("item_group", "first"),
                warehouse_name=("warehouse_name", "first"),
                physical_stock=("physical_stock", "sum"),
                committed_stock=("committed_stock", "sum"),
                on_order_stock=("on_order_stock", "sum"),
            )
        )
        frame["warehouse_code"] = warehouse_code or "ALL"
        if warehouse_code is None:
            frame["warehouse_name"] = "Todos los almacenes"

    frame["available_stock"] = (
        frame["physical_stock"] - frame["committed_stock"]
    )
    frame["projected_stock"] = (
        frame["available_stock"] + frame["on_order_stock"]
    )
    if only_with_stock:
        frame = frame[
            (frame["physical_stock"] != 0)
            | (frame["committed_stock"] != 0)
            | (frame["on_order_stock"] != 0)
        ]
    return frame.reset_index(drop=True)


def inventory_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def load_inventory_artifact() -> pd.DataFrame | None:
    path = Path(__file__).resolve().parents[2] / "exports" / "current_inventory_snapshot.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"item_code": str, "warehouse_code": str})
