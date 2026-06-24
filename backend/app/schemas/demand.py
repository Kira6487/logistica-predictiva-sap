from pydantic import BaseModel


class MonthlyDemand(BaseModel):
    year: int
    month: int
    period: str
    item_code: str
    item_name: str | None = None
    warehouse_code: str | None = None
    net_quantity: float
    net_sales_total: float | None = None
    item_group: str | None = None
