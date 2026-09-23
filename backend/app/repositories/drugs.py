from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Drug, Inventory


class DrugRepository:
    """LEFT JOINs inventory so a drug without an inventory row (shouldn't
    normally happen, but isn't DB-enforced) still lists instead of vanishing.
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self, *, search: str | None, active: bool | None):
        query = select(Drug, Inventory).outerjoin(Inventory, Inventory.drug_id == Drug.id)

        if search:
            like = f"%{search}%"
            query = query.where(or_(Drug.name.ilike(like), Drug.code.ilike(like)))
        if active is not None:
            query = query.where(Drug.is_active == active)

        return query

    def list_drugs(
        self, *, search: str | None, active: bool | None, offset: int, limit: int
    ) -> tuple[list[tuple[Drug, Inventory | None]], int]:
        query = self._base_query(search=search, active=active)

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

        query = query.order_by(Drug.name.asc()).offset(offset).limit(limit)
        rows = self.db.execute(query).all()
        return [(row[0], row[1]) for row in rows], total

    def get_drug_with_inventory(self, drug_id: int) -> tuple[Drug, Inventory | None] | None:
        query = select(Drug, Inventory).outerjoin(Inventory, Inventory.drug_id == Drug.id).where(Drug.id == drug_id)
        row = self.db.execute(query).one_or_none()
        return (row[0], row[1]) if row else None
