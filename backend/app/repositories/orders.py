from datetime import datetime

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import OrderStatus
from app.models import Drug, Order, OrderItem, Patient

SORT_COLUMNS = {
    "created_at": Order.created_at,
    "order_number": Order.order_number,
    "status": Order.status,
    "dispensed_at": Order.dispensed_at,
    "completed_at": Order.completed_at,
}


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_orders(
        self,
        *,
        search: str | None,
        status: OrderStatus | None,
        drug_id: int | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_by: str,
        sort_order: str,
        offset: int,
        limit: int,
    ) -> tuple[list[tuple[Order, str, int]], int]:
        items_count_subq = (
            select(func.count(OrderItem.id)).where(OrderItem.order_id == Order.id).correlate(Order).scalar_subquery()
        )

        query = (
            select(Order, Patient.full_name, items_count_subq.label("items_count"))
            .join(Patient, Order.patient_id == Patient.id)
        )

        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(or_(Order.order_number.ilike(like), Patient.full_name.ilike(like)))
        if status is not None:
            conditions.append(Order.status == status)
        if drug_id is not None:
            conditions.append(
                exists().where(and_(OrderItem.order_id == Order.id, OrderItem.drug_id == drug_id))
            )
        if date_from is not None:
            conditions.append(Order.created_at >= date_from)
        if date_to is not None:
            conditions.append(Order.created_at <= date_to)

        if conditions:
            query = query.where(and_(*conditions))

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

        sort_column = SORT_COLUMNS.get(sort_by, Order.created_at)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        query = query.offset(offset).limit(limit)

        rows = self.db.execute(query).all()
        return [(row[0], row[1], row[2]) for row in rows], total

    def get_order_with_details(self, order_id: int) -> tuple[Order, str] | None:
        query = (
            select(Order, Patient.full_name)
            .join(Patient, Order.patient_id == Patient.id)
            .options(joinedload(Order.items).joinedload(OrderItem.drug))
            .where(Order.id == order_id)
        )
        row = self.db.execute(query).unique().one_or_none()
        return (row[0], row[1]) if row else None
