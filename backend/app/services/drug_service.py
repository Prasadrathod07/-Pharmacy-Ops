from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.domain.rules import compute_stock_status
from app.models import Drug, Inventory
from app.repositories.drugs import DrugRepository
from app.schemas.common import PaginatedResponse
from app.schemas.drug import DrugDetail, DrugListItem


def _to_list_item(drug: Drug, inventory: Inventory | None) -> DrugListItem:
    quantity = inventory.quantity_on_hand if inventory else 0
    low = inventory.low_stock_threshold if inventory else 0
    reorder = inventory.reorder_threshold if inventory else 0
    return DrugListItem(
        id=drug.id,
        code=drug.code,
        name=drug.name,
        strength=drug.strength,
        dosage_form=drug.dosage_form,
        is_active=drug.is_active,
        quantity_on_hand=quantity,
        stock_status=compute_stock_status(quantity, low, reorder),
    )


class DrugService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DrugRepository(db)

    def list_drugs(
        self, *, search: str | None, active: bool | None, page_params
    ) -> PaginatedResponse[DrugListItem]:
        rows, total = self.repo.list_drugs(
            search=search, active=active, offset=page_params.offset, limit=page_params.page_size
        )
        items = [_to_list_item(drug, inventory) for drug, inventory in rows]
        return PaginatedResponse.build(items, page_params.page, page_params.page_size, total)

    def get_drug(self, drug_id: int) -> DrugDetail:
        result = self.repo.get_drug_with_inventory(drug_id)
        if result is None:
            raise AppError("DRUG_NOT_FOUND", f"Drug {drug_id} not found.", status_code=404)

        drug, inventory = result
        base = _to_list_item(drug, inventory)
        return DrugDetail(
            **base.model_dump(),
            low_stock_threshold=inventory.low_stock_threshold if inventory else 0,
            reorder_threshold=inventory.reorder_threshold if inventory else 0,
            last_restocked_at=inventory.last_restocked_at if inventory else None,
        )
