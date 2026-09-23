from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.enums import InventoryMovementSource, InventoryMovementType


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("ix_inventory_transactions_drug_created_at", "drug_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("drugs.id"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("orders.id"), nullable=True, index=True
    )
    order_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("order_items.id"), nullable=True, index=True
    )
    movement_type: Mapped[InventoryMovementType] = mapped_column(
        Enum(InventoryMovementType, native_enum=False, length=20, validate_strings=True), nullable=False
    )
    source: Mapped[InventoryMovementSource] = mapped_column(
        Enum(InventoryMovementSource, native_enum=False, length=30, validate_strings=True), nullable=False
    )
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    drug: Mapped["Drug"] = relationship(back_populates="transactions")
    order: Mapped["Order"] = relationship(back_populates="transactions")
    order_item: Mapped["OrderItem"] = relationship(back_populates="transactions")
