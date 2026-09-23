from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import OrderItemStatus, OrderStatus


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: int
    drug_code: str
    drug_name: str
    requested_quantity: int
    dispensed_quantity: int
    status: OrderItemStatus
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    patient_id: int
    patient_name: str
    status: OrderStatus
    items_count: int
    created_at: datetime
    dispensed_at: datetime | None
    completed_at: datetime | None
    fulfilment_minutes: float | None


class OrderDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    patient_id: int
    patient_name: str
    status: OrderStatus
    items: list[OrderItemOut]
    created_at: datetime
    dispensed_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    updated_at: datetime
    fulfilment_minutes: float | None


class OrderItemCreate(BaseModel):
    drug_id: int
    quantity: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    patient_name: str = Field(min_length=1, max_length=150)
    # Optional: if omitted, the server stamps the current UTC time. Accepting
    # a client-supplied value allows backdating a phone order taken earlier,
    # but the server never trusts a client-supplied *stock* figure - only this
    # timestamp, which is not security/consistency sensitive.
    ordered_at: datetime | None = None
    items: list[OrderItemCreate] = Field(min_length=1)

    @field_validator("patient_name")
    @classmethod
    def _trim_patient_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("patient_name must not be blank")
        return trimmed

    @field_validator("items")
    @classmethod
    def _no_duplicate_drugs(cls, items: list[OrderItemCreate]) -> list[OrderItemCreate]:
        seen: set[int] = set()
        for item in items:
            if item.drug_id in seen:
                raise ValueError(f"Duplicate drug_id {item.drug_id} in order items.")
            seen.add(item.drug_id)
        return items
