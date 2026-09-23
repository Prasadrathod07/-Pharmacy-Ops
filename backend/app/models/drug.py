from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Drug(TimestampMixin, Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    inventory: Mapped["Inventory"] = relationship(back_populates="drug", uselist=False)
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="drug")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(back_populates="drug")
