from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domain.enums import InventoryMovementType, StockStatus
from app.domain.rules import stock_status_sql_case
from app.models import Drug, Inventory, InventoryTransaction

SORT_COLUMNS = {
    "name": Drug.name,
    "code": Drug.code,
    "quantity_on_hand": Inventory.quantity_on_hand,
    "last_restocked_at": Inventory.last_restocked_at,
}


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _filtered_query(
        self,
        *,
        search: str | None,
        status: StockStatus | None,
        low_stock_only: bool,
        critical_only: bool,
    ):
        query = select(Inventory, Drug).join(Drug, Inventory.drug_id == Drug.id)

        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(or_(Drug.name.ilike(like), Drug.code.ilike(like)))
        if status is not None:
            conditions.append(stock_status_sql_case() == status.value)
        if low_stock_only:
            conditions.append(Inventory.quantity_on_hand <= Inventory.low_stock_threshold)
        if critical_only:
            conditions.append(
                and_(Inventory.quantity_on_hand <= Inventory.reorder_threshold, Inventory.quantity_on_hand > 0)
            )

        if conditions:
            query = query.where(and_(*conditions))
        return query

    def list_inventory(
        self,
        *,
        search: str | None,
        status: StockStatus | None,
        low_stock_only: bool,
        critical_only: bool,
        sort_by: str,
        sort_order: str,
        offset: int,
        limit: int,
    ) -> tuple[list[tuple[Inventory, Drug]], int]:
        query = self._filtered_query(
            search=search, status=status, low_stock_only=low_stock_only, critical_only=critical_only
        )

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

        sort_column = stock_status_sql_case() if sort_by == "status" else SORT_COLUMNS.get(sort_by, Drug.name)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        query = query.offset(offset).limit(limit)

        rows = self.db.execute(query).all()
        return [(row[0], row[1]) for row in rows], total

    def get_by_drug_id(self, drug_id: int, *, for_update: bool = False) -> Inventory | None:
        query = select(Inventory).where(Inventory.drug_id == drug_id)
        if for_update:
            query = query.with_for_update()
        return self.db.execute(query).scalar_one_or_none()

    def list_transactions(
        self,
        *,
        drug_id: int,
        movement_type: InventoryMovementType | None,
        date_from: datetime | None,
        date_to: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[list[InventoryTransaction], int]:
        query = select(InventoryTransaction).where(InventoryTransaction.drug_id == drug_id)

        if movement_type is not None:
            query = query.where(InventoryTransaction.movement_type == movement_type)
        if date_from is not None:
            query = query.where(InventoryTransaction.created_at >= date_from)
        if date_to is not None:
            query = query.where(InventoryTransaction.created_at <= date_to)

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

        query = query.order_by(InventoryTransaction.created_at.desc()).offset(offset).limit(limit)
        rows = self.db.execute(query).scalars().all()
        return list(rows), total
