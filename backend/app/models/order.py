from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.enums import OrderStatus
from app.models.mixins import TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_status_created_at", "status", "created_at"),
        Index("ix_orders_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("patients.id"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=30, validate_strings=True), nullable=False
    )
    dispensed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(back_populates="order")
