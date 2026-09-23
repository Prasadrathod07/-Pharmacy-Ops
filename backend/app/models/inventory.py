from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Inventory(TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_quantity_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="ck_inventory_low_stock_threshold_non_negative"),
        CheckConstraint("reorder_threshold >= 0", name="ck_inventory_reorder_threshold_non_negative"),
        CheckConstraint(
            "reorder_threshold <= low_stock_threshold", name="ck_inventory_reorder_le_low_stock"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("drugs.id"), nullable=False, unique=True
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_restocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    drug: Mapped["Drug"] = relationship(back_populates="inventory")
