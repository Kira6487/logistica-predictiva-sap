from pydantic import BaseModel


class DataQualityFlag(BaseModel):
    code: str
    message: str


class MonthlyConsumptionRecord(BaseModel):
    item_code: str | None
    item_description: str | None
    warehouse: str | None
    year: int
    month: int
    period: str | None
    consumed_quantity: float
    movement_count: int
    first_date: str | None
    last_date: str | None
    quality_flags: list[str] = []


class ConsumptionTopItem(BaseModel):
    item_code: str
    item_description: str | None = None
    consumed_quantity: float
    movement_count: int


class ConsumptionTopWarehouse(BaseModel):
    warehouse: str
    consumed_quantity: float
    movement_count: int


class ConsumptionSummary(BaseModel):
    date_range: dict[str, str | None]
    total_items_with_consumption: int
    total_warehouses: int
    total_periods: int
    total_consumed_quantity: float
    total_movements_analyzed: int
    excluded_transfer_movements: int
    revisable_movements: int
    top_items_by_consumption: list[ConsumptionTopItem]
    top_warehouses_by_consumption: list[ConsumptionTopWarehouse]


class MovementTypeSummary(BaseModel):
    trans_type: int | None
    movement_count: int
    total_in_qty: float
    total_out_qty: float
    first_date: str | None
    last_date: str | None
    sample_base_ref: str | None = None
    category: str
    is_transfer: bool
    is_adjustment: bool
    is_revisable: bool
    interpretation: str


class ItemConsumptionDetail(BaseModel):
    item: dict[str, str | None]
    monthly_consumption: list[MonthlyConsumptionRecord]
    warehouses: list[str]
    summary: dict[str, float | int]
    recent_movements: list[dict]
    quality_warnings: list[str]