from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import StockStatus


class DrugListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    strength: str | None
    dosage_form: str | None
    is_active: bool
    quantity_on_hand: int
    stock_status: StockStatus


class DrugDetail(DrugListItem):
    low_stock_threshold: int
    reorder_threshold: int
    last_restocked_at: datetime | None
