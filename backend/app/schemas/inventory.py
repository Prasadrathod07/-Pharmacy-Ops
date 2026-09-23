from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import InventoryMovementSource, InventoryMovementType, StockStatus


class InventoryListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug_id: int
    drug_code: str
    drug_name: str
    strength: str | None
    dosage_form: str | None
    quantity_on_hand: int
    low_stock_threshold: int
    reorder_threshold: int
    status: StockStatus
    last_restocked_at: datetime | None


class InventoryTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: int
    order_id: int | None
    order_item_id: int | None
    movement_type: InventoryMovementType
    source: InventoryMovementSource
    quantity_delta: int
    quantity_before: int
    quantity_after: int
    note: str | None
    created_at: datetime


class InventoryDetail(InventoryListItem):
    recent_transactions: list[InventoryTransactionOut]


class RestockRequest(BaseModel):
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)
