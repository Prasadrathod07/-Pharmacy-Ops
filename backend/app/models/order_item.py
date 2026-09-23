from sqlalchemy import BigInteger, CheckConstraint, Enum, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.enums import OrderItemStatus
from app.models.mixins import TimestampMixin


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "drug_id", name="uq_order_items_order_drug"),
        CheckConstraint("requested_quantity > 0", name="ck_order_items_requested_quantity_positive"),
        CheckConstraint("dispensed_quantity >= 0", name="ck_order_items_dispensed_quantity_non_negative"),
        Index("ix_order_items_drug_status", "drug_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id"), nullable=False, index=True
    )
    drug_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("drugs.id"), nullable=False)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderItemStatus] = mapped_column(
        Enum(OrderItemStatus, native_enum=False, length=30, validate_strings=True), nullable=False
    )
    dispensed_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    order: Mapped["Order"] = relationship(back_populates="items")
    drug: Mapped["Drug"] = relationship(back_populates="order_items")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(back_populates="order_item")
