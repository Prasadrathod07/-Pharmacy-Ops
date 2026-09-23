from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import OrderStatus, StockStatus
from app.domain.rules import stock_status_sql_case
from app.models import Drug, Inventory, Order


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_orders_created_between(self, start: datetime, end: datetime) -> int:
        return self.db.execute(
            select(func.count()).select_from(Order).where(Order.created_at >= start, Order.created_at < end)
        ).scalar_one()

    def count_orders_completed_between(self, start: datetime, end: datetime) -> int:
        return self.db.execute(
            select(func.count())
            .select_from(Order)
            .where(
                Order.status == OrderStatus.COMPLETED,
                Order.completed_at >= start,
                Order.completed_at < end,
            )
        ).scalar_one()

    def count_pending_orders(self) -> int:
        return self.db.execute(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.WAITING_FOR_STOCK)
        ).scalar_one()

    def dispensed_order_timestamps_between(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        """(created_at, dispensed_at) pairs for orders dispensed in the window.

        Averaging is done in Python rather than via a dialect-specific SQL
        function (e.g. MySQL's TIMESTAMPDIFF) to keep the query portable and
        the calculation easy to unit test in isolation.
        """
        rows = self.db.execute(
            select(Order.created_at, Order.dispensed_at).where(
                Order.dispensed_at.isnot(None),
                Order.dispensed_at >= start,
                Order.dispensed_at < end,
            )
        ).all()
        return [(row[0], row[1]) for row in rows]

    def count_low_stock_drugs(self) -> int:
        return self.db.execute(
            select(func.count())
            .select_from(Inventory)
            .where(
                Inventory.quantity_on_hand <= Inventory.low_stock_threshold,
                Inventory.quantity_on_hand > Inventory.reorder_threshold,
            )
        ).scalar_one()

    def count_critical_stock_drugs(self) -> int:
        # Deliberately includes OUT_OF_STOCK (quantity 0 <= reorder_threshold
        # is always true): master spec §14.6 defines CRITICAL as
        # quantity <= reorder_threshold with no exclusion for zero, and the
        # combined "Critical / Urgent Reorder" KPI card (§9.1) is meant to
        # capture every drug needing urgent attention. This differs from the
        # 4-way StockStatus badge used in the Inventory UI, where
        # OUT_OF_STOCK is its own distinct label.
        return self.db.execute(
            select(func.count())
            .select_from(Inventory)
            .where(Inventory.quantity_on_hand <= Inventory.reorder_threshold)
        ).scalar_one()

    def list_non_healthy_inventory(self) -> list[tuple[Inventory, Drug]]:
        status_expr = stock_status_sql_case()
        query = (
            select(Inventory, Drug)
            .join(Drug, Inventory.drug_id == Drug.id)
            .where(status_expr != StockStatus.HEALTHY.value)
            .order_by(Inventory.quantity_on_hand.asc())
        )
        rows = self.db.execute(query).all()
        return [(row[0], row[1]) for row in rows]
