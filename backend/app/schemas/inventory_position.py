from typing import Any

from pydantic import BaseModel


class StockPositionRecord(BaseModel):
    item_code: str | None
    item_name: str | None
    warehouse_code: str | None
    warehouse_name: str | None
    stock_fisico: float
    stock_comprometido: float
    stock_pedido: float
    stock_disponible: float
    stock_proyectado_base: float
    sin_stock: bool
    stock_negativo: bool
    comprometido_mayor_stock: bool
    tiene_stock: bool
    tiene_pedido_abierto: bool
    tiene_compromiso_abierto: bool
    item_inventory: bool
    item_active: bool
    warehouse_locked: bool
    warehouse_inactive: bool


class StockSummary(BaseModel):
    total_items_with_stock: int
    total_warehouses: int
    stock_fisico_total: float
    stock_disponible_total: float
    items_without_stock: int
    negative_stock_items: int
    committed_over_stock_items: int
    items_with_open_orders: int


class StockItemDetail(BaseModel):
    item_code: str
    item_name: str | None
    stock_by_warehouse: list[StockPositionRecord]
    summary: dict[str, Any]


class WarehouseStockSummary(BaseModel):
    warehouse_code: str | None
    warehouse_name: str | None
    total_items: int
    stock_fisico_total: float
    stock_disponible_total: float
    stock_pedido_total: float
    negative_stock_items: int
    committed_over_stock_items: int


class OpenDocumentRecord(BaseModel):
    tipo_documento: str | None
    doc_entry: int | None
    doc_num: int | None
    line_num: int | None
    fecha_documento: str | None
    fecha_entrega: str | None
    card_code: str | None
    card_name: str | None
    item_code: str | None
    item_name: str | None
    warehouse_code: str | None
    warehouse_name: str | None
    cantidad_abierta: float
    moneda: str | None
    precio: float
    total_linea: float
    estado_documento: str | None
    estado_linea: str | None
    direction: str | None
    source_table: str | None


class OpenDocumentsSummary(BaseModel):
    open_purchase_orders: int
    open_sales_orders: int
    open_production_orders: int
    open_transfer_requests: int
    open_incoming_quantity: float
    open_outgoing_quantity: float
    affected_items: int
    total_documents: int


class OpenDocumentsItemDetail(BaseModel):
    item_code: str
    documents: list[OpenDocumentRecord]
    summary: OpenDocumentsSummary


class InventoryPositionRecord(StockPositionRecord):
    stock_comprometido_sap: float
    stock_pedido_sap: float
    entradas_abiertas: float
    salidas_abiertas: float
    stock_proyectado_con_partidas: float


class InventoryPositionItemDetail(BaseModel):
    item_code: str
    item_name: str | None
    position_by_warehouse: list[InventoryPositionRecord]
    open_documents: list[OpenDocumentRecord]
    summary: dict[str, Any]


class InventoryPositionSummary(BaseModel):
    stock: StockSummary
    open_documents: OpenDocumentsSummary
    stock_projected_with_open_documents_note: str