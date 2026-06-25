from __future__ import annotations

from typing import Any
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import DatabaseConnectionError, get_engine


INVENTORY_QUERY = text(
    """
    SELECT
        W.ItemCode AS item_code,
        I.ItemName AS item_name,
        G.ItmsGrpNam AS item_group,
        W.WhsCode AS warehouse_code,
        H.WhsName AS warehouse_name,
        CAST(W.OnHand AS decimal(19, 6)) AS physical_stock,
        CAST(W.IsCommited AS decimal(19, 6)) AS committed_stock,
        CAST(W.OnOrder AS decimal(19, 6)) AS on_order_stock
    FROM OITW W
    INNER JOIN OITM I ON I.ItemCode = W.ItemCode
    LEFT JOIN OITB G ON G.ItmsGrpCod = I.ItmsGrpCod
    LEFT JOIN OWHS H ON H.WhsCode = W.WhsCode
    WHERE (:item_code IS NULL OR W.ItemCode = :item_code)
      AND (:warehouse_code IS NULL OR W.WhsCode = :warehouse_code)
      AND (:item_group IS NULL OR G.ItmsGrpNam = :item_group)
    ORDER BY W.ItemCode, W.WhsCode
    """
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
        with get_engine().connect() as connection:
            frame = pd.read_sql_query(
                INVENTORY_QUERY,
                connection,
                params={
                    "item_code": item_code,
                    "warehouse_code": warehouse_code,
                    "item_group": item_group,
                },
            )
    except SQLAlchemyError as exc:
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
