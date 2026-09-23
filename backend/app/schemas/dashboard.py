from pydantic import BaseModel


class DashboardSummary(BaseModel):
    orders_today: int
    completed_today: int
    pending_orders: int
    average_fulfilment_minutes: float | None
    low_stock_drugs: int
    critical_stock_drugs: int
